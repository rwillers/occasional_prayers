#!/usr/bin/env python3
"""Propose an extreme topical taxonomy based on ACNA 2019 topical tags."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
import re
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_DIR = ROOT / "migration" / "taxonomy"
EXTREME_DIR = TAXONOMY_DIR / "extreme"

FINAL_MAPPING_PATH = TAXONOMY_DIR / "tag_mapping_final.csv"
CANONICAL_TAGS_PATH = EXTREME_DIR / "canonical_tags.csv"
EXTREME_MAPPING_PATH = EXTREME_DIR / "extreme_tag_mapping_proposed.csv"
SUMMARY_PATH = EXTREME_DIR / "extreme_summary.md"
PAGE_PREVIEW_PATH = EXTREME_DIR / "extreme_page_remap_preview.csv"
PAGES_WITHOUT_TAGS_PATH = EXTREME_DIR / "pages_without_extreme_tags.txt"

SEASON_CANONICAL_TAGS = [
    "Advent",
    "Christmas",
    "Epiphany",
    "Lent",
    "Holy Week",
    "Easter",
    "Ascension",
    "Pentecost",
    "Trinity Season",
    "Other Feasts",
]

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

TOPICAL_FACETS = {"topic", "prayer_type", "life_or_church_context", "liturgical_season"}
NON_TOPICAL_ACTIONS = {
    "move_to_source",
    "move_to_attribution",
    "move_to_citation",
    "merge",
}

EXPLICIT_ALIAS_MAP = {
    "church at home": "The Church",
    "church overseas": "The Church",
    "church of god": "The Church",
    "our nation and government": "The Nation",
    "nations of the world": "The Nation",
    "family and personal life throughout the day": "Family and Personal Life",
    "rites of healing prayers for use by a sick person": "Rites of Healing",
    "at evening": "At Times of Prayer and Worship",
    "in the morning": "At Times of Prayer and Worship",
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


def _normalized_text(value: str) -> str:
    lowered = value.lower().replace("&", " and ")
    lowered = lowered.replace("’", "'")
    lowered = lowered.replace("'", "")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    if lowered.startswith("the "):
        lowered = lowered[4:]
    return lowered


def _token_stem(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _normalized_tokens(value: str) -> set[str]:
    tokens = _normalized_text(value).split()
    return {_token_stem(token) for token in tokens if token}


def _read_final_mapping() -> list[dict[str, str]]:
    with FINAL_MAPPING_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _acna_topical_canonical_tags(final_rows: list[dict[str, str]]) -> list[str]:
    acna_files = sorted((ROOT / "acna2019").rglob("*.md"))
    first_tags: list[str] = []
    for path in acna_files:
        text = path.read_text(encoding="utf-8")
        raw_front_matter, err = _extract_front_matter(text)
        if err:
            continue
        parsed = yaml.safe_load(raw_front_matter) or {}
        if not isinstance(parsed, dict):
            continue
        tags = _normalize_tags(parsed.get("tags"))
        if tags:
            first_tags.append(tags[0])

    seen: set[str] = set()
    unique_first_tags: list[str] = []
    for tag in first_tags:
        if tag in seen:
            continue
        seen.add(tag)
        unique_first_tags.append(tag)

    by_raw = {row["raw_value"]: row for row in final_rows}
    canonical: list[str] = []
    for tag in unique_first_tags:
        row = by_raw.get(tag)
        if row is None:
            continue
        if row["reviewed_action"] == "keep" and row["reviewed_facet"] in TOPICAL_FACETS:
            canonical.append(tag)
    return canonical


def _season_for_tag(tag_name: str) -> str | None:
    normalized = _normalized_text(tag_name)
    if "advent" in normalized:
        return "Advent"
    if "christmas" in normalized or "nativity" in normalized:
        return "Christmas"
    if "epiphany" in normalized:
        return "Epiphany"
    if "lent" in normalized or "ash wednesday" in normalized:
        return "Lent"
    if (
        "holy week" in normalized
        or "palm sunday" in normalized
        or "good friday" in normalized
        or "maundy" in normalized
    ):
        return "Holy Week"
    if "easter" in normalized:
        return "Easter"
    if "ascension" in normalized:
        return "Ascension"
    if "pentecost" in normalized or "whitsun" in normalized:
        return "Pentecost"
    if "trinity season" in normalized or "season after pentecost" in normalized:
        return "Trinity Season"
    if (
        "saints days and holy days" in normalized
        or normalized == "holy days"
        or "lesser feasts" in normalized
        or "feast" in normalized
        or "rogation" in normalized
        or "ember" in normalized
    ):
        return "Other Feasts"
    return None


def _fuzzy_topical_map(
    tag_name: str, canonical_tags: list[str]
) -> tuple[str | None, str]:
    normalized = _normalized_text(tag_name)
    alias_target = EXPLICIT_ALIAS_MAP.get(normalized)
    if alias_target is not None:
        return alias_target, "explicit_alias_rule"

    tokens = _normalized_tokens(tag_name)
    if not tokens:
        return None, "no_tokens"

    best_tag: str | None = None
    best_score = 0.0
    for candidate in canonical_tags:
        candidate_tokens = _normalized_tokens(candidate)
        if not candidate_tokens:
            continue
        score = len(tokens & candidate_tokens) / len(tokens | candidate_tokens)
        if score > best_score:
            best_score = score
            best_tag = candidate
    if best_tag is not None and best_score >= 0.66:
        return best_tag, "token_overlap_map"
    return None, "no_confident_map"


def _write_csv(
    path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    final_rows = _read_final_mapping()
    canonical_acna_tags = _acna_topical_canonical_tags(final_rows)
    canonical_tag_set = set(canonical_acna_tags) | set(SEASON_CANONICAL_TAGS)

    canonical_rows: list[dict[str, str]] = []
    for tag in canonical_acna_tags:
        canonical_rows.append({"tag": tag, "group": "acna_topical"})
    for tag in SEASON_CANONICAL_TAGS:
        canonical_rows.append({"tag": tag, "group": "seasonal"})
    _write_csv(CANONICAL_TAGS_PATH, ("tag", "group"), canonical_rows)

    mapping_rows: list[dict[str, str]] = []
    extreme_tag_lookup: dict[str, str | None] = {}
    row_counts: Counter[str] = Counter()
    assignment_counts: Counter[str] = Counter()

    for row in final_rows:
        raw_tag = row["raw_value"]
        assignment_count = int(row["assignment_count"])
        reviewed_action = row["reviewed_action"]
        reviewed_facet = row["reviewed_facet"]

        extreme_action = "drop"
        extreme_tag = ""
        reason = "not_in_extreme_canonical_set"
        confidence = "medium"

        if raw_tag in canonical_tag_set:
            extreme_action = "keep"
            extreme_tag = raw_tag
            reason = "canonical_exact"
            confidence = "high"
        elif reviewed_action in NON_TOPICAL_ACTIONS:
            extreme_action = "drop"
            reason = "non_topical_provenance_or_alias"
            confidence = "high"
        else:
            season_tag = _season_for_tag(raw_tag)
            if season_tag is not None:
                extreme_action = "map"
                extreme_tag = season_tag
                reason = "seasonal_rule"
                confidence = "high"
            else:
                mapped_tag, mapped_reason = _fuzzy_topical_map(
                    raw_tag, canonical_acna_tags
                )
                if mapped_tag is not None:
                    extreme_action = "map"
                    extreme_tag = mapped_tag
                    reason = mapped_reason
                    confidence = "medium"

        if extreme_action in {"keep", "map"}:
            extreme_tag_lookup[raw_tag] = extreme_tag
        else:
            extreme_tag_lookup[raw_tag] = None

        row_counts[extreme_action] += 1
        assignment_counts[extreme_action] += assignment_count

        mapping_rows.append(
            {
                "raw_tag": raw_tag,
                "assignment_count": str(assignment_count),
                "current_action": reviewed_action,
                "current_facet": reviewed_facet,
                "extreme_action": extreme_action,
                "extreme_tag": extreme_tag,
                "reason": reason,
                "confidence": confidence,
            }
        )

    mapping_rows.sort(
        key=lambda item: (-int(item["assignment_count"]), item["raw_tag"].casefold())
    )
    _write_csv(
        EXTREME_MAPPING_PATH,
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
        mapping_rows,
    )

    markdown_files = _iter_markdown_files()
    pages_with_tags = 0
    pages_without_tags: list[str] = []
    mapped_tag_counts: Counter[str] = Counter()
    page_preview_rows: list[dict[str, str]] = []

    for markdown_file in markdown_files:
        rel_path = markdown_file.relative_to(ROOT).as_posix()
        text = markdown_file.read_text(encoding="utf-8")
        raw_front_matter, err = _extract_front_matter(text)
        if err:
            continue
        parsed = yaml.safe_load(raw_front_matter) or {}
        if not isinstance(parsed, dict):
            continue

        raw_tags = _normalize_tags(parsed.get("tags"))
        mapped_tags: set[str] = set()
        for tag_name in raw_tags:
            mapped_tag = extreme_tag_lookup.get(tag_name)
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
                "original_tag_count": str(len(raw_tags)),
                "extreme_tag_count": str(len(mapped_tags)),
                "extreme_tags": " | ".join(sorted(mapped_tags, key=str.casefold)),
            }
        )

    page_preview_rows.sort(key=lambda item: item["path"].casefold())
    _write_csv(
        PAGE_PREVIEW_PATH,
        ("path", "original_tag_count", "extreme_tag_count", "extreme_tags"),
        page_preview_rows,
    )
    PAGES_WITHOUT_TAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAGES_WITHOUT_TAGS_PATH.write_text(
        "\n".join(sorted(pages_without_tags, key=str.casefold)) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Extreme Topical Taxonomy Summary",
        "",
        "Policy modeled:",
        "- Canonical topical tags = ACNA 2019 first-position topical tags.",
        "- Keep explicit season tags plus `Other Feasts`.",
        "- Drop all non-topical provenance tags.",
        "- Drop non-canonical topical tags unless mapped by season or explicit/fuzzy alias.",
        "",
        "## Canonical Set",
        f"- ACNA topical canonical tags: `{len(canonical_acna_tags)}`",
        f"- Seasonal canonical tags: `{len(SEASON_CANONICAL_TAGS)}`",
        f"- Total canonical tags: `{len(canonical_tag_set)}`",
        "",
        "## Tag Mapping Impact (By Distinct Tag Rows)",
    ]
    for action in ("keep", "map", "drop"):
        lines.append(f"- `{action}`: {row_counts[action]}")

    lines.extend(["", "## Tag Mapping Impact (By Tag Assignments)"])
    for action in ("keep", "map", "drop"):
        lines.append(f"- `{action}`: {assignment_counts[action]}")

    lines.extend(
        [
            "",
            "## Page Coverage",
            f"- Pages with >=1 extreme topical tag: `{pages_with_tags}`",
            f"- Pages without extreme topical tags: `{len(pages_without_tags)}`",
            "",
            "## Top Extreme Tags (By Page Count)",
        ]
    )
    for tag_name, count in mapped_tag_counts.most_common(25):
        lines.append(f"- `{tag_name}`: {count}")

    lines.extend(
        [
            "",
            "## Artifacts",
            "- `migration/taxonomy/extreme/canonical_tags.csv`",
            "- `migration/taxonomy/extreme/extreme_tag_mapping_proposed.csv`",
            "- `migration/taxonomy/extreme/extreme_page_remap_preview.csv`",
            "- `migration/taxonomy/extreme/pages_without_extreme_tags.txt`",
        ]
    )

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
