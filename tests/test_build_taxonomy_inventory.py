from __future__ import annotations

from tests.module_loader import load_script_module


build_taxonomy_inventory = load_script_module("build_taxonomy_inventory")


def test_normalize_tags_from_supported_shapes() -> None:
    assert build_taxonomy_inventory._normalize_tags("one, two") == ["one", "two"]
    assert build_taxonomy_inventory._normalize_tags(["one", " two "]) == ["one", "two"]
    assert build_taxonomy_inventory._normalize_tags('["alpha", "beta"]') == [
        "alpha",
        "beta",
    ]


def test_classify_tag_detects_citation_prefixes() -> None:
    assert build_taxonomy_inventory._classify_tag("After St. Augustine") == (
        "provenance_non_scriptural_source"
    )
    assert (
        build_taxonomy_inventory._classify_tag("Adapted from Book of Common Prayer")
        == "provenance_non_scriptural_source"
    )
    assert build_taxonomy_inventory._classify_tag("Based on Romans 15:13") == (
        "citation_provenance_scripture"
    )


def test_classify_tag_detects_bible_reference_like_tag() -> None:
    assert build_taxonomy_inventory._classify_tag("Romans 12") == (
        "bible_reference_like"
    )


def test_classify_tag_does_not_treat_name_as_bible_reference() -> None:
    assert build_taxonomy_inventory._classify_tag("John Donne") == "topic_or_source"


def test_scripture_and_source_provenance_helpers() -> None:
    assert build_taxonomy_inventory._is_citation_like("Based on Romans 15:13")
    assert build_taxonomy_inventory._is_source_provenance_like(
        "Adapted from Book of Common Prayer"
    )


def test_normalization_key_collapses_whitespace_and_punctuation() -> None:
    assert build_taxonomy_inventory._normalization_key("Family & Personal Life") == (
        "family personal life"
    )
    assert build_taxonomy_inventory._normalization_key(
        "  Family   Personal  Life "
    ) == ("family personal life")
