from __future__ import annotations

from datetime import timedelta
import math
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json
from ingestion.cleaning import build_text_for_embedding


def _json_value(value: Any) -> Any:
    """Convert pandas/numpy scalars and missing values to JSON-safe values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Return a deterministic corrupted copy and write a detailed event log.

    The corruption set is designed for the Step 7 exercise only. It does not
    repair records or evaluate the resulting data.
    """
    corrupted = df.copy(deep=True)
    input_rows = len(corrupted)
    events: list[dict[str, Any]] = []

    def event(corruption_type: str, paper_id: Any, **details: Any) -> None:
        events.append({
            "corruption_type": corruption_type,
            "paper_id": str(paper_id),
            **details,
        })

    if not corrupted.empty:
        if "paper_id" not in corrupted or "published" not in corrupted:
            raise ValueError("Clean dataframe must contain paper_id and published columns.")

        # Drop the newest fifth by publication date, independent of input order.
        drop_count = max(1, math.ceil(input_rows * 0.20))
        newest = corrupted.assign(
            __published_sort=pd.to_datetime(corrupted["published"], errors="coerce")
        ).sort_values(
            ["__published_sort", "paper_id"], ascending=[False, True], kind="stable"
        )
        drop_indices = newest.index[:drop_count]
        dropped = corrupted.loc[drop_indices]
        for index, row in dropped.iterrows():
            event(
                "drop_latest_records",
                row["paper_id"],
                action="row_removed",
                row_index=str(index),
                field="row",
                before={"published": _json_value(row["published"])},
                after=None,
            )
        corrupted = corrupted.drop(index=drop_indices).copy()

        # Use distinct surviving records for the remaining corruption modes.
        targets = list(corrupted.index)
        if targets:
            blank_idx = targets[0]
            before = corrupted.at[blank_idx, "summary"] if "summary" in corrupted else ""
            corrupted.at[blank_idx, "summary"] = ""
            event("blank_summary", corrupted.at[blank_idx, "paper_id"], field="summary",
                  row_index=str(blank_idx), before=_json_value(before), after="")

        if len(targets) > 1 and "summary" in corrupted:
            noise_idx = targets[1]
            before = corrupted.at[noise_idx, "summary"]
            noise = " qzxv_noise_7f3a blorp_91k2 "
            corrupted.at[noise_idx, "summary"] = f"{str(before).rstrip()}{noise}"
            event("inject_noise", corrupted.at[noise_idx, "paper_id"], field="summary",
                  row_index=str(noise_idx), before=_json_value(before),
                  after=corrupted.at[noise_idx, "summary"], noise=noise.strip())

        if len(targets) > 2 and "title" in corrupted:
            title_idx = targets[2]
            before = str(corrupted.at[title_idx, "title"])
            after = before[:6]
            corrupted.at[title_idx, "title"] = after
            event("truncate_title", corrupted.at[title_idx, "paper_id"], field="title",
                  row_index=str(title_idx), before=before, after=after)

        if len(targets) > 3:
            stale_idx = targets[3]
            before = pd.to_datetime(corrupted.at[stale_idx, "published"], errors="coerce")
            if pd.isna(before):
                raise ValueError(f"Invalid published date for {corrupted.at[stale_idx, 'paper_id']}.")
            after = before - timedelta(days=365)
            corrupted.at[stale_idx, "published"] = after.strftime("%Y-%m-%d")
            if "age_days" in corrupted:
                old_age = corrupted.at[stale_idx, "age_days"]
                corrupted.at[stale_idx, "age_days"] = int(old_age) + 365
            event("stale_date", corrupted.at[stale_idx, "paper_id"], field="published",
                  row_index=str(stale_idx), before=before.strftime("%Y-%m-%d"),
                  after=after.strftime("%Y-%m-%d"), age_days=_json_value(corrupted.at[stale_idx, "age_days"])
                  if "age_days" in corrupted else None)

        # Keep summary_chars coherent after blanking/noise.
        if "summary_chars" in corrupted and "summary" in corrupted:
            corrupted["summary_chars"] = corrupted["summary"].fillna("").astype(str).str.len()

        # Rebuild all embedding text from the mutated source fields using Step 3's
        # canonical formatter so all text corruptions affect downstream retrieval.
        if "text_for_embedding" in corrupted:
            corrupted["text_for_embedding"] = corrupted.apply(build_text_for_embedding, axis=1)

        # Duplicate a surviving row after mutations so duplicate identity is real
        # and the audit log can point to its source.
        if len(targets) > 4:
            duplicate_idx = targets[4]
            duplicate = corrupted.loc[[duplicate_idx]].copy()
            source_id = corrupted.at[duplicate_idx, "paper_id"]
            corrupted = pd.concat([corrupted, duplicate], ignore_index=True)
            event("duplicate_rows", source_id, action="row_duplicated",
                  source_row_index=str(duplicate_idx), duplicate_row_index=str(len(corrupted) - 1),
                  field="paper_id", before=str(source_id), after=str(source_id))

    log = {
        "summary": {
            "input_rows": input_rows,
            "output_rows": len(corrupted),
            "events": len(events),
            "corruption_types": sorted({item["corruption_type"] for item in events}),
        },
        "events": events,
    }
    write_json(Path(output_log_path), log)
    return corrupted.reset_index(drop=True)
