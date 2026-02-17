#!/usr/bin/env python3
"""Check representative render parity between Urubu and Pelican output."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "_build"
PELICAN_DIR = ROOT / "_build_pelican"
REPRESENTATIVE_CSV = ROOT / "migration" / "baseline" / "representative_urls.csv"
SUMMARY_PATH = ROOT / "migration" / "parity" / "render_parity_summary.md"
DETAILS_CSV_PATH = ROOT / "migration" / "parity" / "render_parity_details.csv"

EXPECTED_DEVIATION_URLS = {"/search.html"}


@dataclass(frozen=True)
class CheckResult:
    url: str
    exists_in_baseline: bool
    exists_in_pelican: bool
    title_match: bool
    h2_match: bool
    breadcrumb_match: bool
    tags_block_match: bool
    token_similarity: float
    expected_deviation: bool


def _extract(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return " ".join(unescape(match.group(1)).split())


def _clean_html_for_text_similarity(text: str) -> str:
    text = re.sub(
        r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(
        r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return " ".join(text.split())


def _token_similarity(baseline_text: str, pelican_text: str) -> float:
    baseline_tokens = set(re.findall(r"[A-Za-z0-9']+", baseline_text.lower()))
    pelican_tokens = set(re.findall(r"[A-Za-z0-9']+", pelican_text.lower()))
    union = baseline_tokens | pelican_tokens
    if not union:
        return 1.0
    return len(baseline_tokens & pelican_tokens) / len(union)


def _load_representative_urls() -> list[str]:
    urls: list[str] = []
    with REPRESENTATIVE_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            url = (row.get("url_path") or "").strip()
            if url and url not in urls:
                urls.append(url)
    return urls


def _check_url(url: str) -> CheckResult:
    rel_path = url.lstrip("/")
    baseline_path = BASELINE_DIR / rel_path
    pelican_path = PELICAN_DIR / rel_path

    exists_in_baseline = baseline_path.exists()
    exists_in_pelican = pelican_path.exists()
    if not (exists_in_baseline and exists_in_pelican):
        return CheckResult(
            url=url,
            exists_in_baseline=exists_in_baseline,
            exists_in_pelican=exists_in_pelican,
            title_match=False,
            h2_match=False,
            breadcrumb_match=False,
            tags_block_match=False,
            token_similarity=0.0,
            expected_deviation=url in EXPECTED_DEVIATION_URLS,
        )

    baseline_html = baseline_path.read_text(encoding="utf-8")
    pelican_html = pelican_path.read_text(encoding="utf-8")

    baseline_title = _extract(r"<title>(.*?)</title>", baseline_html)
    pelican_title = _extract(r"<title>(.*?)</title>", pelican_html)
    title_match = baseline_title == pelican_title

    baseline_h2 = _extract(r"<h2[^>]*>(.*?)</h2>", baseline_html)
    pelican_h2 = _extract(r"<h2[^>]*>(.*?)</h2>", pelican_html)
    h2_match = baseline_h2 == pelican_h2

    baseline_breadcrumb = 'class="breadcrumb"' in baseline_html
    pelican_breadcrumb = 'class="breadcrumb"' in pelican_html
    breadcrumb_match = baseline_breadcrumb == pelican_breadcrumb

    baseline_tags = 'class="tags"' in baseline_html
    pelican_tags = 'class="tags"' in pelican_html
    tags_block_match = baseline_tags == pelican_tags

    baseline_text = _clean_html_for_text_similarity(baseline_html)
    pelican_text = _clean_html_for_text_similarity(pelican_html)
    similarity = _token_similarity(baseline_text, pelican_text)

    return CheckResult(
        url=url,
        exists_in_baseline=exists_in_baseline,
        exists_in_pelican=exists_in_pelican,
        title_match=title_match,
        h2_match=h2_match,
        breadcrumb_match=breadcrumb_match,
        tags_block_match=tags_block_match,
        token_similarity=similarity,
        expected_deviation=url in EXPECTED_DEVIATION_URLS,
    )


def _write_details(results: list[CheckResult]) -> None:
    DETAILS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DETAILS_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "url",
                "exists_in_baseline",
                "exists_in_pelican",
                "title_match",
                "h2_match",
                "breadcrumb_match",
                "tags_block_match",
                "token_similarity",
                "expected_deviation",
            )
        )
        for result in results:
            writer.writerow(
                (
                    result.url,
                    result.exists_in_baseline,
                    result.exists_in_pelican,
                    result.title_match,
                    result.h2_match,
                    result.breadcrumb_match,
                    result.tags_block_match,
                    f"{result.token_similarity:.4f}",
                    result.expected_deviation,
                )
            )


def _write_summary(results: list[CheckResult]) -> None:
    comparable = [
        result
        for result in results
        if result.exists_in_baseline and result.exists_in_pelican
    ]
    strict_failures = [
        result
        for result in comparable
        if not result.expected_deviation
        and (
            not result.title_match
            or not result.h2_match
            or not result.breadcrumb_match
            or not result.tags_block_match
            or result.token_similarity < 0.90
        )
    ]
    expected_deviations = [result for result in comparable if result.expected_deviation]
    missing_files = [
        result
        for result in results
        if not (result.exists_in_baseline and result.exists_in_pelican)
    ]

    avg_similarity = (
        sum(item.token_similarity for item in comparable) / len(comparable)
        if comparable
        else 0.0
    )

    lines: list[str] = [
        "# Render Parity Summary",
        "",
        f"- URLs checked: `{len(results)}`",
        f"- Comparable URLs: `{len(comparable)}`",
        f"- Missing file pairs: `{len(missing_files)}`",
        f"- Strict parity failures: `{len(strict_failures)}`",
        f"- Expected deviations: `{len(expected_deviations)}`",
        f"- Average token similarity: `{avg_similarity:.4f}`",
        "",
        "## Notes",
        "- `/search.html` is treated as an expected deviation because search implementation changed from Tipue to PageFind.",
    ]

    if strict_failures:
        lines.extend(["", "## Strict Failure Samples"])
        for item in strict_failures[:10]:
            lines.append(
                f"- `{item.url}` (similarity `{item.token_similarity:.4f}`, title={item.title_match}, h2={item.h2_match}, breadcrumb={item.breadcrumb_match}, tags={item.tags_block_match})"
            )

    if missing_files:
        lines.extend(["", "## Missing File Samples"])
        for item in missing_files[:10]:
            lines.append(
                f"- `{item.url}` (baseline={item.exists_in_baseline}, pelican={item.exists_in_pelican})"
            )

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    urls = _load_representative_urls()
    results = [_check_url(url) for url in urls]
    _write_details(results)
    _write_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
