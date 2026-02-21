from __future__ import annotations

from pathlib import Path

from tests.module_loader import load_script_module


cutover_readiness = load_script_module("cutover_readiness")


def test_manual_tasks_no_urubu_reference() -> None:
    tasks_text = "\n".join(cutover_readiness._manual_tasks_section()).lower()
    assert "urubu" not in tasks_text


def test_url_parity_passes_with_expected_extra(tmp_path: Path, monkeypatch) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True)
    (build_dir / "index.html").write_text("ok", encoding="utf-8")
    (build_dir / "404.html").write_text("not found", encoding="utf-8")

    baseline = tmp_path / "baseline.txt"
    baseline.write_text("/index.html\n", encoding="utf-8")

    monkeypatch.setattr(cutover_readiness, "BUILD_DIR", build_dir)
    monkeypatch.setattr(cutover_readiness, "BASELINE_URLS_PATH", baseline)
    result = cutover_readiness._check_url_parity()
    assert result.status == "PASS"


def test_url_parity_passes_with_expected_extra_prefix(
    tmp_path: Path, monkeypatch
) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True)
    (build_dir / "index.html").write_text("ok", encoding="utf-8")
    nested = build_dir / "coe1559"
    nested.mkdir(parents=True)
    (nested / "1.html").write_text("x", encoding="utf-8")

    baseline = tmp_path / "baseline.txt"
    baseline.write_text("/index.html\n", encoding="utf-8")

    monkeypatch.setattr(cutover_readiness, "BUILD_DIR", build_dir)
    monkeypatch.setattr(cutover_readiness, "BASELINE_URLS_PATH", baseline)
    result = cutover_readiness._check_url_parity()
    assert result.status == "PASS"


def test_url_parity_fails_with_unexpected_extra(tmp_path: Path, monkeypatch) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True)
    (build_dir / "index.html").write_text("ok", encoding="utf-8")
    (build_dir / "unexpected.html").write_text("x", encoding="utf-8")

    baseline = tmp_path / "baseline.txt"
    baseline.write_text("/index.html\n", encoding="utf-8")

    monkeypatch.setattr(cutover_readiness, "BUILD_DIR", build_dir)
    monkeypatch.setattr(cutover_readiness, "BASELINE_URLS_PATH", baseline)
    result = cutover_readiness._check_url_parity()
    assert result.status == "FAIL"
    assert "unexpected_extra" in result.detail
