from __future__ import annotations

from tests.module_loader import load_script_module


audit_metadata = load_script_module("audit_metadata")


def test_extract_front_matter_success() -> None:
    raw = "---\ntitle: Example\nlayout: page\n---\nBody"
    front_matter, error = audit_metadata._extract_front_matter(raw)
    assert error == ""
    assert "title: Example" in front_matter


def test_extract_front_matter_missing() -> None:
    front_matter, error = audit_metadata._extract_front_matter("title: missing")
    assert front_matter is None
    assert error == "missing_front_matter"


def test_normalize_tags_from_string_and_list() -> None:
    assert audit_metadata._normalize_tags("one, two") == ["one", "two"]
    assert audit_metadata._normalize_tags(["one", " two "]) == ["one", "two"]
    assert audit_metadata._normalize_tags('["alpha", "beta"]') == ["alpha", "beta"]


def test_normalize_layout() -> None:
    assert audit_metadata._normalize_layout(" Page ") == "page"
