#!/usr/bin/env python3
"""Finalize Extreme Taxonomy Option 2 (core + 4 structural fallback tags)."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_DIR = ROOT / "migration" / "taxonomy"
EXTREME_DIR = TAXONOMY_DIR / "extreme"

EXTREME_MAPPING_PATH = EXTREME_DIR / "extreme_tag_mapping_proposed.csv"
EXTREME_CANONICAL_PATH = EXTREME_DIR / "canonical_tags.csv"

OPTION2_MAPPING_PATH = EXTREME_DIR / "option2_final_mapping.csv"
OPTION2_CANONICAL_PATH = EXTREME_DIR / "option2_final_canonical_tags.csv"
OPTION2_PAGE_PREVIEW_PATH = EXTREME_DIR / "option2_final_page_remap_preview.csv"
OPTION2_PAGES_WITHOUT_TAGS_PATH = EXTREME_DIR / "option2_final_pages_without_tags.txt"
OPTION2_SUMMARY_PATH = EXTREME_DIR / "option2_final_summary.md"

DEFAULT_PAGE_PATHS = [
    "index-pelican.md",
    "about.md",
    "search.md",
    "notfound.md",
    "acna2019",
    "acna2019collects",
    "coe1662",
    "coi2004",
    "davidtaylor",
    "other",
    "parish-devotional",
    "parish-intercessory",
    "parish-occasions",
    "parish-sacraments",
    "parish-supplementary",
    "parish-year",
    "potec",
    "tag",
    "tec1928",
    "tec1979",
]
EXTRA_AUDIT_FILES = ["index.md", "404.md"]

OPTION2_STRUCTURAL_FALLBACK_TAGS = [
    "The Church’s Year",
    "Intercessory Prayers",
    "Various Occasions",
    "Devotional Prayers",
    "Sacraments and Ordinances",
    "Supplementary Prayers",
    "Pastoral",
    "The World",
    "Commons of Commemoration",
    "Collects",
]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _page_paths() -> list[str]:
    try:
        from pelicanconf import PAGE_PATHS  # type: ignore

        return [str(item) for item in PAGE_PATHS]
    except Exception:
        return DEFAULT_PAGE_PATHS


def _iter_markdown_files() -> list[Path]:
    discovered: set[Path] = set()
    for entry in _page_paths():
        path = ROOT / entry
        if path.is_file() and path.suffix == ".md":
            discovered.add(path)
            continue
        if path.is_dir():
            for markdown_file in path.rglob("*.md"):
                discovered.add(markdown_file)

    for extra in EXTRA_AUDIT_FILES:
        path = ROOT / extra
        if path.exists():
            discovered.add(path)
    return sorted(discovered)


def _extract_front_matter(text: str) -> tuple[str | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing_front_matter"

    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return None, "unterminated_front_matter"

    return "\n".join(lines[1:end_index]), ""


def _normalize_tags(raw_value: Any) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        value = raw_value.strip()
        if not value:
            return []
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = yaml.safe_load(value)
            except yaml.YAMLError:
                parsed = None
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    return [str(raw_value).strip()] if str(raw_value).strip() else []


def _apply_option2_overrides(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    fallback_set = set(OPTION2_STRUCTURAL_FALLBACK_TAGS)
    final_rows: list[dict[str, str]] = []
    for row in rows:
        updated = dict(row)
        if updated["raw_tag"] in fallback_set:
            updated["extreme_action"] = "keep"
            updated["extreme_tag"] = updated["raw_tag"]
            updated["reason"] = "option2_structural_fallback"
            updated["confidence"] = "high"
        final_rows.append(updated)
    return final_rows


def main() -> int:
    extreme_rows = _read_rows(EXTREME_MAPPING_PATH)
    canonical_rows = _read_rows(EXTREME_CANONICAL_PATH)
    option2_rows = _apply_option2_overrides(extreme_rows)

    fallback_rows = [
        {"tag": tag_name, "group": "structural_fallback"}
        for tag_name in OPTION2_STRUCTURAL_FALLBACK_TAGS
    ]
    canonical_combined = canonical_rows + fallback_rows
    _write_csv(OPTION2_CANONICAL_PATH, ("tag", "group"), canonical_combined)

    option2_rows_sorted = sorted(
        option2_rows,
        key=lambda row: (-int(row["assignment_count"]), row["raw_tag"].casefold()),
    )
    _write_csv(
        OPTION2_MAPPING_PATH,
        (
            "raw_tag",
            "assignment_count",
            "current_action",
            "current_facet",
            "extreme_action",
            "extreme_tag",
            "reason",
            "confidence",
        ),
        option2_rows_sorted,
    )

    action_counts: Counter[str] = Counter()
    assignment_counts: Counter[str] = Counter()
    tag_lookup: dict[str, str | None] = {}
    for row in option2_rows:
        action = row["extreme_action"]
        assignment = int(row["assignment_count"])
        action_counts[action] += 1
        assignment_counts[action] += assignment
        if action in {"keep", "map"}:
            tag_lookup[row["raw_tag"]] = row["extreme_tag"]
        else:
            tag_lookup[row["raw_tag"]] = None

    markdown_files = _iter_markdown_files()
    page_preview_rows: list[dict[str, str]] = []
    pages_without_tags: list[str] = []
    mapped_tag_counts: Counter[str] = Counter()
    pages_with_tags = 0

    for markdown_file in markdown_files:
        rel_path = markdown_file.relative_to(ROOT).as_posix()
        text = markdown_file.read_text(encoding="utf-8")
        raw_front_matter, err = _extract_front_matter(text)
        if err:
            continue
        parsed = yaml.safe_load(raw_front_matter) or {}
        if not isinstance(parsed, dict):
            continue

        original_tags = _normalize_tags(parsed.get("tags"))
        mapped_tags: set[str] = set()
        for tag_name in original_tags:
            mapped_tag = tag_lookup.get(tag_name)
            if mapped_tag:
                mapped_tags.add(mapped_tag)

        if mapped_tags:
            pages_with_tags += 1
            for mapped_tag in mapped_tags:
                mapped_tag_counts[mapped_tag] += 1
        else:
            pages_without_tags.append(rel_path)

        page_preview_rows.append(
            {
                "path": rel_path,
                "original_tag_count": str(len(original_tags)),
                "option2_tag_count": str(len(mapped_tags)),
                "option2_tags": " | ".join(sorted(mapped_tags, key=str.casefold)),
            }
        )

    page_preview_rows.sort(key=lambda row: row["path"].casefold())
    _write_csv(
        OPTION2_PAGE_PREVIEW_PATH,
        ("path", "original_tag_count", "option2_tag_count", "option2_tags"),
        page_preview_rows,
    )
    OPTION2_PAGES_WITHOUT_TAGS_PATH.write_text(
        "\n".join(sorted(pages_without_tags, key=str.casefold)) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Extreme Option 2 Final Summary",
        "",
        "Policy:",
        "- Start from extreme proposal (ACNA topical + seasons + Other Feasts).",
        "- Add structural fallback tags (core + 4) as allowed topical tags.",
        "",
        "## Structural Fallback Tags",
    ]
    for tag_name in OPTION2_STRUCTURAL_FALLBACK_TAGS:
        lines.append(f"- `{tag_name}`")

    lines.extend(["", "## Tag Mapping Impact (By Distinct Tag Rows)"])
    for action in ("keep", "map", "drop"):
        lines.append(f"- `{action}`: {action_counts[action]}")

    lines.extend(["", "## Tag Mapping Impact (By Tag Assignments)"])
    for action in ("keep", "map", "drop"):
        lines.append(f"- `{action}`: {assignment_counts[action]}")

    lines.extend(
        [
            "",
            "## Page Coverage",
            f"- Pages with >=1 option2 tag: `{pages_with_tags}`",
            f"- Pages without option2 tags: `{len(pages_without_tags)}`",
            "",
            "## Top Option2 Tags (By Page Count)",
        ]
    )
    for tag_name, count in mapped_tag_counts.most_common(25):
        lines.append(f"- `{tag_name}`: {count}")

    lines.extend(
        [
            "",
            "## Artifacts",
            "- `migration/taxonomy/extreme/option2_final_canonical_tags.csv`",
            "- `migration/taxonomy/extreme/option2_final_mapping.csv`",
            "- `migration/taxonomy/extreme/option2_final_page_remap_preview.csv`",
            "- `migration/taxonomy/extreme/option2_final_pages_without_tags.txt`",
        ]
    )
    OPTION2_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
