"""Scraping and Markdown normalization."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from models import ArticleDoc
from settings import HELP_CENTER_HOST, LOCALE, OUT_DIR
from utils import approx_token_count, log, slugify, stable_hash


def request_json(url: str) -> dict[str, Any]:
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    return res.json()


def fetch_articles() -> list[dict[str, Any]]:
    """Fetch all public Zendesk Help Center articles sorted by newest update."""
    articles: list[dict[str, Any]] = []
    url = (
        f"{HELP_CENTER_HOST.rstrip('/')}/api/v2/help_center/{LOCALE}/articles.json"
        "?per_page=100&sort_by=updated_at&sort_order=desc"
    )

    while url:
        log("fetch_page", url=url)
        payload = request_json(url)
        for article in payload.get("articles", []):
            if article.get("draft"):
                continue
            articles.append(article)
        url = payload.get("next_page")

    log("fetch_complete", count=len(articles))
    return articles


def normalize_links(soup: BeautifulSoup, base_url: str) -> None:
    for tag in soup.find_all(["a", "img"]):
        attr = "href" if tag.name == "a" else "src"
        value = tag.get(attr)
        if not value or value.startswith(("#", "mailto:", "tel:")):
            continue
        tag[attr] = urljoin(base_url, value)


def remove_inline_data_images(soup: BeautifulSoup) -> int:
    removed = 0
    for tag in soup.find_all("img"):
        src = tag.get("src")
        if isinstance(src, str) and src.startswith("data:"):
            tag.decompose()
            removed += 1
    return removed


def html_to_markdown(article: dict[str, Any]) -> str:
    title = (article.get("title") or "Untitled").strip()
    url = article.get("html_url") or article.get("url") or HELP_CENTER_HOST
    source_updated_at = article.get("updated_at") or article.get("edited_at") or ""
    body_html = article.get("body") or ""

    soup = BeautifulSoup(body_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    removed_inline_images = remove_inline_data_images(soup)
    if removed_inline_images:
        log(
            "removed_inline_data_images",
            article_id=str(article.get("id")),
            title=title,
            count=removed_inline_images,
        )
    normalize_links(soup, url)

    body_md = md(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=["script", "style", "noscript"],
    ).strip()
    body_md = re.sub(r"\n{3,}", "\n\n", body_md)

    return f"""---
article_id: {article.get('id')}
title: {title}
source_updated_at: {source_updated_at}
---

Article URL: {url}

# {title}

{body_md}
""".strip() + "\n"


def write_markdown(articles: list[dict[str, Any]]) -> list[ArticleDoc]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    docs: list[ArticleDoc] = []

    for article in articles:
        article_id = str(article.get("id"))
        title = (article.get("title") or article_id).strip()
        slug = slugify(title, article_id)
        path = OUT_DIR / f"{slug}.md"
        content = html_to_markdown(article)
        content_hash = stable_hash(content)
        path.write_text(content, encoding="utf-8")
        token_count = approx_token_count(content)

        docs.append(
            ArticleDoc(
                article_id=article_id,
                title=title,
                url=article.get("html_url") or article.get("url") or "",
                source_updated_at=article.get("updated_at") or article.get("edited_at") or "",
                slug=slug,
                path=str(path),
                content_hash=content_hash,
                bytes=len(content.encode("utf-8")),
                approx_tokens=token_count,
            )
        )

    log(
        "markdown_complete",
        files=len(docs),
        out_dir=str(OUT_DIR),
    )
    return docs
