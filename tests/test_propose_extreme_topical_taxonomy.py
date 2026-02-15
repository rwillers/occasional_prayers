from __future__ import annotations

from tests.module_loader import load_script_module


propose_extreme_topical_taxonomy = load_script_module(
    "propose_extreme_topical_taxonomy"
)


def test_season_for_tag_maps_expected_values() -> None:
    assert propose_extreme_topical_taxonomy._season_for_tag("Eastertide") == "Easter"
    assert (
        propose_extreme_topical_taxonomy._season_for_tag("The Ascension Day")
        == "Ascension"
    )
    assert (
        propose_extreme_topical_taxonomy._season_for_tag("Saints’ Days and Holy Days")
        == "Other Feasts"
    )


def test_fuzzy_topical_map_uses_explicit_alias() -> None:
    canonical = ["The Church", "Family and Personal Life"]
    mapped, reason = propose_extreme_topical_taxonomy._fuzzy_topical_map(
        "The Church at Home", canonical
    )
    assert mapped == "The Church"
    assert reason == "explicit_alias_rule"


def test_fuzzy_topical_map_can_use_token_overlap() -> None:
    canonical = ["Family and Personal Life", "Social Order"]
    mapped, reason = propose_extreme_topical_taxonomy._fuzzy_topical_map(
        "Family and Personal Life (Throughout the Day)",
        canonical,
    )
    assert mapped == "Family and Personal Life"
    assert reason in {"explicit_alias_rule", "token_overlap_map"}
