from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records, parse_crossref_payload
from observability.quality import run_data_quality_checks
from observability.reporting import (
    format_corruption_comparison_table,
    generate_corruption_report,
)
from retrieval.index import LocalEmbeddingIndex


def repair_from_raw_snapshot(settings: Settings) -> pd.DataFrame:
    """Recreate clean papers from immutable raw input, never from corrupted rows."""
    if settings.paths.raw_records_json.exists():
        records = load_raw_records(settings.paths.raw_records_json)
    elif settings.paths.raw_api_response.exists():
        records = parse_crossref_payload(read_json(settings.paths.raw_api_response))
    else:
        raise FileNotFoundError("No raw Crossref snapshot is available for repair.")

    repaired = build_clean_dataframe(records, datetime.now(UTC))
    if repaired.empty:
        raise RuntimeError("Raw snapshot produced no repairable records.")

    quality = run_data_quality_checks(repaired, settings, stage="repaired")
    if not quality["success"] or not quality["freshness"]["is_fresh"]:
        raise RuntimeError("Repaired data failed the quality or freshness gate; Chroma was not changed.")

    write_csv(repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired.to_dict(orient="records"))
    return repaired


def run_corruption_flow_pipeline(settings: Settings) -> dict[str, Any]:
    """Measure corrupted retrieval, restore from raw, and compare all three states."""
    paths = settings.paths
    required = (
        paths.clean_json, paths.baseline_metrics, paths.baseline_quality_report,
        paths.eval_testset,
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Phase 1 artifacts are missing; run python script/run_phase1.py first: "
            + ", ".join(missing)
        )

    baseline_metrics = read_json(paths.baseline_metrics)
    baseline_quality = read_json(paths.baseline_quality_report)
    clean_df = pd.DataFrame(read_json(paths.clean_json))
    if clean_df.empty:
        raise RuntimeError("The Phase 1 clean dataset is empty.")

    corrupted_df = corrupt_clean_dataframe(clean_df, paths.corruption_log)
    write_csv(corrupted_df, paths.corrupted_clean_csv)
    write_json(paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, stage="corrupted")

    # A failed gate must not hide the downstream impact measured by this lab.
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, paths.corrupted_embeddings_json
    )
    corrupted_evaluation = evaluate_pipeline(
        settings, corrupted_index, paths.eval_testset,
        paths.corrupted_metrics, paths.corrupted_answers,
    )

    repaired_df = repair_from_raw_snapshot(settings)
    repaired_quality = read_json(paths.quality_dir / "repaired_quality_report.json")
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, paths.repaired_embeddings_json
    )
    repaired_evaluation = evaluate_pipeline(
        settings, repaired_index, paths.eval_testset,
        paths.repaired_metrics, paths.repaired_answers,
    )

    generate_corruption_report(
        paths.comparison_report,
        baseline_metrics,
        corrupted_evaluation.summary,
        repaired_evaluation.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_quality["freshness"],
        repaired_quality["freshness"],
        baseline_quality,
    )
    return {
        "baseline_metrics": baseline_metrics,
        "baseline_quality": baseline_quality,
        "corrupted_metrics": corrupted_evaluation.summary,
        "repaired_metrics": repaired_evaluation.summary,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
        "corrupted_documents": corrupted_index.collection.count(),
        "repaired_documents": repaired_index.collection.count(),
        "report_path": str(paths.comparison_report),
    }


def main() -> None:
    result = run_corruption_flow_pipeline(load_settings())
    print(format_corruption_comparison_table(
        result["baseline_metrics"], result["corrupted_metrics"],
        result["repaired_metrics"], result["corrupted_quality"],
        result["repaired_quality"],
        baseline_quality=result["baseline_quality"],
    ))
    print(f"Report: {result['report_path']}")
