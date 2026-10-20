"""Unit tests for CSV and JSON exporters."""

from pathlib import Path
import json
import pandas as pd
from cbv.export.csv_export import export_all_to_csv
from cbv.export.json_export import export_all_to_json


def test_export_all_to_csv(tmp_path):
    target = export_all_to_csv(tmp_path)
    assert (target / "matches.csv").exists()
    assert (target / "players.csv").exists()
    assert (target / "teams.csv").exists()
    assert (target / "rankings_scoring.csv").exists()

    df_matches = pd.read_csv(target / "matches.csv")
    assert len(df_matches) > 0


def test_export_all_to_json(tmp_path):
    target = export_all_to_json(tmp_path)
    assert (target / "matches.json").exists()
    assert (target / "players.json").exists()
    assert (target / "teams.json").exists()
    assert (target / "rankings.json").exists()

    data = json.loads((target / "rankings.json").read_text(encoding="utf-8"))
    assert "scoring" in data
    assert "attack" in data
    assert "serve" in data
    assert "block" in data
