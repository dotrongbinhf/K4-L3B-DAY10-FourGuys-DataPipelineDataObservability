from __future__ import annotations

import json

import pandas as pd

from ingestion.corruption import corrupt_clean_dataframe


def _clean_rows(count: int = 10) -> pd.DataFrame:
    rows = []
    for index in range(count):
        published = (pd.Timestamp("2026-09-20") - pd.Timedelta(days=index)).date().isoformat()
        rows.append({
            "paper_id": f"10.1234/test.{index}",
            "title": f"Paper title {index}",
            "summary": f"A sufficiently long summary for paper number {index} with useful details.",
            "authors_joined": f"Author {index}",
            "categories_joined": "Computer science",
            "published": published,
            "age_days": index,
            "summary_chars": 70,
            "text_for_embedding": "original text",
        })
    return pd.DataFrame(rows)


def test_corruption_is_auditable_deterministic_and_does_not_mutate_input(tmp_path):
    original = _clean_rows()
    snapshot = original.copy(deep=True)

    first_log = tmp_path / "first.json"
    second_log = tmp_path / "second.json"
    first = corrupt_clean_dataframe(original, first_log)
    second = corrupt_clean_dataframe(original, second_log)

    pd.testing.assert_frame_equal(original, snapshot)
    pd.testing.assert_frame_equal(first, second)
    assert json.loads(first_log.read_text()) == json.loads(second_log.read_text())

    log = json.loads(first_log.read_text())
    expected = {
        "drop_latest_records", "blank_summary", "inject_noise", "truncate_title",
        "stale_date", "duplicate_rows",
    }
    assert set(log["summary"]["corruption_types"]) == expected
    assert log["summary"]["input_rows"] == 10
    assert log["summary"]["output_rows"] == 9

    dropped_ids = {
        event["paper_id"] for event in log["events"]
        if event["corruption_type"] == "drop_latest_records"
    }
    assert dropped_ids == {"10.1234/test.0", "10.1234/test.1"}
    assert (first["summary"] == "").any()
    assert first["summary"].str.contains("qzxv_noise_7f3a", regex=False).any()
    assert (first["title"].str.len() < 8).any()
    stale_event = next(event for event in log["events"] if event["corruption_type"] == "stale_date")
    stale_row = first[first["paper_id"] == stale_event["paper_id"]].iloc[0]
    assert pd.Timestamp(stale_event["before"]) - pd.Timestamp(stale_event["after"]) == pd.Timedelta(days=365)
    assert stale_row["age_days"] == int(stale_event["age_days"])
    assert first["paper_id"].duplicated().any()

    for _, row in first.iterrows():
        assert row["title"] in row["text_for_embedding"]
        assert row["summary"] in row["text_for_embedding"]
        assert row["published"] in row["text_for_embedding"]
