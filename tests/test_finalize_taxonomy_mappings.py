from __future__ import annotations

import csv
from pathlib import Path

from tests.module_loader import load_script_module


finalize_taxonomy_mappings = load_script_module("finalize_taxonomy_mappings")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_main_applies_merge_decision_and_writes_redirect(
    tmp_path: Path, monkeypatch
) -> None:
    taxonomy_dir = tmp_path / "taxonomy"
    taxonomy_dir.mkdir(parents=True)

    proposed_path = taxonomy_dir / "tag_mapping_proposed.csv"
    merge_path = taxonomy_dir / "tag_merge_candidates.csv"
    final_path = taxonomy_dir / "tag_mapping_final.csv"
    redirects_path = taxonomy_dir / "tag_redirect_from_merges.csv"
    summary_path = taxonomy_dir / "finalization_summary.md"

    _write_csv(
        proposed_path,
        [
            "raw_value",
            "assignment_count",
            "file_count",
            "overlap_file_count",
            "overlap_ratio",
            "canonical_value",
            "reviewed_action",
            "reviewed_facet",
            "tag_surface_policy",
            "confidence",
            "rationale",
            "review_notes",
        ],
        [
            {
                "raw_value": "Epiphany",
                "assignment_count": "10",
                "file_count": "10",
                "overlap_file_count": "0",
                "overlap_ratio": "0.00",
                "canonical_value": "Epiphany",
                "reviewed_action": "keep",
                "reviewed_facet": "liturgical_season",
                "tag_surface_policy": "retain_tag",
                "confidence": "medium",
                "rationale": "topical_default",
                "review_notes": "",
            },
            {
                "raw_value": "The Epiphany",
                "assignment_count": "2",
                "file_count": "2",
                "overlap_file_count": "0",
                "overlap_ratio": "0.00",
                "canonical_value": "The Epiphany",
                "reviewed_action": "keep",
                "reviewed_facet": "liturgical_season",
                "tag_surface_policy": "retain_tag",
                "confidence": "medium",
                "rationale": "topical_default",
                "review_notes": "",
            },
        ],
    )
    _write_csv(
        merge_path,
        [
            "tag_a",
            "tag_b",
            "assignment_count_a",
            "assignment_count_b",
            "proposed_canonical",
            "reason",
            "review_decision",
            "review_notes",
        ],
        [
            {
                "tag_a": "Epiphany",
                "tag_b": "The Epiphany",
                "assignment_count_a": "10",
                "assignment_count_b": "2",
                "proposed_canonical": "Epiphany",
                "reason": "punctuation_or_article_variant",
                "review_decision": "merge",
                "review_notes": "",
            }
        ],
    )

    monkeypatch.setattr(finalize_taxonomy_mappings, "PROPOSED_PATH", proposed_path)
    monkeypatch.setattr(finalize_taxonomy_mappings, "MERGE_DECISIONS_PATH", merge_path)
    monkeypatch.setattr(finalize_taxonomy_mappings, "FINAL_MAPPING_PATH", final_path)
    monkeypatch.setattr(
        finalize_taxonomy_mappings, "MERGE_REDIRECTS_PATH", redirects_path
    )
    monkeypatch.setattr(
        finalize_taxonomy_mappings, "FINALIZATION_SUMMARY_PATH", summary_path
    )

    assert finalize_taxonomy_mappings.main() == 0
    assert final_path.exists()
    assert redirects_path.exists()
    assert summary_path.exists()

    with final_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    the_epiphany = next(row for row in rows if row["raw_value"] == "The Epiphany")
    assert the_epiphany["canonical_value"] == "Epiphany"
    assert the_epiphany["reviewed_action"] == "merge"
    assert the_epiphany["tag_surface_policy"] == "remove_from_tags"

    with redirects_path.open("r", encoding="utf-8", newline="") as handle:
        redirects = list(csv.DictReader(handle))
    assert len(redirects) == 1
    assert redirects[0]["old_tag"] == "The Epiphany"
    assert redirects[0]["new_tag"] == "Epiphany"
