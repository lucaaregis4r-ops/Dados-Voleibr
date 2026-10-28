from pathlib import Path

import duckdb

from cbv.pipeline import staged_update


def test_staged_update_handles_missing_raw_cache(tmp_path: Path):
    root = tmp_path
    data = root / "data"
    data.mkdir()

    with duckdb.connect(str(data / "cbv.duckdb")) as conn:
        conn.execute("CREATE TABLE matches (match_id INTEGER PRIMARY KEY)")

    def worker(stage_data: Path, stage: Path):
        # Mirrors cbv.config startup: the staged raw path must behave like
        # a real directory even when the GitHub Actions cache was empty.
        (stage_data / "raw").mkdir(parents=True, exist_ok=True)

        (stage / "exports").mkdir(parents=True, exist_ok=True)
        (stage / "docs").mkdir(parents=True, exist_ok=True)
        (stage / "index.html").write_text("<html>atlas</html>", encoding="utf-8")
        (stage / "exports" / "dashboard.html").write_text("<html>dashboard</html>", encoding="utf-8")
        (stage / "docs" / "index.html").write_text("<html>docs</html>", encoding="utf-8")
        (stage / "docs" / "CADERNO_METODOLOGICO.md").write_text("# Metodologia\n", encoding="utf-8")

    staged_update(root, worker)

    assert (data / "raw").is_dir()
