#!/usr/bin/env python3
"""Build taxonomy inventory and mapping templates from markdown front matter."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
import re
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "migration" / "taxonomy"
SUMMARY_PATH = OUTPUT_DIR / "inventory_summary.md"
TAG_INVENTORY_PATH = OUTPUT_DIR / "tag_inventory.csv"
ATTRIBUTION_INVENTORY_PATH = OUTPUT_DIR / "attribution_inventory.csv"
TAG_ATTRIBUTION_OVERLAP_PATH = OUTPUT_DIR / "tag_attribution_overlap.csv"
CITATION_LIKE_TAGS_PATH = OUTPUT_DIR / "citation_like_tags.csv"
SOURCE_PROVENANCE_TAGS_PATH = OUTPUT_DIR / "source_provenance_tags.csv"
NORMALIZATION_CANDIDATES_PATH = OUTPUT_DIR / "normalization_candidates.csv"
TAG_MAPPING_TEMPLATE_PATH = OUTPUT_DIR / "tag_mapping_template.csv"
TAG_MAPPING_SEED_PATH = OUTPUT_DIR / "tag_mapping_seed.csv"
ATTRIBUTION_MAPPING_TEMPLATE_PATH = OUTPUT_DIR / "attribution_mapping_template.csv"
TAG_REDIRECT_TEMPLATE_PATH = OUTPUT_DIR / "tag_redirect_template.csv"

DEFAULT_PAGE_PATHS = [
    "index-pelican.md",
    "about.md",
    "search.md",
    "notfound.md",
    "acna2019",
    "acna2019collects",
    "coe1559",
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

_BOOK_KEYWORDS = [
    "genesis",
    "exodus",
    "leviticus",
    "numbers",
    "deuteronomy",
    "joshua",
    "judges",
    "ruth",
    "samuel",
    "kings",
    "chronicles",
    "ezra",
    "nehemiah",
    "esther",
    "job",
    "psalm",
    "psalms",
    "proverbs",
    "ecclesiastes",
    "song of",
    "isaiah",
    "jeremiah",
    "ezekiel",
    "daniel",
    "hosea",
    "joel",
    "amos",
    "obadiah",
    "jonah",
    "micah",
    "nahum",
    "habakkuk",
    "zephaniah",
    "haggai",
    "zechariah",
    "malachi",
    "matthew",
    "mark",
    "luke",
    "john",
    "acts",
    "romans",
    "corinthians",
    "galatians",
    "ephesians",
    "philippians",
    "colossians",
    "thessalonians",
    "timothy",
    "titus",
    "philemon",
    "hebrews",
    "james",
    "peter",
    "jude",
    "revelation",
]
_SCRIPTURE_BOOK_PATTERN = re.compile(
    rf"\b(?:[1-3]\s*)?(?:{'|'.join(re.escape(keyword) for keyword in _BOOK_KEYWORDS)})\b\.?\s+\d",
    re.IGNORECASE,
)
_SOURCE_MARKER_TERMS = {
    "prayer book",
    "book of",
    "book",
    "breviary",
    "sacramentary",
    "missal",
    "liturgy",
    "order",
    "office",
    "service book",
    "euchologium",
    "canon",
    "church order",
    "diocese",
    "church of",
    "guild",
    "society",
    "board",
    "conference",
    "convocation",
    "synod",
}


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


def _normalize_attribution(raw_value: Any) -> str:
    if raw_value is None:
        return ""
    return str(raw_value).strip()


def _classify_tag(tag_name: str) -> str:
    lowered = tag_name.lower()
    provenance = _extract_provenance_target(tag_name)
    if provenance is not None:
        _, target = provenance
        if _is_scripture_reference(target):
            return "citation_provenance_scripture"
        return "provenance_non_scriptural_source"
    if _is_scripture_reference(tag_name):
        return "bible_reference_like"
    if any(term in lowered for term in _SOURCE_MARKER_TERMS):
        return "source_like"
    return "topic_or_source"


def _is_citation_like(tag_name: str) -> bool:
    classification = _classify_tag(tag_name)
    return classification in {"citation_provenance_scripture", "bible_reference_like"}


def _is_source_like(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _SOURCE_MARKER_TERMS)


def _extract_provenance_target(tag_name: str) -> tuple[str, str] | None:
    lowered = tag_name.lower()
    prefixes = ("after ", "adapted from ", "based on ", "from ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return prefix.strip(), tag_name[len(prefix) :].strip()
    return None


def _is_scripture_reference(value: str) -> bool:
    return bool(_SCRIPTURE_BOOK_PATTERN.search(value))


def _is_source_provenance_like(tag_name: str) -> bool:
    classification = _classify_tag(tag_name)
    return classification == "provenance_non_scriptural_source"


def _normalization_key(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", lowered).strip()
    return re.sub(r"\s+", " ", normalized)


def _sort_by_count_then_name(counter: Counter[str]) -> list[tuple[str, int]]:
    return sorted(counter.items(), key=lambda item: (-item[1], item[0].casefold()))


def _section_for_path(path: Path) -> str:
    rel_path = path.relative_to(ROOT)
    parts = rel_path.parts
    if len(parts) <= 1:
        return "(root)"
    return parts[0]


def _write_csv(
    path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    markdown_files = _iter_markdown_files()

    tag_counts: Counter[str] = Counter()
    tag_files: dict[str, set[str]] = defaultdict(set)
    tag_sections: dict[str, set[str]] = defaultdict(set)

    attribution_counts: Counter[str] = Counter()
    attribution_files: dict[str, set[str]] = defaultdict(set)
    attribution_sections: dict[str, set[str]] = defaultdict(set)

    overlap_counts: Counter[str] = Counter()
    front_matter_errors: list[tuple[str, str]] = []

    for markdown_file in markdown_files:
        rel_path = markdown_file.relative_to(ROOT).as_posix()
        section = _section_for_path(markdown_file)
        text = markdown_file.read_text(encoding="utf-8")
        raw_front_matter, front_matter_error = _extract_front_matter(text)
        if front_matter_error:
            front_matter_errors.append((rel_path, front_matter_error))
            continue

        try:
            parsed = yaml.safe_load(raw_front_matter) or {}
        except yaml.YAMLError:
            front_matter_errors.append((rel_path, "front_matter_yaml_error"))
            continue
        if not isinstance(parsed, dict):
            front_matter_errors.append((rel_path, "front_matter_not_mapping"))
            continue

        deduped_tags = list(dict.fromkeys(_normalize_tags(parsed.get("tags"))))
        attribution = _normalize_attribution(parsed.get("attribution"))

        for tag_name in deduped_tags:
            tag_counts[tag_name] += 1
            tag_files[tag_name].add(rel_path)
            tag_sections[tag_name].add(section)

        if attribution:
            attribution_counts[attribution] += 1
            attribution_files[attribution].add(rel_path)
            attribution_sections[attribution].add(section)
            if attribution in deduped_tags:
                overlap_counts[attribution] += 1

    sorted_tags = _sort_by_count_then_name(tag_counts)
    sorted_attributions = _sort_by_count_then_name(attribution_counts)

    tag_rows: list[dict[str, Any]] = []
    citation_rows: list[dict[str, Any]] = []
    source_provenance_rows: list[dict[str, Any]] = []
    normalization_groups: dict[str, set[str]] = defaultdict(set)
    for tag_name, assignment_count in sorted_tags:
        classification = _classify_tag(tag_name)
        file_count = len(tag_files[tag_name])
        sections = sorted(tag_sections[tag_name], key=str.casefold)
        tag_rows.append(
            {
                "tag": tag_name,
                "assignment_count": assignment_count,
                "file_count": file_count,
                "section_count": len(sections),
                "sections": ";".join(sections),
                "classification": classification,
                "citation_like": "yes" if _is_citation_like(tag_name) else "no",
            }
        )
        if _is_citation_like(tag_name):
            citation_rows.append(
                {
                    "tag": tag_name,
                    "assignment_count": assignment_count,
                    "file_count": file_count,
                    "classification": classification,
                }
            )
        elif _is_source_provenance_like(tag_name):
            source_provenance_rows.append(
                {
                    "tag": tag_name,
                    "assignment_count": assignment_count,
                    "file_count": file_count,
                    "classification": classification,
                }
            )
        key = _normalization_key(tag_name)
        if key:
            normalization_groups[key].add(tag_name)

    attribution_rows: list[dict[str, Any]] = []
    for attribution, assignment_count in sorted_attributions:
        attribution_rows.append(
            {
                "attribution": attribution,
                "assignment_count": assignment_count,
                "file_count": len(attribution_files[attribution]),
                "section_count": len(attribution_sections[attribution]),
                "as_tag_overlap_count": overlap_counts.get(attribution, 0),
            }
        )

    overlap_rows: list[dict[str, Any]] = []
    for value, overlap_count in sorted(
        overlap_counts.items(), key=lambda item: (-item[1], item[0].casefold())
    ):
        sections = sorted(
            attribution_sections.get(value, set()) | tag_sections.get(value, set()),
            key=str.casefold,
        )
        overlap_rows.append(
            {
                "value": value,
                "overlap_file_count": overlap_count,
                "tag_assignment_count": tag_counts.get(value, 0),
                "attribution_assignment_count": attribution_counts.get(value, 0),
                "section_count": len(sections),
                "sections": ";".join(sections),
            }
        )

    normalization_rows: list[dict[str, Any]] = []
    for key, variants in sorted(
        normalization_groups.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        if len(variants) <= 1:
            continue
        sorted_variants = sorted(variants, key=str.casefold)
        total_assignments = sum(tag_counts[variant] for variant in sorted_variants)
        normalization_rows.append(
            {
                "normalized_key": key,
                "variant_count": len(sorted_variants),
                "total_assignments": total_assignments,
                "variants": " | ".join(sorted_variants),
            }
        )

    tag_mapping_rows = [
        {
            "raw_value": row["tag"],
            "assignment_count": row["assignment_count"],
            "file_count": row["file_count"],
            "canonical_value": row["tag"],
            "facet": "",
            "action": "keep",
            "notes": "",
        }
        for row in tag_rows
    ]

    tag_mapping_seed_rows: list[dict[str, Any]] = []
    for row in tag_rows:
        tag_name = str(row["tag"])
        assignment_count = int(row["assignment_count"])
        overlap_count = overlap_counts.get(tag_name, 0)

        suggested_action = "keep"
        suggested_facet = ""
        suggestion_reason = "default_keep"

        if _is_citation_like(tag_name):
            suggested_action = "move_to_citation"
            suggested_facet = "citation_scripture"
            suggestion_reason = "scripture_reference_or_provenance"
        elif _is_source_provenance_like(tag_name):
            suggested_action = "move_to_source"
            suggested_facet = "source"
            suggestion_reason = "non_scriptural_provenance_prefix"
        elif overlap_count > 0 and overlap_count >= assignment_count * 0.8:
            if _is_source_like(tag_name):
                suggested_action = "move_to_source"
                suggested_facet = "source"
                suggestion_reason = "high_overlap_and_source_like"
            else:
                suggested_action = "move_to_attribution"
                suggested_facet = "attribution"
                suggestion_reason = "high_tag_attribution_overlap"

        tag_mapping_seed_rows.append(
            {
                "raw_value": tag_name,
                "assignment_count": assignment_count,
                "file_count": row["file_count"],
                "overlap_file_count": overlap_count,
                "canonical_value": tag_name,
                "suggested_facet": suggested_facet,
                "suggested_action": suggested_action,
                "suggestion_reason": suggestion_reason,
                "reviewed_action": "",
                "reviewed_facet": "",
                "review_notes": "",
            }
        )

    attribution_mapping_rows = [
        {
            "raw_value": row["attribution"],
            "assignment_count": row["assignment_count"],
            "file_count": row["file_count"],
            "canonical_value": row["attribution"],
            "action": "keep",
            "notes": "",
        }
        for row in attribution_rows
    ]

    redirect_template_rows = [
        {
            "old_tag": "",
            "new_tag": "",
            "old_path": "",
            "new_path": "",
            "status": "301",
            "note": "",
        }
    ]

    _write_csv(
        TAG_INVENTORY_PATH,
        (
            "tag",
            "assignment_count",
            "file_count",
            "section_count",
            "sections",
            "classification",
            "citation_like",
        ),
        tag_rows,
    )
    _write_csv(
        ATTRIBUTION_INVENTORY_PATH,
        (
            "attribution",
            "assignment_count",
            "file_count",
            "section_count",
            "as_tag_overlap_count",
        ),
        attribution_rows,
    )
    _write_csv(
        TAG_ATTRIBUTION_OVERLAP_PATH,
        (
            "value",
            "overlap_file_count",
            "tag_assignment_count",
            "attribution_assignment_count",
            "section_count",
            "sections",
        ),
        overlap_rows,
    )
    _write_csv(
        CITATION_LIKE_TAGS_PATH,
        ("tag", "assignment_count", "file_count", "classification"),
        citation_rows,
    )
    _write_csv(
        SOURCE_PROVENANCE_TAGS_PATH,
        ("tag", "assignment_count", "file_count", "classification"),
        source_provenance_rows,
    )
    _write_csv(
        NORMALIZATION_CANDIDATES_PATH,
        ("normalized_key", "variant_count", "total_assignments", "variants"),
        normalization_rows,
    )
    _write_csv(
        TAG_MAPPING_TEMPLATE_PATH,
        (
            "raw_value",
            "assignment_count",
            "file_count",
            "canonical_value",
            "facet",
            "action",
            "notes",
        ),
        tag_mapping_rows,
    )
    _write_csv(
        TAG_MAPPING_SEED_PATH,
        (
            "raw_value",
            "assignment_count",
            "file_count",
            "overlap_file_count",
            "canonical_value",
            "suggested_facet",
            "suggested_action",
            "suggestion_reason",
            "reviewed_action",
            "reviewed_facet",
            "review_notes",
        ),
        tag_mapping_seed_rows,
    )
    _write_csv(
        ATTRIBUTION_MAPPING_TEMPLATE_PATH,
        (
            "raw_value",
            "assignment_count",
            "file_count",
            "canonical_value",
            "action",
            "notes",
        ),
        attribution_mapping_rows,
    )
    _write_csv(
        TAG_REDIRECT_TEMPLATE_PATH,
        ("old_tag", "new_tag", "old_path", "new_path", "status", "note"),
        redirect_template_rows,
    )

    top_tags = sorted_tags[:20]
    top_attributions = sorted_attributions[:20]
    lines: list[str] = [
        "# Taxonomy Inventory Summary",
        "",
        f"- Markdown files scanned: `{len(markdown_files)}`",
        f"- Distinct tags: `{len(tag_counts)}`",
        f"- Distinct attribution values: `{len(attribution_counts)}`",
        f"- Tag/attribution overlap values: `{len(overlap_counts)}`",
        f"- Scriptural citation-like tags: `{len(citation_rows)}`",
        f"- Non-scriptural source provenance tags: `{len(source_provenance_rows)}`",
        f"- Normalization candidate groups: `{len(normalization_rows)}`",
        f"- Front matter parse issues: `{len(front_matter_errors)}`",
        "",
        "## Top Tags",
    ]
    if not top_tags:
        lines.append("- None")
    else:
        for tag_name, count in top_tags:
            lines.append(f"- `{tag_name}`: {count}")

    lines.extend(["", "## Top Attribution Values"])
    if not top_attributions:
        lines.append("- None")
    else:
        for attribution, count in top_attributions:
            lines.append(f"- `{attribution}`: {count}")

    lines.extend(["", "## Generated Artifacts"])
    lines.extend(
        [
            "- `migration/taxonomy/tag_inventory.csv`",
            "- `migration/taxonomy/attribution_inventory.csv`",
            "- `migration/taxonomy/tag_attribution_overlap.csv`",
            "- `migration/taxonomy/citation_like_tags.csv`",
            "- `migration/taxonomy/source_provenance_tags.csv`",
            "- `migration/taxonomy/normalization_candidates.csv`",
            "- `migration/taxonomy/tag_mapping_template.csv`",
            "- `migration/taxonomy/tag_mapping_seed.csv`",
            "- `migration/taxonomy/attribution_mapping_template.csv`",
            "- `migration/taxonomy/tag_redirect_template.csv`",
        ]
    )
    if front_matter_errors:
        lines.extend(["", "## Front Matter Parse Issues"])
        for path, kind in front_matter_errors[:20]:
            lines.append(f"- `{path}`: `{kind}`")

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
