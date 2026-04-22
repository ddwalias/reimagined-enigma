"""Dataclasses shared across the OptiBot modules."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArticleDoc:
    article_id: str
    title: str
    url: str
    source_updated_at: str
    slug: str
    path: str
    content_hash: str
    bytes: int
    approx_tokens: int


@dataclass
class Citation:
    title: str
    url: str
    document_name: str
