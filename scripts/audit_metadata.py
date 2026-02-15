#!/usr/bin/env python3
"""Audit markdown front matter used by the Pelican migration."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "migration" / "parity" / "metadata_audit_summary.md"
ISSUES_CSV_PATH = ROOT / "migration" / "parity" / "metadata_audit_issues.csv"

SUPPORTED_LAYOUTS = {"home", "index", "page", "search", "tag"}
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
EXTRA_AUDIT_FILES = ["index.md"]


@dataclass(frozen=True)
class Issue:
    kind: str
    path: str
    detail: str


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


def _normalize_layout(raw_value: Any) -> str:
    return str(raw_value).strip().lower()


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


def _write_issues_csv(issues: list[Issue]) -> None:
    ISSUES_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ISSUES_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("issue_kind", "path", "detail"))
        for issue in issues:
            writer.writerow((issue.kind, issue.path, issue.detail))


def _write_summary(
    markdown_files: list[Path],
    issues: list[Issue],
    layout_counts: Counter[str],
    key_counts: Counter[str],
) -> None:
    by_kind: dict[str, list[Issue]] = defaultdict(list)
    for issue in issues:
        by_kind[issue.kind].append(issue)

    lines: list[str] = [
        "# Metadata Audit Summary",
        "",
        f"- Markdown files audited: `{len(markdown_files)}`",
        f"- Distinct front matter keys: `{len(key_counts)}`",
        f"- Distinct layout values: `{len(layout_counts)}`",
        f"- Total issues: `{len(issues)}`",
        "",
        "## Layout Distribution",
    ]

    for layout, count in sorted(layout_counts.items()):
        lines.append(f"- `{layout}`: {count}")

    lines.extend(["", "## Issue Counts"])
    if not by_kind:
        lines.append("- None")
    else:
        for kind, kind_issues in sorted(by_kind.items()):
            lines.append(f"- `{kind}`: {len(kind_issues)}")

    lines.extend(["", "## Sample Issues"])
    if not issues:
        lines.append("- None")
    else:
        for kind in sorted(by_kind):
            sample = by_kind[kind][0]
            lines.append(f"- `{kind}`: `{sample.path}` ({sample.detail})")

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    markdown_files = _iter_markdown_files()
    issues: list[Issue] = []
    key_counts: Counter[str] = Counter()
    layout_counts: Counter[str] = Counter()

    for markdown_file in markdown_files:
        rel_path = markdown_file.relative_to(ROOT).as_posix()
        text = markdown_file.read_text(encoding="utf-8")
        raw_front_matter, front_matter_error = _extract_front_matter(text)
        if front_matter_error:
            issues.append(
                Issue(
                    kind=front_matter_error,
                    path=rel_path,
                    detail="front matter block missing or malformed",
                )
            )
            continue

        try:
            parsed = yaml.safe_load(raw_front_matter) or {}
        except yaml.YAMLError as exc:
            issues.append(
                Issue(
                    kind="front_matter_yaml_error",
                    path=rel_path,
                    detail=str(exc).splitlines()[0],
                )
            )
            continue

        if not isinstance(parsed, dict):
            issues.append(
                Issue(
                    kind="front_matter_not_mapping",
                    path=rel_path,
                    detail=f"type={type(parsed).__name__}",
                )
            )
            continue

        for key in parsed:
            key_counts[str(key)] += 1

        title = str(parsed.get("title", "")).strip()
        if not title:
            issues.append(
                Issue(
                    kind="missing_title",
                    path=rel_path,
                    detail="title is required for parity templates",
                )
            )

        layout = _normalize_layout(parsed.get("layout", ""))
        if not layout:
            issues.append(
                Issue(
                    kind="missing_layout",
                    path=rel_path,
                    detail="layout key is missing",
                )
            )
        else:
            layout_counts[layout] += 1
            if layout not in SUPPORTED_LAYOUTS:
                issues.append(
                    Issue(
                        kind="unsupported_layout",
                        path=rel_path,
                        detail=f"layout={layout}",
                    )
                )

        if "content" in parsed:
            issues.append(
                Issue(
                    kind="content_key_present",
                    path=rel_path,
                    detail="Pelican content property conflict risk",
                )
            )

        if "source_order" in parsed:
            raw_order = str(parsed["source_order"]).strip()
            try:
                int(raw_order)
            except (TypeError, ValueError):
                issues.append(
                    Issue(
                        kind="non_integer_source_order",
                        path=rel_path,
                        detail=f"source_order={raw_order}",
                    )
                )

        if "tags" in parsed:
            normalized_tags = _normalize_tags(parsed["tags"])
            raw_tags = str(parsed["tags"]).strip()
            if raw_tags and not normalized_tags:
                issues.append(
                    Issue(
                        kind="unparseable_tags",
                        path=rel_path,
                        detail=f"raw_tags={raw_tags}",
                    )
                )

    _write_issues_csv(issues)
    _write_summary(markdown_files, issues, layout_counts, key_counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
