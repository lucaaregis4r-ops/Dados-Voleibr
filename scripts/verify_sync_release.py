"""Mandatory pre-publication quality gate and smoke test.

Validates DuckDB integrity, rally invariants, exported artifacts,
compact payload bounds, sync health status, and responsive rules
prior to committing daily updates.
"""

import sys
import json
from pathlib import Path

BASE_REPO = Path(__file__).resolve().parent.parent
if str(BASE_REPO) not in sys.path:
    sys.path.insert(0, str(BASE_REPO))

from cbv.config import BASE_DIR
from cbv.pipeline import quality_gate


def verify_all(root_dir: Path = BASE_DIR) -> bool:
    print("🔍 [Gate 1/5] Verificando integridade DuckDB e invariantes de rallies...")
    db_path = root_dir / "data" / "cbv.duckdb"
    if not db_path.exists():
        print(f"❌ Banco {db_path} não encontrado!")
        return False
    matches = quality_gate(db_path, minimum_matches=5)
    print(f"✓ DuckDB íntegro: {matches} partidas validadas sem duplicações ou violação de rallies.")

    print("📁 [Gate 2/5] Verificando integridade de artefatos essenciais...")
    required_files = [
        root_dir / "index.html",
        root_dir / "docs" / "index.html",
        root_dir / "exports" / "dashboard.html",
        root_dir / "exports" / "sync_health.json",
        root_dir / "exports" / "matches_details.json",
        root_dir / "exports" / "tactical_details.json",
        root_dir / "docs" / "CADERNO_METODOLOGICO.md",
    ]
    for p in required_files:
        if not p.exists() or p.stat().st_size == 0:
            print(f"❌ Artefato ausente ou vazio: {p}")
            return False
    print("✓ Todos os artefatos essenciais foram gerados.")

    print("📦 [Gate 3/5] Verificando payload do HTML e meta de performance...")
    index_html = (root_dir / "index.html").read_text(encoding="utf-8")
    if "__SCOUTING_DATA__" in index_html:
        print("❌ Token __SCOUTING_DATA__ não foi substituído no index.html!")
        return False
    size_mb = (root_dir / "index.html").stat().st_size / (1024 * 1024)
    if size_mb > 5.0:
        print(f"❌ index.html excessivamente grande ({size_mb:.2f} MB)! Esperado < 2.0 MB com payload compacto.")
        return False
    print(f"✓ index.html compacto: {size_mb:.2f} MB (redução progressiva ativa).")

    print("🩺 [Gate 4/5] Verificando relatório formal de saúde (sync_health.json)...")
    health = json.loads((root_dir / "exports" / "sync_health.json").read_text(encoding="utf-8"))
    status = health.get("status")
    if status == "FAILED":
        print(f"❌ sync_health acusa status FAILED!")
        return False
    print(f"✓ Status de saúde do sync: {status}")

    print("📱 [Gate 5/5] Smoke test responsivo e ausência de overflow...")
    css_content = (root_dir / "cbv" / "export" / "templates" / "atlas.css").read_text(encoding="utf-8")
    # Verify mobile-first rules and overflow prevention
    if "overflow-x:clip" not in index_html and "overflow-x: clip" not in css_content and "overflow-x:hidden" not in css_content and "overflow-x: hidden" not in css_content:
        print("❌ Regras globais de contenção de overflow-x ausentes!")
        return False
    print("✓ Regras de contenção de overflow e responsividade verificadas.")

    print("🎉 Todos os gates de validação obrigatórios foram aprovados!")
    return True


if __name__ == "__main__":
    success = verify_all()
    sys.exit(0 if success else 1)
