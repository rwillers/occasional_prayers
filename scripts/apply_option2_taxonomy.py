#!/usr/bin/env python3
"""Apply Option 2 final taxonomy mapping to markdown tags in-place."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = ROOT / "migration" / "taxonomy" / "extreme" / "option2_final_mapping.csv"
REPORT_PATH = ROOT / "migration" / "taxonomy" / "extreme" / "option2_apply_report.csv"
SUMMARY_PATH = ROOT / "migration" / "taxonomy" / "extreme" / "option2_apply_summary.md"

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


@dataclass(frozen=True)
class TagDecision:
    action: str
    target: str


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


def _read_mapping(path: Path) -> dict[str, TagDecision]:
    mapping: dict[str, TagDecision] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            raw_tag = row["raw_tag"].strip()
            action = row["extreme_action"].strip().lower()
            target = row["extreme_tag"].strip()
            mapping[raw_tag] = TagDecision(action=action, target=target)
    return mapping


def _render_tags_line(tags: list[str]) -> str:
    rendered_tags = yaml.safe_dump(
        tags,
        default_flow_style=True,
        allow_unicode=True,
        sort_keys=False,
        width=10_000,
    ).strip()
    return f"tags: {rendered_tags}"


def _replace_tags_line(text: str, new_tags: list[str]) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text

    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return text

    tags_line = _render_tags_line(new_tags)
    tags_index: int | None = None
    tags_pattern = re.compile(r"^\s*tags\s*:")
    for index in range(1, end_index):
        if tags_pattern.match(lines[index]):
            tags_index = index
            break

    if tags_index is not None:
        lines[tags_index] = tags_line
    else:
        lines.insert(end_index, tags_line)

    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _map_tags(
    original_tags: list[str], mapping: dict[str, TagDecision]
) -> tuple[list[str], list[str], list[str], list[str]]:
    mapped: list[str] = []
    dropped: list[str] = []
    remapped: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()

    for tag_name in original_tags:
        decision = mapping.get(tag_name)
        if decision is None:
            missing.append(tag_name)
            continue

        if decision.action == "drop":
            dropped.append(tag_name)
            continue

        target = decision.target or tag_name
        if decision.action == "map" and target != tag_name:
            remapped.append(f"{tag_name} -> {target}")
        if target not in seen:
            seen.add(target)
            mapped.append(target)

    return mapped, dropped, remapped, missing


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
    mapping = _read_mapping(MAPPING_PATH)
    markdown_files = _iter_markdown_files()

    report_rows: list[dict[str, str]] = []
    changed_files = 0
    unchanged_files = 0
    files_with_tags = 0
    files_without_tags = 0
    missing_mapping_tags: set[str] = set()
    total_original_tags = 0
    total_new_tags = 0
    total_dropped_tags = 0

    for markdown_file in markdown_files:
        rel_path = markdown_file.relative_to(ROOT).as_posix()
        text = markdown_file.read_text(encoding="utf-8")
        raw_front_matter, front_matter_error = _extract_front_matter(text)
        if front_matter_error:
            continue

        try:
            parsed = yaml.safe_load(raw_front_matter) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(parsed, dict):
            continue

        original_tags = _normalize_tags(parsed.get("tags"))
        if not original_tags:
            files_without_tags += 1
            continue
        files_with_tags += 1

        new_tags, dropped, remapped, missing = _map_tags(original_tags, mapping)
        total_original_tags += len(original_tags)
        total_new_tags += len(new_tags)
        total_dropped_tags += len(dropped)
        if missing:
            missing_mapping_tags.update(missing)

        new_text = _replace_tags_line(text, new_tags)
        changed = new_text != text
        if changed:
            markdown_file.write_text(new_text, encoding="utf-8")
            changed_files += 1
        else:
            unchanged_files += 1

        report_rows.append(
            {
                "path": rel_path,
                "original_tag_count": str(len(original_tags)),
                "new_tag_count": str(len(new_tags)),
                "changed": "yes" if changed else "no",
                "dropped_tags": " | ".join(dropped),
                "remapped_tags": " | ".join(remapped),
                "missing_mapping_tags": " | ".join(missing),
                "new_tags": " | ".join(new_tags),
            }
        )

    report_rows.sort(key=lambda row: row["path"].casefold())
    _write_csv(
        REPORT_PATH,
        (
            "path",
            "original_tag_count",
            "new_tag_count",
            "changed",
            "dropped_tags",
            "remapped_tags",
            "missing_mapping_tags",
            "new_tags",
        ),
        report_rows,
    )

    lines = [
        "# Option2 Apply Summary",
        "",
        f"- Markdown files scanned: `{len(markdown_files)}`",
        f"- Files with tags processed: `{files_with_tags}`",
        f"- Files without tags: `{files_without_tags}`",
        f"- Files changed: `{changed_files}`",
        f"- Files unchanged: `{unchanged_files}`",
        f"- Total original tag assignments: `{total_original_tags}`",
        f"- Total new tag assignments: `{total_new_tags}`",
        f"- Total dropped tag assignments: `{total_dropped_tags}`",
        f"- Missing mapping tags encountered: `{len(missing_mapping_tags)}`",
        "",
        "## Artifacts",
        "- `migration/taxonomy/extreme/option2_apply_report.csv`",
    ]
    if missing_mapping_tags:
        lines.extend(["", "## Missing Mapping Tags"])
        for tag_name in sorted(missing_mapping_tags, key=str.casefold):
            lines.append(f"- `{tag_name}`")

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
