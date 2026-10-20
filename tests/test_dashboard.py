"""Tests for HTML Dashboard generation."""

from pathlib import Path
from cbv.export.html_dashboard import generate_dashboard_data, build_dashboard_html, export_dashboard_html


def test_generate_dashboard_data():
    data = generate_dashboard_data()
    assert "kpis" in data
    assert data["kpis"]["matches"] >= 7
    assert data["kpis"]["teams"] >= 10
    assert "summary" in data
    assert "sideout_breakpoint" in data["summary"]
    assert "dossiers" in data
    assert "SÃO PAULO" in data["dossiers"]


def test_build_and_export_dashboard_html(tmp_path):
    target_file = tmp_path / "test_dashboard.html"
    res_path = export_dashboard_html(target_file)
    assert res_path.exists()
    assert res_path.stat().st_size > 5000

    content = res_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "CBS Sub-18 Masculino Especial 2026" in content
    assert "SÃO PAULO" in content
    assert "P1 (Pos 1)" in content
