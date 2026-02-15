#!/usr/bin/env python3
"""Generate Phase 2.5 proposed tag mappings from taxonomy inventory artifacts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_DIR = ROOT / "migration" / "taxonomy"
SEED_PATH = TAXONOMY_DIR / "tag_mapping_seed.csv"
TAG_INVENTORY_PATH = TAXONOMY_DIR / "tag_inventory.csv"

PROPOSED_MAPPING_PATH = TAXONOMY_DIR / "tag_mapping_proposed.csv"
MERGE_CANDIDATES_PATH = TAXONOMY_DIR / "tag_merge_candidates.csv"
PROPOSAL_SUMMARY_PATH = TAXONOMY_DIR / "proposal_summary.md"

_SEASON_TERMS = {
    "advent",
    "christmas",
    "epiphany",
    "lent",
    "holy week",
    "easter",
    "eastertide",
    "ascension",
    "pentecost",
    "trinity",
    "ember weeks",
    "rogation",
    "saints days and holy days",
    "holy days",
    "the season after pentecost",
    "the church year",
    "the churchs year",
}
_PRAYER_TYPE_TERMS = {
    "prayer",
    "prayers",
    "thanksgiving",
    "thanksgivings",
    "collect",
    "collects",
    "devotion",
    "devotions",
    "confession",
    "confessions",
}
_CONTEXT_TERMS = {
    "church",
    "nation",
    "world",
    "family",
    "home",
    "government",
    "peace",
    "war",
    "children",
    "sick",
    "missionary",
    "marriage",
}
_STOP_WORDS = {"the", "and", "of", "for", "to", "in", "on", "at", "with", "from"}
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
    "tradition of",
    "service",
    "services",
    "mission",
    "union",
    "college",
    "diary",
}
_NON_PERSON_HINTS = {
    "prayer",
    "book",
    "order",
    "church",
    "diocese",
    "guild",
    "society",
    "board",
    "conference",
    "convocation",
    "synod",
    "service",
    "liturgy",
    "sacramentary",
    "breviary",
    "missal",
    "office",
    "canon",
    "tradition",
}
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
_PROVENANCE_PREFIXES = (
    ("after", "after "),
    ("adapted_from", "adapted from "),
    ("based_on", "based on "),
    ("from", "from "),
)


@dataclass(frozen=True)
class TagRow:
    tag: str
    assignment_count: int
    file_count: int


def _read_seed_rows() -> list[dict[str, str]]:
    with SEED_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_tag_inventory_rows() -> list[TagRow]:
    rows: list[TagRow] = []
    with TAG_INVENTORY_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                TagRow(
                    tag=row["tag"],
                    assignment_count=int(row["assignment_count"]),
                    file_count=int(row["file_count"]),
                )
            )
    return rows


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


def _normalized_tokens(value: str) -> tuple[str, ...]:
    base = _normalized_text(value)
    if not base:
        return tuple()
    tokens = [token for token in base.split() if token and token not in _STOP_WORDS]
    stemmed = [_token_stem(token) for token in tokens]
    return tuple(stemmed)


def _facet_for_keep(tag_name: str) -> str:
    normalized = _normalized_text(tag_name)
    normalized_tokens = set(_normalized_tokens(tag_name))
    if normalized in _SEASON_TERMS:
        return "liturgical_season"
    if normalized_tokens & _PRAYER_TYPE_TERMS:
        return "prayer_type"
    if normalized_tokens & _CONTEXT_TERMS:
        return "life_or_church_context"
    return "topic"


def _is_scripture_reference(value: str) -> bool:
    return bool(_SCRIPTURE_BOOK_PATTERN.search(value))


def _looks_like_source_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _SOURCE_MARKER_TERMS)


def _is_probable_author_name(value: str) -> bool:
    if not value.strip():
        return False
    if _is_scripture_reference(value):
        return False
    lowered = value.lower()
    if any(hint in lowered for hint in _NON_PERSON_HINTS):
        return False
    title_like_tokens = {
        "every",
        "morning",
        "daily",
        "service",
        "services",
        "order",
        "book",
        "mission",
        "union",
        "college",
        "diary",
    }
    raw_tokens = re.findall(r"[A-Za-z']+", value.lower())
    if any(token in title_like_tokens for token in raw_tokens):
        return False
    if re.search(r"\d", value):
        return False
    pattern = re.compile(
        r"^(?:(?:st|saint)\.?\s+)?(?:[A-Z][A-Za-z'`.-]+|[A-Z]\.)"
        r"(?:\s+(?:[A-Z][A-Za-z'`.-]+|[A-Z]\.|of|the)){0,5}$"
    )
    return bool(pattern.match(value.strip()))


def _extract_provenance_target(tag_name: str) -> tuple[str, str] | None:
    lowered = tag_name.lower()
    for prefix_key, prefix_text in _PROVENANCE_PREFIXES:
        if lowered.startswith(prefix_text):
            return prefix_key, tag_name[len(prefix_text) :].strip()
    return None


def _provenance_action_for_prefixed_tag(tag_name: str) -> tuple[str, str, str, str]:
    parsed = _extract_provenance_target(tag_name)
    if parsed is None:
        return ("keep", _facet_for_keep(tag_name), "medium", "topical_default")

    prefix_key, target = parsed
    if _is_scripture_reference(target):
        return (
            "move_to_citation",
            "citation_scripture",
            "high",
            "prefixed_provenance_scripture_reference",
        )
    if _looks_like_source_text(target):
        return (
            "move_to_source",
            "source_text",
            "high",
            "prefixed_provenance_non_scriptural_source",
        )
    if prefix_key == "after" and _is_probable_author_name(target):
        return (
            "move_to_attribution",
            "attribution_author",
            "high",
            "after_prefix_author_attribution",
        )
    if prefix_key in {"based_on", "adapted_from", "from"}:
        return (
            "move_to_source",
            "source_text",
            "medium",
            "prefixed_provenance_default_source",
        )
    return (
        "move_to_source",
        "source_text",
        "medium",
        "prefixed_provenance_ambiguous_default_source",
    )


def _provenance_action_for_overlap_tag(
    tag_name: str, overlap_ratio: float
) -> tuple[str, str, str, str]:
    if _is_scripture_reference(tag_name):
        return (
            "move_to_citation",
            "citation_scripture",
            "high",
            "overlap_and_scripture_reference",
        )
    if _looks_like_source_text(tag_name):
        confidence = "high" if overlap_ratio >= 0.95 else "medium"
        return (
            "move_to_source",
            "source_text",
            confidence,
            "overlap_and_source_like_label",
        )
    if _is_probable_author_name(tag_name):
        confidence = "high" if overlap_ratio >= 0.95 else "medium"
        return (
            "move_to_attribution",
            "attribution_author",
            confidence,
            "overlap_and_author_like_label",
        )
    return (
        "move_to_source",
        "source_text",
        "medium",
        "overlap_ambiguous_default_source_needs_manual_check",
    )


def _proposal_for_seed_row(row: dict[str, str]) -> dict[str, str]:
    tag_name = row["raw_value"]
    assignment_count = int(row["assignment_count"] or 0)
    overlap_count = int(row["overlap_file_count"] or 0)
    suggested_action = row["suggested_action"]
    overlap_ratio = (overlap_count / assignment_count) if assignment_count else 0.0

    reviewed_action = "keep"
    reviewed_facet = _facet_for_keep(tag_name)
    confidence = "medium"
    rationale = "topical_default"

    prefixed_provenance = _extract_provenance_target(tag_name)
    if prefixed_provenance is not None or suggested_action == "move_to_citation":
        (
            reviewed_action,
            reviewed_facet,
            confidence,
            rationale,
        ) = _provenance_action_for_prefixed_tag(tag_name)
    elif suggested_action in {"move_to_attribution", "move_to_source"}:
        (
            reviewed_action,
            reviewed_facet,
            confidence,
            rationale,
        ) = _provenance_action_for_overlap_tag(tag_name, overlap_ratio)
    tag_surface_policy = (
        "retain_tag" if reviewed_action == "keep" else "remove_from_tags"
    )

    return {
        "raw_value": tag_name,
        "assignment_count": str(assignment_count),
        "file_count": row["file_count"],
        "overlap_file_count": str(overlap_count),
        "overlap_ratio": f"{overlap_ratio:.2f}",
        "canonical_value": row["canonical_value"] or tag_name,
        "reviewed_action": reviewed_action,
        "reviewed_facet": reviewed_facet,
        "tag_surface_policy": tag_surface_policy,
        "confidence": confidence,
        "rationale": rationale,
        "review_notes": "",
    }


def _canonical_pick(a: TagRow, b: TagRow) -> str:
    if a.assignment_count > b.assignment_count:
        return a.tag
    if b.assignment_count > a.assignment_count:
        return b.tag
    if len(a.tag) < len(b.tag):
        return a.tag
    if len(b.tag) < len(a.tag):
        return b.tag
    return min(a.tag, b.tag, key=str.casefold)


def _merge_candidate_reason(a: TagRow, b: TagRow) -> str | None:
    text_a = _normalized_text(a.tag)
    text_b = _normalized_text(b.tag)
    tokens_a = set(_normalized_tokens(a.tag))
    tokens_b = set(_normalized_tokens(b.tag))
    if not text_a or not text_b or not tokens_a or not tokens_b:
        return None

    if text_a == text_b:
        return "punctuation_or_article_variant"
    if tokens_a == tokens_b and a.tag.casefold() != b.tag.casefold():
        return "token_set_equivalent_variant"
    if tokens_a == tokens_b and text_a != text_b:
        return "token_set_equivalent_variant"

    union = tokens_a | tokens_b
    intersection = tokens_a & tokens_b
    if not union:
        return None
    jaccard = len(intersection) / len(union)
    if jaccard >= 0.8 and len(union) <= 4:
        return "high_token_overlap_candidate"
    return None


def _build_merge_candidates(tag_rows: list[TagRow]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    dedup: set[tuple[str, str]] = set()
    for left, right in combinations(tag_rows, 2):
        reason = _merge_candidate_reason(left, right)
        if reason is None:
            continue
        low, high = sorted((left.tag, right.tag), key=str.casefold)
        key = (low, high)
        if key in dedup:
            continue
        dedup.add(key)
        canonical = _canonical_pick(left, right)
        candidates.append(
            {
                "tag_a": left.tag,
                "tag_b": right.tag,
                "assignment_count_a": str(left.assignment_count),
                "assignment_count_b": str(right.assignment_count),
                "proposed_canonical": canonical,
                "reason": reason,
                "review_decision": "",
                "review_notes": "",
            }
        )

    candidates.sort(
        key=lambda row: (
            -max(int(row["assignment_count_a"]), int(row["assignment_count_b"])),
            row["reason"],
            row["tag_a"].casefold(),
            row["tag_b"].casefold(),
        )
    )
    return candidates[:200]


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
    seed_rows = _read_seed_rows()
    tag_rows = _read_tag_inventory_rows()

    proposed_rows = [_proposal_for_seed_row(row) for row in seed_rows]
    merge_rows = _build_merge_candidates(tag_rows)

    _write_csv(
        PROPOSED_MAPPING_PATH,
        (
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
        ),
        proposed_rows,
    )
    _write_csv(
        MERGE_CANDIDATES_PATH,
        (
            "tag_a",
            "tag_b",
            "assignment_count_a",
            "assignment_count_b",
            "proposed_canonical",
            "reason",
            "review_decision",
            "review_notes",
        ),
        merge_rows,
    )

    action_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}
    tag_surface_counts: dict[str, int] = {}
    for row in proposed_rows:
        action = row["reviewed_action"]
        confidence = row["confidence"]
        tag_surface_policy = row["tag_surface_policy"]
        action_counts[action] = action_counts.get(action, 0) + 1
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        tag_surface_counts[tag_surface_policy] = (
            tag_surface_counts.get(tag_surface_policy, 0) + 1
        )

    lines = [
        "# Taxonomy Mapping Proposal Summary",
        "",
        f"- Proposed tag rows: `{len(proposed_rows)}`",
        f"- Merge candidates: `{len(merge_rows)}`",
        "",
        "## Proposed Actions",
    ]
    for action, count in sorted(action_counts.items(), key=lambda item: item[0]):
        lines.append(f"- `{action}`: {count}")

    lines.extend(["", "## Confidence Levels"])
    for confidence, count in sorted(
        confidence_counts.items(), key=lambda item: item[0]
    ):
        lines.append(f"- `{confidence}`: {count}")

    lines.extend(["", "## Tag Surface Policy"])
    for policy, count in sorted(tag_surface_counts.items(), key=lambda item: item[0]):
        lines.append(f"- `{policy}`: {count}")

    lines.extend(
        [
            "",
            "## Generated Artifacts",
            "- `migration/taxonomy/tag_mapping_proposed.csv`",
            "- `migration/taxonomy/tag_merge_candidates.csv`",
        ]
    )

    PROPOSAL_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
