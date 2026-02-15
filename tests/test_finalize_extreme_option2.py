from __future__ import annotations

from tests.module_loader import load_script_module


finalize_extreme_option2 = load_script_module("finalize_extreme_option2")


def test_apply_option2_overrides_promotes_structural_fallback_tags() -> None:
    rows = [
        {
            "raw_tag": "Intercessory Prayers",
            "assignment_count": "423",
            "current_action": "keep",
            "current_facet": "prayer_type",
            "extreme_action": "drop",
            "extreme_tag": "",
            "reason": "not_in_extreme_canonical_set",
            "confidence": "medium",
        },
        {
            "raw_tag": "Frank Colquhoun",
            "assignment_count": "109",
            "current_action": "move_to_attribution",
            "current_facet": "attribution_author",
            "extreme_action": "drop",
            "extreme_tag": "",
            "reason": "non_topical_provenance_or_alias",
            "confidence": "high",
        },
    ]

    updated = finalize_extreme_option2._apply_option2_overrides(rows)
    by_tag = {row["raw_tag"]: row for row in updated}

    structural = by_tag["Intercessory Prayers"]
    assert structural["extreme_action"] == "keep"
    assert structural["extreme_tag"] == "Intercessory Prayers"
    assert structural["reason"] == "option2_structural_fallback"
    assert structural["confidence"] == "high"

    non_structural = by_tag["Frank Colquhoun"]
    assert non_structural["extreme_action"] == "drop"
