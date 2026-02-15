#!/usr/bin/env python3
"""Generate static HTML redirect pages from a CSV mapping file."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

DEFAULT_CSV = Path("migration/redirects.csv")
DEFAULT_SITE = Path("_build_pelican")
DEFAULT_REPORT = Path("migration/redirect_report.txt")


@dataclass(frozen=True)
class RedirectRule:
    old_path: str
    new_path: str
    status: str
    note: str


def _normalize_web_path(path: str) -> str:
    value = (path or "").strip()
    if not value:
        return ""
    if not value.startswith("/"):
        value = f"/{value}"
    if value != "/" and value.endswith("/") and len(value) > 1:
        return value
    return value


def _candidate_paths(site_dir: Path, web_path: str) -> list[Path]:
    clean = web_path.lstrip("/")
    if not clean:
        return [site_dir / "index.html"]

    candidates = [site_dir / clean]
    if clean.endswith("/"):
        candidates.append(site_dir / clean / "index.html")
        return candidates

    if not clean.endswith(".html"):
        candidates.append(site_dir / f"{clean}.html")
        candidates.append(site_dir / clean / "index.html")
    return candidates


def _output_file_for_old_path(site_dir: Path, old_path: str) -> Path:
    clean = old_path.lstrip("/")
    if not clean:
        return site_dir / "index.html"
    if old_path.endswith("/"):
        return site_dir / clean / "index.html"
    return site_dir / clean


def _read_redirect_rules(csv_path: Path) -> list[RedirectRule]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"old_path", "new_path", "status", "note"}
        missing = required.difference(reader.fieldnames or set())
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"redirect CSV missing required columns: {missing_text}")

        rules: list[RedirectRule] = []
        for row in reader:
            old_path = _normalize_web_path(row.get("old_path", ""))
            new_path = _normalize_web_path(row.get("new_path", ""))
            status = (row.get("status", "") or "301").strip() or "301"
            note = (row.get("note", "") or "").strip()

            if not old_path and not new_path and not note:
                continue

            rules.append(
                RedirectRule(
                    old_path=old_path,
                    new_path=new_path,
                    status=status,
                    note=note,
                )
            )
    return rules


def _detect_cycles(mapping: dict[str, str]) -> list[list[str]]:
    cycles: list[list[str]] = []
    seen_cycle_keys: set[tuple[str, ...]] = set()

    for start in mapping:
        current = start
        traversal: list[str] = []
        visited_at: dict[str, int] = {}
        while current in mapping:
            if current in visited_at:
                cycle = traversal[visited_at[current] :] + [current]
                cycle_key = tuple(cycle)
                if cycle_key not in seen_cycle_keys:
                    seen_cycle_keys.add(cycle_key)
                    cycles.append(cycle)
                break
            visited_at[current] = len(traversal)
            traversal.append(current)
            current = mapping[current]
    return cycles


def _validate_rules(rules: list[RedirectRule], site_dir: Path) -> list[str]:
    errors: list[str] = []
    seen_old_paths: dict[str, int] = {}
    mapping: dict[str, str] = {}

    for row_number, rule in enumerate(rules, start=2):
        if not rule.old_path:
            errors.append(f"row {row_number}: old_path is required")
            continue
        if not rule.new_path:
            errors.append(f"row {row_number}: new_path is required")
            continue
        if not rule.old_path.startswith("/"):
            errors.append(f"row {row_number}: old_path must start with '/'")
        if not rule.new_path.startswith("/"):
            errors.append(f"row {row_number}: new_path must start with '/'")
        if rule.status not in {"301", "302"}:
            errors.append(
                f"row {row_number}: unsupported status '{rule.status}' (expected 301 or 302)"
            )

        if rule.old_path in seen_old_paths:
            first_row = seen_old_paths[rule.old_path]
            errors.append(
                f"row {row_number}: duplicate old_path '{rule.old_path}' (first at row {first_row})"
            )
        else:
            seen_old_paths[rule.old_path] = row_number

        mapping[rule.old_path] = rule.new_path

    for cycle in _detect_cycles(mapping):
        cycle_text = " -> ".join(cycle)
        errors.append(f"redirect loop detected: {cycle_text}")

    for row_number, rule in enumerate(rules, start=2):
        if not rule.new_path:
            continue
        candidates = _candidate_paths(site_dir, rule.new_path)
        if any(path.exists() for path in candidates):
            continue
        rendered = ", ".join(
            path.relative_to(site_dir).as_posix() for path in candidates
        )
        errors.append(
            f"row {row_number}: new_path '{rule.new_path}' not found in build output (checked: {rendered})"
        )

    return errors


def _render_redirect_html(target_path: str) -> str:
    escaped_target = json.dumps(target_path)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "  <head>",
            '    <meta charset="utf-8">',
            "    <title>Redirecting...</title>",
            f'    <link rel="canonical" href="{target_path}">',
            '    <meta name="robots" content="noindex, nofollow">',
            f'    <meta http-equiv="refresh" content="0; url={target_path}">',
            "  </head>",
            '  <body data-pagefind-ignore="all">',
            f'    <p>Redirecting to <a href="{target_path}">{target_path}</a>.</p>',
            f"    <script>window.location.replace({escaped_target});</script>",
            "  </body>",
            "</html>",
            "",
        ]
    )


def _write_report(report_path: Path, lines: list[str]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", dest="csv_path", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--site", dest="site_dir", type=Path, default=DEFAULT_SITE)
    parser.add_argument(
        "--report",
        dest="report_path",
        type=Path,
        default=DEFAULT_REPORT,
    )
    args = parser.parse_args()

    csv_path = args.csv_path
    site_dir = args.site_dir
    report_path = args.report_path

    if not csv_path.exists():
        _write_report(report_path, [f"ERROR: redirect mapping not found: {csv_path}"])
        return 1
    if not site_dir.exists():
        _write_report(report_path, [f"ERROR: build output not found: {site_dir}"])
        return 1

    try:
        rules = _read_redirect_rules(csv_path)
    except ValueError as exc:
        _write_report(report_path, [f"ERROR: {exc}"])
        return 1

    errors = _validate_rules(rules, site_dir)
    if errors:
        report_lines = [
            "Redirect generation failed.",
            f"Rules evaluated: {len(rules)}",
            f"Invalid entries: {len(errors)}",
            "",
            "Validation errors:",
        ]
        report_lines.extend(f"- {error}" for error in errors)
        _write_report(report_path, report_lines)
        return 1

    generated_count = 0
    for rule in rules:
        output_path = _output_file_for_old_path(site_dir, rule.old_path)
        normalized = PurePosixPath(output_path.relative_to(site_dir).as_posix())
        if ".." in normalized.parts:
            raise ValueError(f"unsafe redirect output path: {rule.old_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            _render_redirect_html(rule.new_path),
            encoding="utf-8",
        )
        generated_count += 1

    _write_report(
        report_path,
        [
            "Redirect generation succeeded.",
            f"Rules evaluated: {len(rules)}",
            f"Redirects generated: {generated_count}",
            "Invalid entries: 0",
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
