from __future__ import annotations

from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a concise, auditable Markdown report for the baseline run."""
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source",
        "",
        f"- Records ingested: {source_summary.get('records_ingested', 0)}",
        f"- Clean records: {source_summary.get('clean_records', 0)}",
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
        f"- Great Expectations gate passed: **{quality.get('success', False)}**",
        f"- Freshness SLA passed: **{freshness.get('is_fresh', False)}**",
        f"- Stale rows: {freshness.get('stale_rows', 0)}/{freshness.get('total_rows', 0)} "
        f"({freshness.get('stale_ratio', 0.0):.1%})",
        f"- Latest published: {freshness.get('latest_published', 'N/A')}",
        f"- Oldest published: {freshness.get('oldest_published', 'N/A')}",
        "",
    ]
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
