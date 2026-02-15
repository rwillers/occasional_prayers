from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

from tests.module_loader import load_script_module


generate_redirects = load_script_module("generate_redirects")


def test_detect_cycles_finds_loop() -> None:
    mapping = {
        "/a": "/b",
        "/b": "/a",
    }
    cycles = generate_redirects._detect_cycles(mapping)
    assert cycles


def test_validate_rules_catches_duplicate_status_and_missing_target(
    tmp_path: Path,
) -> None:
    site_dir = tmp_path / "site"
    site_dir.mkdir(parents=True)
    (site_dir / "target.html").write_text("ok", encoding="utf-8")

    rules = [
        generate_redirects.RedirectRule(
            old_path="/old.html",
            new_path="/target.html",
            status="301",
            note="",
        ),
        generate_redirects.RedirectRule(
            old_path="/old.html",
            new_path="/missing.html",
            status="307",
            note="",
        ),
    ]
    errors = generate_redirects._validate_rules(rules, site_dir)
    assert any("duplicate old_path" in error for error in errors)
    assert any("unsupported status" in error for error in errors)
    assert any("new_path '/missing.html' not found" in error for error in errors)


def test_cli_generates_redirect_html_and_report(tmp_path: Path) -> None:
    site_dir = tmp_path / "site"
    site_dir.mkdir(parents=True)
    (site_dir / "target.html").write_text("target", encoding="utf-8")

    csv_path = tmp_path / "redirects.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["old_path", "new_path", "status", "note"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "old_path": "/old.html",
                "new_path": "/target.html",
                "status": "301",
                "note": "test",
            }
        )

    report_path = tmp_path / "report.txt"
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "generate_redirects.py"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--csv",
            str(csv_path),
            "--site",
            str(site_dir),
            "--report",
            str(report_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    output_file = site_dir / "old.html"
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert 'meta http-equiv="refresh"' in content
    assert "/target.html" in content
    assert report_path.exists()
    assert "Redirect generation succeeded." in report_path.read_text(encoding="utf-8")
