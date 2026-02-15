#!/usr/bin/env python3
"""Finalize taxonomy mappings from approved proposal + merge decisions."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_DIR = ROOT / "migration" / "taxonomy"

PROPOSED_PATH = TAXONOMY_DIR / "tag_mapping_proposed.csv"
MERGE_DECISIONS_PATH = TAXONOMY_DIR / "tag_merge_candidates.csv"

FINAL_MAPPING_PATH = TAXONOMY_DIR / "tag_mapping_final.csv"
MERGE_REDIRECTS_PATH = TAXONOMY_DIR / "tag_redirect_from_merges.csv"
FINALIZATION_SUMMARY_PATH = TAXONOMY_DIR / "finalization_summary.md"


@dataclass(frozen=True)
class MergeDecision:
    tag_a: str
    tag_b: str
    canonical: str
    decision: str


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_merge_decisions(path: Path) -> list[MergeDecision]:
    decisions: list[MergeDecision] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            decisions.append(
                MergeDecision(
                    tag_a=row["tag_a"].strip(),
                    tag_b=row["tag_b"].strip(),
                    canonical=row["proposed_canonical"].strip(),
                    decision=row["review_decision"].strip().lower(),
                )
            )
    return decisions


def _write_csv(
    path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _tag_segment(tag_name: str) -> str:
    return tag_name.replace("/", "%2F")


def _merge_note(existing: str, note: str) -> str:
    existing = existing.strip()
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing}; {note}"


def main() -> int:
    proposed_rows = _read_rows(PROPOSED_PATH)
    merge_decisions = _read_merge_decisions(MERGE_DECISIONS_PATH)
    by_raw = {row["raw_value"]: row for row in proposed_rows}

    missing_tags: list[str] = []
    redirects: list[dict[str, str]] = []
    applied_merges = 0
    unchanged_merges = 0

    for decision in merge_decisions:
        if decision.decision != "merge":
            continue
        applied_merges += 1
        for tag_name in (decision.tag_a, decision.tag_b):
            if tag_name not in by_raw:
                missing_tags.append(tag_name)
                continue

        canonical_row = by_raw.get(decision.canonical)
        if canonical_row is None:
            missing_tags.append(decision.canonical)
            continue
        canonical_facet = canonical_row["reviewed_facet"]

        for tag_name in (decision.tag_a, decision.tag_b):
            row = by_raw.get(tag_name)
            if row is None:
                continue

            old_canonical = row["canonical_value"]
            row["canonical_value"] = decision.canonical

            if tag_name == decision.canonical:
                row["review_notes"] = _merge_note(
                    row.get("review_notes", ""),
                    f"merge canonical retained ({decision.tag_a} <-> {decision.tag_b})",
                )
                continue

            unchanged_merges += 1
            row["reviewed_action"] = "merge"
            row["reviewed_facet"] = canonical_facet
            row["tag_surface_policy"] = "remove_from_tags"
            row["confidence"] = "high"
            row["rationale"] = "approved_merge_alias_to_canonical"
            row["review_notes"] = _merge_note(
                row.get("review_notes", ""),
                f"approved merge alias: {tag_name} -> {decision.canonical}",
            )
            if old_canonical != decision.canonical:
                redirects.append(
                    {
                        "old_tag": tag_name,
                        "new_tag": decision.canonical,
                        "old_path": f"/tag/{_tag_segment(tag_name)}/",
                        "new_path": f"/tag/{_tag_segment(decision.canonical)}/",
                        "status": "301",
                        "note": "approved merge alias redirect",
                    }
                )

    final_rows = sorted(proposed_rows, key=lambda row: row["raw_value"].casefold())
    _write_csv(
        FINAL_MAPPING_PATH,
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
        final_rows,
    )
    _write_csv(
        MERGE_REDIRECTS_PATH,
        ("old_tag", "new_tag", "old_path", "new_path", "status", "note"),
        redirects,
    )

    action_counts: dict[str, int] = {}
    for row in final_rows:
        action = row["reviewed_action"]
        action_counts[action] = action_counts.get(action, 0) + 1

    lines = [
        "# Taxonomy Finalization Summary",
        "",
        f"- Proposed rows read: `{len(proposed_rows)}`",
        f"- Merge decisions applied: `{applied_merges}`",
        f"- Alias rows converted to `merge`: `{unchanged_merges}`",
        f"- Merge redirects generated: `{len(redirects)}`",
        "",
        "## Final Action Counts",
    ]
    for action, count in sorted(action_counts.items(), key=lambda item: item[0]):
        lines.append(f"- `{action}`: {count}")
    if missing_tags:
        lines.extend(["", "## Missing Tags"])
        for tag_name in sorted(set(missing_tags), key=str.casefold):
            lines.append(f"- `{tag_name}`")

    FINALIZATION_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
