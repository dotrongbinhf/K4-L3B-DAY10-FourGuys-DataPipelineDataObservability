from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from html import unescape
import json
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _as_text(value: object) -> str:
    """Convert a Crossref scalar or list field to normalized plain text."""
    if isinstance(value, list):
        value = " ".join(str(part) for part in value if part is not None)
    return " ".join(unescape(str(value or "")).split())


def _strip_markup(value: object) -> str:
    """Remove JATS/HTML tags from Crossref abstracts without losing text."""
    text = unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def _date_from_crossref(value: object) -> str:
    """Return an ISO date from a Crossref date object, or an empty string."""
    if not isinstance(value, dict):
        return ""
    date_parts = value.get("date-parts")
    if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list):
        parts = date_parts[0]
        if parts and isinstance(parts[0], int):
            year = parts[0]
            month = parts[1] if len(parts) > 1 and isinstance(parts[1], int) else 1
            day = parts[2] if len(parts) > 2 and isinstance(parts[2], int) else 1
            try:
                date(year, month, day)
                return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                return ""
    date_time = value.get("date-time")
    if isinstance(date_time, str):
        return date_time[:10]
    return ""


def _first_date(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        date = _date_from_crossref(item.get(key))
        if date:
            return date
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref work-list response into normalized ``PaperRecord`` objects.

    Records without a DOI or title are skipped because they cannot be identified or
    retrieved reliably downstream. Missing optional Crossref fields become empty
    strings/lists rather than causing the whole ingestion run to fail.
    """
    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    items = message.get("items", []) if isinstance(message, dict) else []
    if not isinstance(items, list):
        return []

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = _as_text(item.get("DOI"))
        title = _as_text(item.get("title"))
        if not paper_id or not title:
            continue

        authors: list[str] = []
        raw_authors = item.get("author", [])
        if isinstance(raw_authors, list):
            for author in raw_authors:
                if not isinstance(author, dict):
                    continue
                name = _as_text([author.get("given", ""), author.get("family", "")])
                authors.append(name or _as_text(author.get("name")))
        authors = [author for author in authors if author]

        raw_categories = item.get("subject", [])
        categories = (
            [_as_text(category) for category in raw_categories if _as_text(category)]
            if isinstance(raw_categories, list)
            else []
        )
        url = _as_text(item.get("URL")) or f"https://doi.org/{paper_id}"
        published = _first_date(
            item, "published", "published-online", "published-print", "issued", "created"
        )
        updated = _first_date(item, "updated", "indexed", "created") or published

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_strip_markup(item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {paper_id}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref metadata, preserving raw response and parsed records.

    A failed network request (including rate limiting) falls back to the existing
    raw API snapshot. The fallback deliberately does not overwrite that snapshot.
    """
    raw_path = settings.paths.raw_api_response
    records_path = settings.paths.raw_records_json
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.parent.mkdir(parents=True, exist_ok=True)
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    try:
        response: requests.Response | None = None
        for attempt in range(3):
            response = requests.get(
                "https://api.crossref.org/works",
                params=params,
                headers={"User-Agent": "data-observability-lab/1.0 (mailto:student@example.com)"},
                timeout=20,
            )
            if response.status_code not in {429, 500, 502, 503, 504}:
                break
            if attempt < 2:
                time.sleep(0.5 * (2**attempt))
        if response is None:
            raise requests.RequestException("Crossref request did not produce a response.")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Crossref returned a non-object JSON payload.")
        # This is the untouched API JSON structure; indentation only changes its
        # on-disk presentation, not any values used for lineage/replay.
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        if not raw_path.exists():
            raise RuntimeError(
                "Unable to fetch Crossref and no local raw snapshot is available at "
                f"{raw_path}."
            ) from None
        try:
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Local Crossref snapshot is invalid JSON: {raw_path}") from error

    records = parse_crossref_payload(payload)
    records_path.write_text(
        json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load the parsed-record artifact produced by :func:`fetch_source_records`."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Raw records snapshot must be a JSON list: {path}")
    fields = set(PaperRecord.__dataclass_fields__)
    return [PaperRecord(**{key: item[key] for key in fields}) for item in payload if isinstance(item, dict)]
