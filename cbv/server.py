"""FastAPI backend server for the CBV Volley Data web application."""

import sys
import webbrowser
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from cbv.config import BASE_DIR, logger
from cbv.database.repository import default_repo
from cbv.export.html_dashboard import generate_dashboard_data, build_dashboard_html
from cbv.scraper.sync import run_daily_sync
from cbv.analysis.predictions import predict_matchup, evaluate_prediction_model
from cbv.analysis.setter_distribution import compute_setter_distribution
from cbv.export.csv_export import export_all_to_csv
from cbv.export.json_export import export_all_to_json
from cbv.export.html_dashboard import export_dashboard_html

app = FastAPI(
    title="CBV Volley Data — Tactical Intelligence & Scouting",
    description="Plataforma de inteligência tática, predição e scouting da CBV",
    version="2.0.0",
)

EXPORTS_DIR = BASE_DIR / "exports"


class SyncPayload(BaseModel):
    url: Optional[str] = None
    force: bool = False


@app.get("/api/competitions")
def api_competitions():
    """Returns available competitions, categories, genders and match counts."""
    try:
        with default_repo.get_connection() as conn:
            comps = conn.execute("""
                SELECT 
                    competition, 
                    category, 
                    gender, 
                    COUNT(*) as match_count,
                    MIN(date) as start_date, 
                    MAX(date) as end_date
                FROM matches
                GROUP BY 1, 2, 3
                ORDER BY match_count DESC
            """).fetchdf().to_dict(orient="records")
            for c in comps:
                if hasattr(c.get("start_date"), "isoformat"):
                    c["start_date"] = c["start_date"].isoformat()
                if hasattr(c.get("end_date"), "isoformat"):
                    c["end_date"] = c["end_date"].isoformat()
                gen = c.get("gender")
                c_name = c.get("competition")
                key = f"{c_name}_{gen}".upper() if gen else str(c_name).upper()
                c["key"] = key
                c["label"] = f"{c_name} {c.get('category') or ''} ({gen or ''})".strip().upper()
        return {"competitions": comps}
    except Exception as e:
        logger.error(f"Error fetching competitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data")
def get_all_data(competition: Optional[str] = None):
    """Returns the consolidated competition, tactical and predictive dataset."""
    try:
        data = generate_dashboard_data(competition=competition)
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sync")
def trigger_sync(payload: SyncPayload):
    """Executes daily sync pipeline by URL or competition filters, updating DuckDB and bulletin."""
    try:
        res = run_daily_sync(url=payload.url, open_browser=False)
        txt_path = EXPORTS_DIR / "boletim_ct_diario.txt"
        bulletin_txt = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""
        return {
            "status": "success",
            "competition": res.get("competition"),
            "new_matches": res.get("new_matches", 0),
            "total_matches": res.get("total_matches", 0),
            "bulletin_txt": bulletin_txt,
            "message": f"Sincronização concluída com sucesso! {res.get('new_matches', 0)} novos jogos ingeridos.",
        }
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar: {e}")


@app.get("/api/predict")
def api_predict(team_a: str = Query(...), team_b: str = Query(...)):
    """Computes match prediction and precision metrics between two teams."""
    pred = predict_matchup(team_a, team_b)
    if not pred:
        raise HTTPException(status_code=404, detail="Não foi possível calcular previsão para as equipes informadas.")
    return pred


@app.get("/api/simulated-fixtures")
def api_simulated_fixtures(competition: Optional[str] = None):
    """Computes and returns precomputed Monte Carlo match simulations for marquee fixtures."""
    try:
        fixtures = [
            {"team_a": "SADA CRUZEIRO VÔLEI", "team_b": "VÔLEI RENATA", "competition": "SUPERLIGA_MASCULINO", "label": "Superliga Masc // Sada Cruzeiro × Renata"},
            {"team_a": "DENTIL PRAIA CLUBE", "team_b": "GERDAU MINAS", "competition": "SUPERLIGA_FEMININO", "label": "Superliga Fem // Praia Clube × Gerdau Minas"},
            {"team_a": "SESI VÔLEI BAURU", "team_b": "ITAMBÉ MINAS", "competition": "SUPERLIGA_MASCULINO", "label": "Superliga Masc // Sesi Bauru × Itambé Minas"},
            {"team_a": "OSASCO SÃO CRISTÓVÃO SAÚDE", "team_b": "FLUMINENSE", "competition": "SUPERLIGA_FEMININO", "label": "Superliga Fem // Osasco × Fluminense"},
            {"team_a": "SUZANO VÔLEI", "team_b": "JOINVILLE VÔLEI", "competition": "SUPERLIGA_MASCULINO", "label": "Superliga Masc // Suzano × Joinville"},
            {"team_a": "MINAS GERAIS", "team_b": "SÃO PAULO", "competition": "CBS_MASCULINO", "label": "CBS Sub-18 // Minas Gerais × São Paulo"},
            {"team_a": "RIO DE JANEIRO", "team_b": "PARANÁ", "competition": "CBS_MASCULINO", "label": "CBS Sub-18 // Rio de Janeiro × Paraná"},
        ]

        if competition and competition != "ALL":
            fixtures = [f for f in fixtures if f["competition"] == competition]

        simulations = []
        for fix in fixtures:
            pred = predict_matchup(fix["team_a"], fix["team_b"], include_evaluation=True)
            if pred:
                simulations.append({
                    "fixture": fix,
                    "prediction": pred,
                })

        return {
            "total_fixtures": len(simulations),
            "simulations": simulations,
        }
    except Exception as e:
        logger.error(f"Error computing simulated fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/setter-distribution")
def api_setter_distribution(
    team: str = Query(...),
    rotation: str = Query("P1"),
    pass_quality: str = Query("positive"),
):
    """Computes setter distribution and tactical advice for a specific team, rotation and pass quality."""
    dist = compute_setter_distribution(team, rotation=rotation, pass_quality=pass_quality)
    if not dist:
        raise HTTPException(status_code=404, detail=f"Equipe '{team}' não encontrada ou sem dados táticos.")
    return dist


@app.get("/api/model-evaluation")
def api_model_evaluation():
    """Returns backtesting and calibration results for the match prediction model."""
    return evaluate_prediction_model()


@app.get("/api/bulletin")
def api_bulletin():
    """Returns the latest CT bulletin in text format for WhatsApp sharing."""
    txt_path = EXPORTS_DIR / "boletim_ct_diario.txt"
    if not txt_path.exists():
        return {"bulletin": "", "exists": False}
    return {"bulletin": txt_path.read_text(encoding="utf-8"), "exists": True}


@app.post("/api/export-all")
def api_export_all():
    """Exports all data to CSV, JSON, and standalone HTML files."""
    try:
        export_all_to_csv()
        export_all_to_json()
        html_p = export_dashboard_html()
        return {
            "status": "success",
            "message": "Arquivos CSV, JSON e Dashboard HTML exportados para a pasta exports/",
            "dashboard_path": str(html_p.resolve()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def index_page():
    """Serves the unified modern web application interface."""
    data = generate_dashboard_data()
    return build_dashboard_html(data)


def start_app(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    """Launches the unified web server and opens the browser."""
    # Find free port if 8000 is occupied
    import socket
    for p in range(port, port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, p)) != 0:
                port = p
                break

    url = f"http://{host}:{port}"
    print("\n" + "=" * 65)
    print(f"🏐 CBV VOLLEY DATA — APLICAÇÃO WEB DA COMISSÃO TÉCNICA")
    print(f"🚀 Servidor iniciado em: {url}")
    print(f"💡 Pressione CTRL+C no terminal para encerrar a aplicação")
    print("=" * 65 + "\n")

    if open_browser:
        def _open():
            time.sleep(1.0)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    start_app()
