from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, normalize_whitespace, write_json


_QUESTION_TYPES = ("summary", "authors", "date", "categories")


def _list_text(value: object, fallback: str) -> str:
    """Return a displayable value from either a joined string or JSON list."""
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value if str(item).strip())
    else:
        text = str(value or "")
    return normalize_whitespace(text) or fallback


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build and persist a 10-question benchmark across four paper fields."""
    required_columns = {"paper_id", "title", "summary", "published"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Clean dataframe is missing required columns: {sorted(missing_columns)}")

    candidates = df.dropna(subset=["paper_id", "title", "summary", "published"]).copy()
    candidates["paper_id"] = candidates["paper_id"].astype(str).str.strip()
    candidates["title"] = candidates["title"].map(normalize_whitespace)
    candidates["summary"] = candidates["summary"].map(normalize_whitespace)
    candidates = candidates[
        (candidates["paper_id"] != "")
        & (candidates["title"] != "")
        & (candidates["summary"] != "")
    ].drop_duplicates(subset="paper_id")
    if len(candidates) < 10:
        raise ValueError("At least 10 valid, unique papers are required to build the benchmark test set.")

    test_set: list[dict[str, Any]] = []
    for index, (_, row) in enumerate(candidates.head(10).iterrows(), start=1):
        question_type = _QUESTION_TYPES[(index - 1) % len(_QUESTION_TYPES)]
        title = row["title"]
        if question_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(row["summary"])
        elif question_type == "authors":
            question = f"Who are the authors of the paper '{title}'?"
            ground_truth = _list_text(row.get("authors_joined", row.get("authors")), "Unknown")
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = pd.Timestamp(row["published"]).date().isoformat()
        else:
            question = f"What are the categories of the paper '{title}'?"
            ground_truth = _list_text(
                row.get("categories_joined", row.get("categories")), "Uncategorized"
            )

        test_set.append(
            {
                "id": f"eval_{index:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [row["paper_id"]],
            }
        )

    write_json(output_path, test_set)
    return test_set
