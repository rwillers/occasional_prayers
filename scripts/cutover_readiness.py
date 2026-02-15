#!/usr/bin/env python3
"""Run cutover readiness checks for the Pelican + PageFind migration."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BUILD_DIR = ROOT / "_build_pelican"
BASELINE_URLS_PATH = ROOT / "migration" / "baseline" / "url_inventory.txt"
READINESS_REPORT = ROOT / "migration" / "cutover_readiness.md"

METADATA_ISSUES_PATH = ROOT / "migration" / "parity" / "metadata_audit_issues.csv"
PAGEFIND_ENTRY_PATH = ROOT / "_build_pelican" / "pagefind" / "pagefind-entry.json"
PAGEFIND_QUERY_RESULTS_PATH = (
    ROOT / "migration" / "parity" / "pagefind_query_results.tsv"
)
EXPECTED_EXTRA_URLS = {"/404.html"}
PYTHON_EXECUTABLE = sys.executable


@dataclass
class Check:
    name: str
    status: str
    detail: str


def _run_command(command: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    output = output.strip()
    return result.returncode == 0, output


def _check_build_output() -> Check:
    if not BUILD_DIR.exists():
        return Check("Build output", "FAIL", "_build_pelican does not exist")
    if not (BUILD_DIR / ".nojekyll").exists():
        return Check("Build output", "WARN", "_build_pelican/.nojekyll is missing")
    html_count = len(list(BUILD_DIR.rglob("*.html")))
    return Check("Build output", "PASS", f"_build_pelican has {html_count} HTML files")


def _check_url_parity() -> Check:
    if not BASELINE_URLS_PATH.exists():
        return Check("URL parity", "FAIL", "Baseline URL inventory is missing")
    if not BUILD_DIR.exists():
        return Check("URL parity", "FAIL", "_build_pelican is missing")

    baseline_urls = {
        line.strip()
        for line in BASELINE_URLS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    pelican_urls = {
        "/" + html_file.relative_to(BUILD_DIR).as_posix()
        for html_file in BUILD_DIR.rglob("*.html")
    }

    missing = sorted(baseline_urls - pelican_urls)
    extra = sorted(pelican_urls - baseline_urls)
    unexpected_extra = [url for url in extra if url not in EXPECTED_EXTRA_URLS]
    if missing or extra:
        if missing or unexpected_extra:
            detail = (
                f"missing={len(missing)}, "
                f"extra={len(extra)}, "
                f"unexpected_extra={len(unexpected_extra)}"
            )
            return Check("URL parity", "FAIL", detail)
        detail = (
            f"missing=0, extra={len(extra)} "
            f"(expected: {', '.join(sorted(EXPECTED_EXTRA_URLS))})"
        )
        return Check("URL parity", "PASS", detail)
    return Check("URL parity", "PASS", f"exact parity across {len(baseline_urls)} URLs")


def _check_redirect_validation() -> Check:
    command = [
        PYTHON_EXECUTABLE,
        "scripts/generate_redirects.py",
        "--csv",
        "migration/redirects.csv",
        "--site",
        "_build_pelican",
        "--report",
        "migration/redirect_report.txt",
    ]
    ok, output = _run_command(command)
    if ok:
        return Check(
            "Redirect validation", "PASS", "redirect generation/validation succeeded"
        )
    return Check("Redirect validation", "FAIL", output or "redirect validation failed")


def _check_metadata_audit() -> Check:
    command = [
        PYTHON_EXECUTABLE,
        "scripts/audit_metadata.py",
    ]
    ok, output = _run_command(command)
    if not ok:
        return Check("Metadata audit", "FAIL", output or "metadata audit failed")
    if not METADATA_ISSUES_PATH.exists():
        return Check("Metadata audit", "FAIL", "metadata_audit_issues.csv not found")

    issue_kinds: list[str] = []
    with METADATA_ISSUES_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            issue_kinds.append((row.get("issue_kind") or "").strip())

    unexpected = [
        kind for kind in issue_kinds if kind and kind != "content_key_present"
    ]
    if unexpected:
        return Check(
            "Metadata audit",
            "FAIL",
            f"unexpected metadata issues: {len(unexpected)}",
        )
    if issue_kinds:
        return Check(
            "Metadata audit",
            "WARN",
            "only known issue remains (index.md content key; handled by index-pelican.md)",
        )
    return Check("Metadata audit", "PASS", "no metadata issues found")


def _check_pagefind_assets() -> Check:
    pagefind_dir = BUILD_DIR / "pagefind"
    required_files = [
        pagefind_dir / "pagefind-entry.json",
        pagefind_dir / "pagefind-ui.js",
        pagefind_dir / "pagefind-ui.css",
        pagefind_dir / "pagefind.js",
    ]
    missing = [path.name for path in required_files if not path.exists()]
    if missing:
        return Check("PageFind assets", "FAIL", f"missing assets: {', '.join(missing)}")

    try:
        entry = json.loads(PAGEFIND_ENTRY_PATH.read_text(encoding="utf-8"))
        page_count = int(entry.get("languages", {}).get("en", {}).get("page_count", 0))
    except Exception as exc:
        return Check("PageFind assets", "FAIL", f"invalid pagefind-entry.json: {exc}")

    if page_count <= 0:
        return Check("PageFind assets", "FAIL", "pagefind page_count is zero")
    return Check("PageFind assets", "PASS", f"pagefind indexed pages={page_count}")


def _check_pagefind_queries() -> Check:
    if not PAGEFIND_QUERY_RESULTS_PATH.exists():
        return Check(
            "PageFind queries",
            "WARN",
            "query validation artifact missing (migration/parity/pagefind_query_results.tsv)",
        )

    rows: list[dict[str, str]] = []
    with PAGEFIND_QUERY_RESULTS_PATH.open("r", encoding="utf-8") as handle:
        header = handle.readline().strip().split("\t")
        for line in handle:
            values = line.strip().split("\t")
            if len(values) != len(header):
                continue
            rows.append(dict(zip(header, values)))

    if not rows:
        return Check(
            "PageFind queries", "WARN", "no query rows found in validation artifact"
        )

    zero_count_terms = [
        row.get("term", "") for row in rows if int(row.get("result_count", "0")) == 0
    ]
    tag_topped = [
        row.get("term", "") for row in rows if "/tag/" in row.get("top_result_url", "")
    ]

    if zero_count_terms:
        return Check(
            "PageFind queries",
            "FAIL",
            f"zero-result representative terms: {', '.join(zero_count_terms)}",
        )
    if len(tag_topped) >= max(3, len(rows) // 2):
        detail = (
            "top results skew to tag pages for many terms "
            f"({len(tag_topped)}/{len(rows)}); verify relevance manually"
        )
        return Check("PageFind queries", "WARN", detail)
    return Check(
        "PageFind queries", "PASS", "representative terms return non-zero results"
    )


def _manual_tasks_section() -> list[str]:
    return [
        "## Manual Cutover Tasks",
        "- Freeze content changes during final switch window.",
        "- Run final `make build-pelican-search` in a network-enabled environment.",
        "- Run post-deploy smoke checks: home, section pages, tag pages, search, and 404.",
        "",
        "## Manual Search QA Focus",
        "- Compare search result ordering for representative terms against current production behavior.",
        "- Verify search UX on mobile and desktop (input behavior, result rendering, keyboard navigation).",
        "- Check whether tag pages over-dominate results and tune indexing rules if needed.",
    ]


def main() -> int:
    checks = [
        _check_build_output(),
        _check_url_parity(),
        _check_redirect_validation(),
        _check_metadata_audit(),
        _check_pagefind_assets(),
        _check_pagefind_queries(),
    ]

    fail_count = sum(1 for check in checks if check.status == "FAIL")
    warn_count = sum(1 for check in checks if check.status == "WARN")

    lines: list[str] = [
        "# Cutover Readiness Report",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- FAIL checks: `{fail_count}`",
        f"- WARN checks: `{warn_count}`",
        "",
        "## Automated Checks",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {check.detail} |")

    lines.extend(["", *_manual_tasks_section(), ""])
    READINESS_REPORT.parent.mkdir(parents=True, exist_ok=True)
    READINESS_REPORT.write_text("\n".join(lines), encoding="utf-8")

    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
