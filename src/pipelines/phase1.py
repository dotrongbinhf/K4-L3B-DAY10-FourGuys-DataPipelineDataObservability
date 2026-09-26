from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from core.config import Settings, load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def run_phase1_pipeline(settings: Settings) -> dict[str, Any]:
    """Run the baseline ingestion-to-evaluation pipeline and persist all artifacts."""
    use_snapshot = not settings.refresh_source and settings.paths.raw_records_json.exists()
    records = load_raw_records(settings.paths.raw_records_json) if use_snapshot else fetch_source_records(settings)
    clean_df = build_clean_dataframe(records, datetime.now(UTC))

    # Persist both configured clean artifacts before quality validation so the
    # normalized Step 3 output is available even when the gate fails.
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    quality = run_data_quality_checks(clean_df, settings, stage="baseline")
    if not quality["success"]:
        raise RuntimeError("Baseline data failed the Great Expectations quality gate.")

    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    test_set = build_test_set(clean_df, settings.paths.eval_testset)
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    answers = evaluation.answers
    source_summary = {
        "records_ingested": len(records),
        "clean_records": len(clean_df),
        "source_mode": "local raw snapshot" if use_snapshot else "Crossref API/fallback snapshot",
        "test_questions": len(test_set),
        "collection_name": index.collection_name,
        "indexed_documents": index.collection.count(),
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=quality["freshness"],
        per_query=answers,
    )
    return {
        "source": source_summary,
        "metrics": evaluation.summary,
        "quality": quality,
        "report_path": str(settings.paths.baseline_report),
    }


def main() -> None:
    """Run Phase 1 from the command-line entry point."""
    result = run_phase1_pipeline(load_settings())
    metrics = result["metrics"]
    print(
        "Phase 1 completed: "
        f"hit rate={metrics['retrieval_hit_rate']:.3f}, "
        f"token F1={metrics['mean_token_f1']:.3f}"
    )
