from __future__ import annotations

from tests.module_loader import load_script_module


apply_option2_taxonomy = load_script_module("apply_option2_taxonomy")


def test_map_tags_handles_keep_map_drop_and_missing() -> None:
    mapping = {
        "A": apply_option2_taxonomy.TagDecision(action="keep", target="A"),
        "B": apply_option2_taxonomy.TagDecision(action="map", target="C"),
        "D": apply_option2_taxonomy.TagDecision(action="drop", target=""),
    }
    mapped, dropped, remapped, missing = apply_option2_taxonomy._map_tags(
        ["A", "B", "D", "Z"],
        mapping,
    )
    assert mapped == ["A", "C"]
    assert dropped == ["D"]
    assert remapped == ["B -> C"]
    assert missing == ["Z"]


def test_replace_tags_line_updates_existing_front_matter_tags() -> None:
    raw = "---\n" "title: Example\n" "tags: ['Old']\n" "layout: page\n" "---\n" "Body\n"
    updated = apply_option2_taxonomy._replace_tags_line(raw, ["New", "Other"])
    assert "tags: [New, Other]" in updated
    assert "tags: ['Old']" not in updated
