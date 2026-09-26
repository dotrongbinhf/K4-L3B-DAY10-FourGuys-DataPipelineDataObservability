from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


def _quality_report_path(settings: Settings, stage: str) -> Path:
    """Map known pipeline stages to their stable report locations."""
    known_paths = {
        "baseline": settings.paths.baseline_quality_report,
        "corrupted": settings.paths.corrupted_quality_report,
    }
    return known_paths.get(stage, settings.paths.quality_dir / f"{safe_slug(stage)}_quality_report.json")


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, stage: str) -> dict[str, Any]:
    """Run the mandatory GX 1.x checks and persist a JSON gate report.

    The ephemeral context keeps validation state in memory; only the concise report
    is persisted for lineage and later inspection.
    """
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gx.expectations.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        *[
            gx.expectations.ExpectColumnValuesToNotBeNull(column=column)
            for column in ("paper_id", "title", "text_for_embedding")
        ],
        gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"),
        gx.expectations.ExpectColumnValueLengthsToBeBetween(
            column="summary", min_value=30
        ),
    ]
    validation_results = [batch.validate(expectation) for expectation in expectations]
    freshness = evaluate_freshness_sla(df, settings, settings.paths.freshness_report)
    results = [result.to_json_dict() for result in validation_results]
    report = {
        "stage": stage,
        "success": all(result.success for result in validation_results),
        "row_count": int(len(df)),
        "expectations": results,
        "freshness": freshness,
    }
    write_json(_quality_report_path(settings, stage), report)
    return report


def evaluate_freshness_sla(
    df: pd.DataFrame, settings: Settings, report_path: Path | None = None
) -> dict[str, Any]:
    """Evaluate the 25% stale-row SLA and write its lineage report."""
    published = pd.to_datetime(df.get("published"), errors="coerce")
    if "age_days" in df:
        age_days = pd.to_numeric(df["age_days"], errors="coerce")
    else:
        today = pd.Timestamp(datetime.now(UTC)).tz_localize(None).normalize()
        age_days = (today - published.dt.normalize()).dt.days

    total_rows = int(len(df))
    stale_rows = int((age_days > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    valid_dates = published.dropna()
    report = {
        "latest_published": valid_dates.max().date().isoformat() if not valid_dates.empty else None,
        "oldest_published": valid_dates.min().date().isoformat() if not valid_dates.empty else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": 0.25,
        "is_fresh": stale_ratio <= 0.25,
    }
    write_json(Path(report_path or settings.paths.freshness_report), report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
    """Backward-compatible name for :func:`evaluate_freshness_sla`."""
    return evaluate_freshness_sla(df, settings, report_path)
