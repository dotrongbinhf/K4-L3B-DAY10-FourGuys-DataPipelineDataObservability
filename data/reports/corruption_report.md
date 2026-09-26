# Corruption, Repair, and Impact Report

## Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Samples | 10 | 10 | 10 |
| Retrieval hit rate | 1.000 | 0.500 | 1.000 |
| Mean token F1 | 0.900 | 0.621 | 0.900 |
| Judge accuracy | 0.900 | 0.600 | 0.900 |
| Mean judge score | 4.600 | 3.400 | 4.600 |
| Quality gate | PASS | FAIL | PASS |
| Data rows | 24 | 20 | 24 |
| Freshness SLA | PASS | PASS | PASS |
| Stale ratio | 0.0% | 5.0% | 0.0% |

## Measured impact

- Corruption versus baseline: retrieval hit rate -0.500; mean token F1 -0.279.
- Repair versus corruption: retrieval hit rate +0.500; mean token F1 +0.279.
- Repair versus baseline: retrieval hit rate +0.000; mean token F1 +0.000.

The corrupted rows were indexed and evaluated even though their quality gate failed. This measures the silent failure that a gate should prevent in production.

## Recovery method

The repaired dataset was rebuilt from the original raw Crossref snapshot, validated, and indexed in ChromaDB before evaluation. The benchmark questions and ground truth were kept fixed across all three states.

## Artifacts

- `data/results/corruption_log.json`
- `data/results/baseline_metrics.json`
- `data/results/corrupted_metrics.json`
- `data/results/repaired_metrics.json`
- `data/quality/corrupted_quality_report.json`
- `data/quality/repaired_quality_report.json`
- `data/clean/papers_clean_corrupted.json`
- `data/clean/papers_clean_repaired.json`
