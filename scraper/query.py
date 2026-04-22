"""Question answering against the Gemini File Search store."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Iterator

from google.genai import types as genai_types

from file_search import get_active_store_name, make_gemini_client
from models import Citation
from settings import GEMINI_MODEL, SYSTEM_PROMPT


def extract_response_text(
    response: genai_types.GenerateContentResponse,
    *,
    require_text: bool = True,
) -> str:
    text = response.text
    if text:
        return text

    if not response.candidates:
        if require_text:
            raise RuntimeError("Gemini returned no candidates.")
        return ""

    parts: list[str] = []
    for candidate in response.candidates:
        content = candidate.content
        if content is None or not content.parts:
            continue
        for part in content.parts:
            part_text = part.text
            if part_text:
                parts.append(part_text)

    resolved_text = "\n".join(parts).strip()
    if resolved_text or not require_text:
        return resolved_text
    raise RuntimeError("Gemini returned no text content.")


def custom_metadata_to_dict(items: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items or []:
        key = item.key
        if not key:
            continue
        string_value = item.string_value
        numeric_value = item.numeric_value
        string_list_value = item.string_list_value
        if string_value is not None:
            result[key] = str(string_value)
        elif numeric_value is not None:
            result[key] = str(numeric_value)
        elif string_list_value:
            result[key] = ", ".join(str(value) for value in string_list_value)
    return result


def extract_citations(response: genai_types.GenerateContentResponse, limit: int = 3) -> list[Citation]:
    citations: list[Citation] = []
    seen_keys: set[str] = set()

    candidates = response.candidates or []
    if not candidates:
        return citations

    grounding_metadata = candidates[0].grounding_metadata
    if grounding_metadata is None:
        return citations

    for chunk in grounding_metadata.grounding_chunks or []:
        context = chunk.retrieved_context
        if context is None:
            continue

        metadata = custom_metadata_to_dict(context.custom_metadata)
        url = context.uri or metadata.get("article_url", "")
        title = context.title or metadata.get("slug", "Support article")
        document_name = context.document_name or ""
        dedupe_key = url or document_name or title
        if dedupe_key in seen_keys:
            continue

        citations.append(Citation(title=title, url=url, document_name=document_name))
        seen_keys.add(dedupe_key)
        if len(citations) >= limit:
            break

    return citations


def normalize_messages(messages: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role", "")).strip().lower()
        content = str(message.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def build_chat_prompt(messages: list[dict[str, str]]) -> str:
    if not messages:
        raise ValueError("At least one non-empty chat message is required.")

    conversation_lines = [
        f'{"User" if message["role"] == "user" else "Assistant"}: {message["content"]}'
        for message in messages[-12:]
    ]
    latest_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), None)
    if not latest_user_message:
        raise ValueError("At least one user message is required.")

    return (
        "Use the OptiSigns support docs to answer the latest user message.\n"
        "Keep the conversation context in mind, but do not invent facts outside the docs.\n\n"
        "Conversation history:\n"
        f"{chr(10).join(conversation_lines)}\n\n"
        "Latest user message:\n"
        f"{latest_user_message}"
    )


def build_generate_request(messages: Iterable[dict[str, Any]]) -> tuple[list[dict[str, str]], str, str, genai_types.GenerateContentConfig]:
    normalized_messages = normalize_messages(messages)
    prompt = build_chat_prompt(normalized_messages)
    store_name = get_active_store_name()
    config = genai_types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[
            genai_types.Tool(
                file_search=genai_types.FileSearch(file_search_store_names=[store_name])
            )
        ],
    )
    return normalized_messages, prompt, store_name, config


def ask_messages(messages: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized_messages, prompt, store_name, config = build_generate_request(messages)

    client = make_gemini_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )

    return {
        "messages": normalized_messages,
        "answer": extract_response_text(response),
        "citations": [asdict(citation) for citation in extract_citations(response)],
        "store_name": store_name,
        "model": GEMINI_MODEL,
    }


def stream_messages(messages: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    normalized_messages, prompt, store_name, config = build_generate_request(messages)

    client = make_gemini_client()
    stream = client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )

    accumulated_text = ""
    final_chunk: genai_types.GenerateContentResponse | None = None

    for chunk in stream:
        final_chunk = chunk
        text_delta = extract_response_text(chunk, require_text=False)
        if text_delta:
            accumulated_text += text_delta
            yield {"type": "token", "text": text_delta}

    citations = [asdict(citation) for citation in extract_citations(final_chunk)] if final_chunk else []
    yield {
        "type": "done",
        "messages": normalized_messages,
        "answer": accumulated_text,
        "citations": citations,
        "store_name": store_name,
        "model": GEMINI_MODEL,
    }


def ask_question(question: str) -> dict[str, Any]:
    result = ask_messages([{"role": "user", "content": question}])
    result["question"] = question
    return result
