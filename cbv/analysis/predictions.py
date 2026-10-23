"""Predictive tactical engine and pre-match scouting for volleyball matchups."""

import math
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from cbv.database.repository import default_repo
from cbv.analysis.tactics import get_team_tactical_dossier

import random
from collections import Counter

console = Console()


def sigmoid(x: float) -> float:
    """Standard sigmoid function for probability scaling."""
    return 1.0 / (1.0 + math.exp(-x))


def simulate_monte_carlo_match(
    so_a_pct: float,
    bp_a_pct: float,
    so_b_pct: float,
    bp_b_pct: float,
    n_simulations: int = 5000,
    best_of_five: bool = True,
) -> Dict[str, Any]:
    """
    Rally-by-rally stochastic Monte Carlo simulation engine.
    Models volleyball as an alternating Markov transition process.
    """
    p_so_a = max(0.20, min(0.90, so_a_pct / 100.0))
    p_so_b = max(0.20, min(0.90, so_b_pct / 100.0))

    target_sets = 3 if best_of_five else 2
    score_counts = Counter()
    total_pts_list = []
    wins_a = 0

    for _ in range(n_simulations):
        sets_a = 0
        sets_b = 0
        match_pts = 0

        while sets_a < target_sets and sets_b < target_sets:
            is_tiebreak = (sets_a == target_sets - 1 and sets_b == target_sets - 1)
            target_pts = 15 if is_tiebreak else 25

            pa, pb = 0, 0
            server_is_a = random.random() < 0.5

            while True:
                if server_is_a:
                    if random.random() < p_so_b:
                        pb += 1
                        server_is_a = False
                    else:
                        pa += 1
                else:
                    if random.random() < p_so_a:
                        pa += 1
                        server_is_a = True
                    else:
                        pb += 1

                if (pa >= target_pts or pb >= target_pts) and abs(pa - pb) >= 2:
                    match_pts += pa + pb
                    if pa > pb:
                        sets_a += 1
                    else:
                        sets_b += 1
                    break

        score_counts[f"{sets_a}x{sets_b}"] += 1
        total_pts_list.append(match_pts)
        if sets_a == target_sets:
            wins_a += 1

    prob_scores = {k: round(v / n_simulations * 100, 1) for k, v in sorted(score_counts.items())}
    avg_pts = round(sum(total_pts_list) / n_simulations, 1)

    ou_line = round(avg_pts)
    over_count = sum(1 for p in total_pts_list if p > ou_line)

    return {
        "n_simulations": n_simulations,
        "win_probability_a": round(wins_a / n_simulations * 100, 1),
        "win_probability_b": round((n_simulations - wins_a) / n_simulations * 100, 1),
        "score_distribution": prob_scores,
        "expected_total_points": avg_pts,
        "over_under_line": ou_line,
        "over_probability": round(over_count / n_simulations * 100, 1),
        "under_probability": round((n_simulations - over_count) / n_simulations * 100, 1),
    }


def _cohorts():
    from cbv.export.html_dashboard import generate_dashboard_data
    return generate_dashboard_data()['cohorts']


def evaluate_prediction_model() -> Dict[str, Any]:
    from cbv.analysis.temporal import evaluation
    predictions = [p for c in _cohorts() for p in c['evaluation']['predictions']]
    return evaluation(predictions)


def predict_matchup(team_a_query, team_b_query, include_evaluation=True, season=None):
    """Current-cohort L2 logistic forecast, validated with identical temporal features."""
    for c in _cohorts():
        if season and c['season'] != season:
            continue
        names = [t['team'] for t in c['teams']]
        def resolve(query):
            exact = [n for n in names if n.casefold() == query.casefold()]
            partial = [n for n in names if query.casefold() in n.casefold()]
            found = exact or partial
            return found[0] if len(found)==1 else None
        a,b = resolve(team_a_query),resolve(team_b_query)
        if not a or not b or a==b:
            continue
        matchup = next((m for m in c['model_matchups'] if {m['team_a'],m['team_b']}=={a,b}),None)
        if not matchup:
            continue
        p = matchup['probability_a'] if matchup['team_a']==a else 1-matchup['probability_a']
        ev=c['evaluation']
        return dict(team_a=a,team_b=b,metric_class='MODELO',model_version=ev['model_version'],
                    probabilities={a:round(100*p,1),b:round(100*(1-p),1)},
                    favorite=a if p>=.5 else b,confidence='Não quantificada',
                    projected_scores={'best_of_3':'Indisponível','best_of_5':'Indisponível'},
                    precision=dict(empirical_accuracy_pct=ev['accuracy_pct'],brier_score=ev['brier_score'],
                                   log_loss=ev['log_loss'],calibration_error=ev['calibration_error'],
                                   margin_of_error_pct=None,ci_90=None,
                                   interval_note='Intervalo preditivo ainda não estimado; sets não são ensaios de vitórias independentes.',
                                   season_calibration={'target_season':c['season'],'method':'Somente coorte selecionada; sem mistura entre temporadas'},
                                   validation=ev if include_evaluation else None))
    return None


def display_match_prediction(team_a_query, team_b_query):
    pred=predict_matchup(team_a_query,team_b_query,season=None)
    if not pred:
        console.print('Modelo indisponível: histórico anterior insuficiente ou equipes de coortes diferentes.')
        return
    console.print(Panel(f"{pred['team_a']} × {pred['team_b']} · MODELO"))
    console.print(pred['probabilities'])
    console.print(pred['precision']['interval_note'])
    console.print(f"Validação temporal: {pred['precision']['validation']}")


def display_model_evaluation():
    result=evaluate_prediction_model()
    console.print(Panel('Validação temporal · regressão logística regularizada'))
    console.print({k:v for k,v in result.items() if k!='predictions'})
