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
    baseline_quality: dict[str, Any] | None = None,
) -> None:
    """Write measured impact, repair, and quality evidence for all stages."""
    table = format_corruption_comparison_table(
        baseline_metrics, corrupted_metrics, repaired_metrics,
        corrupted_quality, repaired_quality,
        corrupted_freshness, repaired_freshness, baseline_quality,
    )
    hit_drop = corrupted_metrics["retrieval_hit_rate"] - baseline_metrics["retrieval_hit_rate"]
    hit_recovery = repaired_metrics["retrieval_hit_rate"] - corrupted_metrics["retrieval_hit_rate"]
    f1_drop = corrupted_metrics["mean_token_f1"] - baseline_metrics["mean_token_f1"]
    f1_recovery = repaired_metrics["mean_token_f1"] - corrupted_metrics["mean_token_f1"]
    lines = [
        "# Corruption, Repair, and Impact Report",
        "",
        "## Comparison",
        "",
        table,
        "",
        "## Measured impact",
        "",
        f"- Corruption versus baseline: retrieval hit rate {hit_drop:+.3f}; mean token F1 {f1_drop:+.3f}.",
        f"- Repair versus corruption: retrieval hit rate {hit_recovery:+.3f}; mean token F1 {f1_recovery:+.3f}.",
        f"- Repair versus baseline: retrieval hit rate {repaired_metrics['retrieval_hit_rate'] - baseline_metrics['retrieval_hit_rate']:+.3f}; mean token F1 {repaired_metrics['mean_token_f1'] - baseline_metrics['mean_token_f1']:+.3f}.",
        "",
        "The corrupted rows were indexed and evaluated even though their quality gate failed. "
        "This measures the silent failure that a gate should prevent in production.",
        "",
        "## Recovery method",
        "",
        "The repaired dataset was rebuilt from the original raw Crossref snapshot, "
        "validated, and indexed in ChromaDB before evaluation. The benchmark "
        "questions and ground truth were kept fixed across all three states.",
        "",
        "## Artifacts",
        "",
        "- `data/results/corruption_log.json`",
        "- `data/results/baseline_metrics.json`",
        "- `data/results/corrupted_metrics.json`",
        "- `data/results/repaired_metrics.json`",
        "- `data/quality/corrupted_quality_report.json`",
        "- `data/quality/repaired_quality_report.json`",
        "- `data/clean/papers_clean_corrupted.json`",
        "- `data/clean/papers_clean_repaired.json`",
        "",
    ]
    write_text(report_path, "\n".join(lines))


def format_corruption_comparison_table(
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any] | None = None,
    repaired_freshness: dict[str, Any] | None = None,
    baseline_quality: dict[str, Any] | None = None,
) -> str:
    """Use the same three-state Markdown table in the report and console."""
    corrupted_freshness = corrupted_freshness or corrupted_quality["freshness"]
    repaired_freshness = repaired_freshness or repaired_quality["freshness"]
    baseline_freshness = baseline_quality.get("freshness", {}) if baseline_quality else {}
    baseline_gate = ("PASS" if baseline_quality["success"] else "FAIL") if baseline_quality else "-"
    baseline_rows = str(baseline_quality["row_count"]) if baseline_quality else "-"
    baseline_sla = (
        "PASS" if baseline_freshness["is_fresh"] else "FAIL"
    ) if baseline_freshness else "-"
    baseline_stale = f"{baseline_freshness['stale_ratio']:.1%}" if baseline_freshness else "-"
    rows = [
        "| Metric | Baseline | Corrupted | Repaired |",
        "|---|---:|---:|---:|",
    ]
    for label, key in (
        ("Samples", "samples"),
        ("Retrieval hit rate", "retrieval_hit_rate"),
        ("Mean token F1", "mean_token_f1"),
        ("Judge accuracy", "judge_accuracy"),
        ("Mean judge score", "mean_judge_score"),
    ):
        values = [baseline_metrics[key], corrupted_metrics[key], repaired_metrics[key]]
        rendered = [str(int(value)) if key == "samples" else f"{value:.3f}" for value in values]
        rows.append(f"| {label} | {' | '.join(rendered)} |")
    rows.extend([
        f"| Quality gate | {baseline_gate} | {'PASS' if corrupted_quality['success'] else 'FAIL'} | {'PASS' if repaired_quality['success'] else 'FAIL'} |",
        f"| Data rows | {baseline_rows} | {corrupted_quality['row_count']} | {repaired_quality['row_count']} |",
        f"| Freshness SLA | {baseline_sla} | {'PASS' if corrupted_freshness['is_fresh'] else 'FAIL'} | {'PASS' if repaired_freshness['is_fresh'] else 'FAIL'} |",
        f"| Stale ratio | {baseline_stale} | {corrupted_freshness['stale_ratio']:.1%} | {repaired_freshness['stale_ratio']:.1%} |",
    ])
    return "\n".join(rows)
