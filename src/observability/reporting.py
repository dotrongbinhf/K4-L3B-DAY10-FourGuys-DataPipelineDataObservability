from __future__ import annotations

from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
    per_query: list[dict[str, Any]] | None = None,
) -> None:
    """Write a concise, auditable Markdown report for the baseline run."""
    expectation_results = quality.get("expectations", [])

    def expectation_success(expectation_type: str, column: str | None = None) -> bool:
        for result in expectation_results:
            config = result.get("expectation_config", {})
            if config.get("type") != expectation_type:
                continue
            if column is not None and config.get("kwargs", {}).get("column") != column:
                continue
            return bool(result.get("success"))
        return False

    required_non_null = all(
        expectation_success("expect_column_values_to_not_be_null", column)
        for column in ("paper_id", "title", "text_for_embedding")
    )
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source",
        "",
        f"- Records ingested: {source_summary.get('records_ingested', 0)}",
        f"- Clean records: {source_summary.get('clean_records', 0)}",
        f"- Benchmark questions: {source_summary.get('test_questions', 0)}",
        f"- Chroma collection: {source_summary.get('collection_name', 'unknown')}",
        f"- Indexed documents: {source_summary.get('indexed_documents', 'unknown')}",
        f"- Source mode: {source_summary.get('source_mode', 'unknown')}",
        "",
        "## Evaluation",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Samples | {metrics.get('samples', 0)} |",
        f"| Retrieval hit rate | {metrics.get('retrieval_hit_rate', 0.0):.3f} |",
        f"| Mean token F1 | {metrics.get('mean_token_f1', 0.0):.3f} |",
        f"| Judge accuracy | {metrics.get('judge_accuracy', 0.0):.3f} |",
        f"| Mean judge score | {metrics.get('mean_judge_score', 0.0):.3f} |",
        "",
        "## Data Quality",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Great Expectations gate | {'PASS' if quality.get('success', False) else 'FAIL'} |",
        f"| Row count | {quality.get('row_count', 0)} |",
        f"| Required non-null fields | {'PASS' if required_non_null else 'FAIL'} |",
        f"| Unique paper_id | {'PASS' if expectation_success('expect_column_values_to_be_unique', 'paper_id') else 'FAIL'} |",
        f"| Summary minimum length (30 chars) | {'PASS' if expectation_success('expect_column_value_lengths_to_be_between', 'summary') else 'FAIL'} |",
        f"| Freshness SLA (<= 25% older than {freshness.get('freshness_threshold_days', 180)} days) | {'PASS' if freshness.get('is_fresh', False) else 'FAIL'} |",
        f"| Stale rows | {freshness.get('stale_rows', 0)}/{freshness.get('total_rows', 0)} ({freshness.get('stale_ratio', 0.0):.1%}) |",
        f"| Latest published | {freshness.get('latest_published', 'N/A')} |",
        f"| Oldest published | {freshness.get('oldest_published', 'N/A')} |",
        "",
        "## Per-Query Results",
        "",
        "| ID | Type | Hit | Token F1 | Ground-truth documents | Retrieved documents |",
        "|---|---|---:|---:|---|---|",
    ]
    for item in per_query or []:
        ground_truth_ids = ", ".join(item.get("ground_truth_doc_ids", []))
        retrieved_ids = ", ".join(item.get("retrieved_doc_ids", []))
        lines.append(
            f"| {item.get('id', '')} | {item.get('question_type', '')} | "
            f"{'Yes' if item.get('retrieval_hit') else 'No'} | {item.get('token_f1', 0.0):.3f} | "
            f"{ground_truth_ids} | {retrieved_ids} |"
        )
    lines.extend([
        "",
        "## Generated Artifacts",
        "",
        "- `data/clean/papers_clean.csv`",
        "- `data/clean/papers_clean.json`",
        "- `data/eval/test_set.json`",
        "- `data/results/baseline_metrics.json`",
        "- `data/results/baseline_answers.json`",
        "- `data/quality/baseline_quality_report.json`",
        "- `data/quality/freshness_report.json`",
        "",
    ])
    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    raise NotImplementedError("Student task: implement corruption comparison report.")
