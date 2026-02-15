from __future__ import annotations

from tests.module_loader import load_script_module


propose_taxonomy_mappings = load_script_module("propose_taxonomy_mappings")


def test_normalized_text_removes_articles_punctuation() -> None:
    assert propose_taxonomy_mappings._normalized_text("The Church’s Year") == (
        "churchs year"
    )
    assert propose_taxonomy_mappings._normalized_text("Family & Personal Life") == (
        "family and personal life"
    )


def test_token_stem_handles_plural_forms() -> None:
    assert propose_taxonomy_mappings._token_stem("thanksgivings") == "thanksgiving"
    assert propose_taxonomy_mappings._token_stem("families") == "family"


def test_facet_for_keep_recognizes_seasons_and_context() -> None:
    assert propose_taxonomy_mappings._facet_for_keep("Advent") == "liturgical_season"
    assert propose_taxonomy_mappings._facet_for_keep("Intercessory Prayers") == (
        "prayer_type"
    )
    assert propose_taxonomy_mappings._facet_for_keep("The Nation") == (
        "life_or_church_context"
    )


def test_merge_candidate_reason_detects_token_equivalence() -> None:
    left = propose_taxonomy_mappings.TagRow(
        tag="Thanksgivings",
        assignment_count=48,
        file_count=48,
    )
    right = propose_taxonomy_mappings.TagRow(
        tag="Thanksgiving",
        assignment_count=4,
        file_count=4,
    )
    reason = propose_taxonomy_mappings._merge_candidate_reason(left, right)
    assert reason in {
        "token_set_equivalent_variant",
        "high_token_overlap_candidate",
    }


def test_scripture_detection_requires_reference_numbers() -> None:
    assert propose_taxonomy_mappings._is_scripture_reference("Romans 12:1-2")
    assert not propose_taxonomy_mappings._is_scripture_reference("John Donne")


def test_prefixed_provenance_routes_to_source_and_citation() -> None:
    action, facet, _, _ = propose_taxonomy_mappings._provenance_action_for_prefixed_tag(
        "Adapted from Book of Common Prayer"
    )
    assert action == "move_to_source"
    assert facet == "source_text"

    action, facet, _, _ = propose_taxonomy_mappings._provenance_action_for_prefixed_tag(
        "Based on Romans 12:1-2"
    )
    assert action == "move_to_citation"
    assert facet == "citation_scripture"


def test_overlap_source_like_prefers_source_over_attribution() -> None:
    action, facet, _, _ = propose_taxonomy_mappings._provenance_action_for_overlap_tag(
        "American Prayer Book", 0.92
    )
    assert action == "move_to_source"
    assert facet == "source_text"
