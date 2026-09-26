from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import re

import pandas as pd

from ingestion.crossref import PaperRecord


_CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "comment",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "age_days",
    "text_for_embedding",
]


def _save_clean_artifacts(df: pd.DataFrame) -> None:
    """Persist the clean dataset beside the raw artifacts for the next pipeline step."""
    clean_dir = Path(__file__).resolve().parents[2] / "data" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(clean_dir / "papers_clean.csv", index=False)
    df.to_json(clean_dir / "papers_clean.json", orient="records", force_ascii=False, indent=2)


def _normalize_text(value: object) -> str:
    """Collapse whitespace and remove any remaining lightweight markup."""
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return " ".join(text.split())


def _normalize_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [cleaned for value in values if (cleaned := _normalize_text(value))]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Return and save a deduplicated, embedding-ready Crossref dataframe."""
    if not records:
        empty_df = pd.DataFrame(columns=_CLEAN_COLUMNS)
        _save_clean_artifacts(empty_df)
        return empty_df

    df = pd.DataFrame([asdict(record) for record in records])
    for column in ("paper_id", "title", "summary", "primary_category", "abs_url", "pdf_url", "comment"):
        df[column] = df[column].map(_normalize_text)
    # DOI comparison is case-insensitive; use a canonical lowercase identifier.
    df["paper_id"] = df["paper_id"].str.lower()
    df["authors"] = df["authors"].map(_normalize_list)
    df["categories"] = df["categories"].map(_normalize_list)
    df["primary_category"] = df.apply(
        lambda row: row["primary_category"] or (row["categories"][0] if row["categories"] else ""), axis=1
    )

    df["published"] = pd.to_datetime(df["published"], errors="coerce").dt.normalize()
    df["updated"] = pd.to_datetime(df["updated"], errors="coerce").dt.normalize()
    # A row without identity, text, or publication date cannot be embedded or used
    # for freshness monitoring, so remove it before deduplication.
    df = df.dropna(subset=["published"])
    df = df[(df["paper_id"] != "") & (df["title"] != "") & (df["summary"] != "")]
    df = df.drop_duplicates(subset="paper_id", keep="first").copy()

    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is not None:
        run_timestamp = run_timestamp.tz_convert("UTC").tz_localize(None)
    run_timestamp = run_timestamp.normalize()
    df["age_days"] = (run_timestamp - df["published"]).dt.days.astype("int64")
    df["published"] = df["published"].dt.strftime("%Y-%m-%d")
    df["updated"] = df["updated"].dt.strftime("%Y-%m-%d").fillna("")
    df["authors_joined"] = df["authors"].map(lambda values: ", ".join(values) or "Unknown")
    df["categories_joined"] = df["categories"].map(lambda values: ", ".join(values) or "Uncategorized")
    df["summary_chars"] = df["summary"].str.len().astype("int64")
    df["text_for_embedding"] = df.apply(
        lambda row: (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Published: {row['published']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        ),
        axis=1,
    )
    clean_df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)[
        _CLEAN_COLUMNS
    ]
    _save_clean_artifacts(clean_df)
    return clean_df
