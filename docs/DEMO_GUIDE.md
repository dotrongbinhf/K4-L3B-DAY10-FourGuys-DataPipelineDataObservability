# Live Demo & Q&A Guide

## Demo flow (3–5 minutes)

1. **Show the pipeline and baseline:** run `uv run python script/run_phase1.py`. Point to `data/reports/phase1_report.md` and the baseline quality report. Explain that 24 clean records become 24 vectors in `papers-baseline` and are evaluated against 10 fixed questions.
2. **Inject corruption and measure impact:** run `uv run python script/run_corruption_flow.py`. Open `data/results/corruption_log.json` and identify its six corruption types. Show the quality gate failing on duplicate `paper_id` and blank summary.
3. **Explain freshness separately:** corrupted stale ratio is 5% (1/20), so freshness remains PASS under the 25% SLA even while the structural/content gate fails.
4. **Show repair:** point out that repair rebuilds from `data/raw/crossref_records.json`, validates, reindexes, and evaluates with the same test set. Show the three-state table in `data/reports/corruption_report.md`.
5. **Close with measured results:** baseline → corrupted → repaired Hit Rate is 1.000 → 0.500 → 1.000; token F1 is 0.900 → 0.621 → 0.900.

## Commands

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

For a prepared demo, run both commands once before presenting and keep the generated reports open. Neither command requires an LLM key in the default configuration; the benchmark uses deterministic field extraction and a heuristic judge. Ragas is skipped unless `RUN_RAGAS=1`.

## Q&A talking points

- **Why GX 1.x Ephemeral Context?** It creates an in-memory pandas datasource/batch for a one-run validation without persisting GX context configuration.
- **What does the quality gate check?** Row count 5–5000, non-null `paper_id`/`title`/`text_for_embedding`, unique `paper_id`, and summary length ≥30 characters.
- **How is freshness different?** Freshness counts rows with `age_days > 180`; it flags stale only when their share exceeds 25%. It is reported separately from the GX expectations.
- **Why does corrupted freshness still pass?** One of 20 rows is stale (5%), below the 25% SLA, while the duplicate and blank summary fail other quality checks.
- **How is retrieval measured?** The evaluator searches Chroma using MiniLM embeddings and checks whether the retrieved IDs contain the ground-truth DOI. It does not promote a document using the quoted title.
- **Why keep one test set?** The same question/ground-truth pairs isolate the effect of data corruption and repair.
- **What makes repair idempotent?** It reconstructs clean records from the immutable raw snapshot and recreates the repaired Chroma collection instead of editing corrupted rows in place.
- **Is the judge an LLM?** No. The current report uses the reproducible heuristic judge and skips Ragas by default; describe those as limitations.

## Before presenting/submitting

- Confirm the latest `main` is pushed and each teammate appears in GitHub Insights → Contributors.
- Fill real names, student IDs, and roles in `docs/TEAM.md` and `report/group_report.md`.
- Each member writes their own `report/<MSSV>_<HoTen>.md` and submits the repository link on LMS.
- Keep all secrets out of Git and the screen share.
