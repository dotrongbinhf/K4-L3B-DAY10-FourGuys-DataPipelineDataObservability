# Phase 1 Baseline Report

## Source

- Records ingested: 24
- Clean records: 24
- Benchmark questions: 10
- Chroma collection: papers-baseline
- Indexed documents: 24
- Source mode: local raw snapshot

## Evaluation

| Metric | Value |
|---|---:|
| Samples | 10 |
| Retrieval hit rate | 0.900 |
| Mean token F1 | 0.614 |
| Judge accuracy | 0.600 |
| Mean judge score | 3.400 |

## Data Quality

| Check | Result |
|---|---|
| Great Expectations gate | PASS |
| Row count | 24 |
| Required non-null fields | PASS |
| Unique paper_id | PASS |
| Summary minimum length (30 chars) | PASS |
| Freshness SLA (<= 25% older than 180 days) | PASS |
| Stale rows | 0/24 (0.0%) |
| Latest published | 2026-09-15 |
| Oldest published | 2026-04-01 |

## Per-Query Results

| ID | Type | Hit | Token F1 | Ground-truth documents | Retrieved documents |
|---|---|---:|---:|---|---|
| eval_001 | summary | Yes | 1.000 | 10.21203/rs.3.rs-10489777/v1 | 10.21203/rs.3.rs-10489777/v1, 10.55041/isjem07213, 10.36887/2415-8453-2026-3-2, 10.20944/preprints202604.0339.v1 |
| eval_002 | authors | Yes | 0.000 | 10.70267/aitia.2026482489 | 10.55041/isjem07213, 10.20944/preprints202604.0339.v1, 10.54254/2755-2721/2026.36624, 10.70267/aitia.2026482489 |
| eval_003 | date | Yes | 1.000 | 10.21203/rs.3.rs-10349437/v1 | 10.21203/rs.3.rs-10349437/v1, 10.1093/sleep/zsag091.0346, 10.1007/s10278-026-02086-9, 10.55041/isjem07213 |
| eval_004 | categories | Yes | 1.000 | 10.54254/2755-2721/2026.36624 | 10.54254/2755-2721/2026.36624, 10.55041/isjem07213, 10.20944/preprints202604.0339.v1, 10.36887/2415-8453-2026-3-2 |
| eval_005 | summary | Yes | 1.000 | 10.36887/2415-8453-2026-3-2 | 10.36887/2415-8453-2026-3-2, 10.54254/2755-2721/2026.36624, 10.36948/ijfmr.2026.v08i04.85777, 10.20944/preprints202604.0339.v1 |
| eval_006 | authors | No | 0.000 | 10.28932/jutisi.v12i2.13099 | 10.55041/isjem07213, 10.20944/preprints202604.0339.v1, 10.54254/2755-2721/2026.36624, 10.47576/2949-1894.2026.7.7.023 |
| eval_007 | date | Yes | 0.000 | 10.20944/preprints202608.1849.v1 | 10.55041/isjem07213, 10.36948/ijfmr.2026.v08i04.85777, 10.20944/preprints202608.1849.v1, 10.20944/preprints202604.0339.v1 |
| eval_008 | categories | Yes | 1.000 | 10.21203/rs.3.rs-10423755/v1 | 10.21203/rs.3.rs-10423755/v1, 10.55041/isjem07213, 10.54254/2755-2721/2026.36624, 10.36887/2415-8453-2026-3-2 |
| eval_009 | summary | Yes | 0.140 | 10.3390/knowledge6030022 | 10.20944/preprints202604.0339.v1, 10.36948/ijfmr.2026.v08i04.85777, 10.3390/knowledge6030022, 10.55041/isjem07213 |
| eval_010 | authors | Yes | 1.000 | 10.36948/ijfmr.2026.v08i04.85777 | 10.36948/ijfmr.2026.v08i04.85777, 10.55041/isjem07213, 10.20944/preprints202604.0339.v1, 10.1093/sleep/zsag091.0346 |

## Generated Artifacts

- `data/clean/papers_clean.csv`
- `data/clean/papers_clean.json`
- `data/eval/test_set.json`
- `data/results/baseline_metrics.json`
- `data/results/baseline_answers.json`
- `data/quality/baseline_quality_report.json`
- `data/quality/freshness_report.json`
