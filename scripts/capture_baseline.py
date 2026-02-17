#!/usr/bin/env python3
"""Capture baseline artifacts from the current Urubu output."""

from __future__ import annotations

import csv
import datetime as dt
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "_build"
OUTPUT_DIR = ROOT / "migration" / "baseline"

IGNORE_BUILD_PREFIXES = ("venv/",)
IGNORE_MD_PREFIXES = ("_build/", "_workingfiles/", "migration/", "venv/")
IGNORE_MD_FILES = {"AGENTS.md", "README.md", "TODO.md"}

FRONT_MATTER_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*:")


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[tuple[str, ...]], header: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def normalize_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def collect_urls(build_dir: Path) -> list[str]:
    urls: list[str] = []
    for html_file in sorted(build_dir.rglob("*.html")):
        rel_path = normalize_path(html_file, build_dir)
        if rel_path.startswith(IGNORE_BUILD_PREFIXES):
            continue
        urls.append(f"/{rel_path}")
    return urls


def collect_section_dirs() -> list[str]:
    sections: list[str] = []
    for index_md in sorted(ROOT.glob("*/index.md")):
        section = normalize_path(index_md.parent, ROOT)
        if section.startswith("_"):
            continue
        if section in {"venv", "_build", "_workingfiles"}:
            continue
        sections.append(section)
    return sections


def collect_representative_urls(
    urls: list[str], sections: list[str]
) -> list[tuple[str, str, str]]:
    url_set = set(urls)
    samples: list[tuple[str, str, str]] = []

    root_samples = [
        ("/index.html", "root home"),
        ("/search.html", "search page"),
        ("/about.html", "about page"),
        ("/tag/index.html", "tag index"),
        ("/notfound.html", "not found page"),
    ]
    for url, reason in root_samples:
        if url in url_set:
            samples.append(("root", url, reason))

    for section in sections:
        section_urls = sorted(
            url
            for url in urls
            if url.startswith(f"/{section}/") and url.endswith(".html")
        )
        if not section_urls:
            continue
        index_url = f"/{section}/index.html"
        if index_url in url_set:
            samples.append((section, index_url, "section index"))
        first_page = next(
            (url for url in section_urls if not url.endswith("/index.html")), ""
        )
        if first_page:
            samples.append((section, first_page, "first content page"))

    return samples


def extract_front_matter_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index]
    return []


def clean_value(raw: str) -> str:
    value = raw.strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    return value


def collect_metadata() -> tuple[Counter[str], Counter[str], list[str], list[str]]:
    key_counts: Counter[str] = Counter()
    layout_counts: Counter[str] = Counter()
    missing_front_matter: list[str] = []
    markdown_files: list[str] = []

    for markdown_file in sorted(ROOT.rglob("*.md")):
        rel_path = normalize_path(markdown_file, ROOT)
        if rel_path.startswith(IGNORE_MD_PREFIXES):
            continue
        if rel_path in IGNORE_MD_FILES:
            continue

        markdown_files.append(rel_path)
        text = markdown_file.read_text(encoding="utf-8")
        front_matter_lines = extract_front_matter_lines(text)
        if not front_matter_lines:
            missing_front_matter.append(rel_path)
            continue

        for line in front_matter_lines:
            key_match = FRONT_MATTER_KEY_RE.match(line.strip())
            if not key_match:
                continue
            key = key_match.group(1)
            key_counts[key] += 1

            if key != "layout":
                continue
            _, raw_value = line.split(":", 1)
            layout = clean_value(raw_value)
            if layout:
                layout_counts[layout] += 1

    return key_counts, layout_counts, missing_front_matter, markdown_files


def collect_tipue_assets() -> tuple[list[str], list[str]]:
    source_assets: list[str] = []
    build_assets: list[str] = []

    source_dir = ROOT / "tipuesearch"
    if source_dir.exists():
        for source_file in sorted(source_dir.rglob("*")):
            if source_file.is_file():
                source_assets.append(normalize_path(source_file, ROOT))

    build_dir = BUILD_DIR / "tipuesearch"
    if build_dir.exists():
        for build_file in sorted(build_dir.rglob("*")):
            if build_file.is_file():
                build_assets.append(normalize_path(build_file, BUILD_DIR))

    return source_assets, build_assets


def collect_templates() -> list[str]:
    template_dir = ROOT / "_layouts"
    if not template_dir.exists():
        return []
    return [
        normalize_path(template_file, ROOT)
        for template_file in sorted(template_dir.rglob("*.html"))
    ]


def write_summary(
    output_dir: Path,
    urls: list[str],
    sections: list[str],
    markdown_files: list[str],
    key_counts: Counter[str],
    layout_counts: Counter[str],
) -> None:
    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    top_level_counts: Counter[str] = Counter()
    for url in urls:
        parts = url.lstrip("/").split("/")
        top_level = parts[0] if len(parts) > 1 else "(root)"
        top_level_counts[top_level] += 1

    lines = [
        "# Baseline Summary",
        "",
        f"- Captured: `{timestamp}`",
        f"- Total HTML URLs: `{len(urls)}`",
        f"- Total Markdown source files (in scope): `{len(markdown_files)}`",
        f"- Sections with `index.md`: `{len(sections)}`",
        f"- Distinct front matter keys: `{len(key_counts)}`",
        f"- Distinct layout values: `{len(layout_counts)}`",
        "",
        "## Top-level URL counts",
    ]
    for name, count in sorted(top_level_counts.items()):
        lines.append(f"- `{name}`: {count}")

    write_lines(output_dir / "baseline_summary.md", lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    urls = collect_urls(BUILD_DIR)
    write_lines(OUTPUT_DIR / "url_inventory.txt", urls)

    top_level_rows: list[tuple[str, str]] = []
    top_level_counts: Counter[str] = Counter()
    for url in urls:
        parts = url.lstrip("/").split("/")
        top_level = parts[0] if len(parts) > 1 else "(root)"
        top_level_counts[top_level] += 1
    for section, count in sorted(top_level_counts.items()):
        top_level_rows.append((section, str(count)))
    write_csv(
        OUTPUT_DIR / "url_inventory_by_top_level.csv",
        top_level_rows,
        ("top_level", "url_count"),
    )

    sections = collect_section_dirs()
    reps = collect_representative_urls(urls, sections)
    write_csv(
        OUTPUT_DIR / "representative_urls.csv",
        reps,
        ("sample_group", "url_path", "reason"),
    )

    key_counts, layout_counts, missing_front_matter, markdown_files = collect_metadata()
    write_csv(
        OUTPUT_DIR / "metadata_key_counts.csv",
        [(key, str(count)) for key, count in key_counts.most_common()],
        ("metadata_key", "file_count"),
    )
    write_csv(
        OUTPUT_DIR / "layout_usage.csv",
        [(layout, str(count)) for layout, count in layout_counts.most_common()],
        ("layout", "file_count"),
    )
    write_lines(OUTPUT_DIR / "front_matter_missing.txt", sorted(missing_front_matter))

    source_tipue, build_tipue = collect_tipue_assets()
    write_lines(OUTPUT_DIR / "tipuesearch_source_assets.txt", source_tipue)
    write_lines(OUTPUT_DIR / "tipuesearch_build_assets.txt", build_tipue)

    templates = collect_templates()
    write_lines(OUTPUT_DIR / "urubu_layout_templates.txt", templates)

    write_summary(OUTPUT_DIR, urls, sections, markdown_files, key_counts, layout_counts)


if __name__ == "__main__":
    main()
