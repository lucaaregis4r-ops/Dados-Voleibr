"""Predictive tactical engine and pre-match scouting for volleyball matchups."""

import math
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from cbv.database.repository import default_repo
from cbv.analysis.tactics import get_team_tactical_dossier


console = Console()


def _cohorts():
    from cbv.export.html_dashboard import generate_dashboard_data
    return generate_dashboard_data(include_atlas=False)['cohorts']


def evaluate_prediction_model() -> Dict[str, Any]:
    from cbv.analysis.temporal import evaluation
    predictions = [p for c in _cohorts() for p in c['evaluation']['predictions']]
    return evaluation(predictions)


def predict_matchup(team_a_query, team_b_query, include_evaluation=True, season=None):
    """Current-cohort L2 logistic forecast, validated with identical temporal features."""
    cohorts=_cohorts()
    if not season:
        latest={}
        for c in cohorts:
            key=(c['competition'],c['category'],c['gender'])
            latest[key]=max(latest.get(key,''),c['season'] or '')
        cohorts=[c for c in cohorts if c['season']==latest[(c['competition'],c['category'],c['gender'])]]
    for c in cohorts:
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
        return dict(team_a=a,team_b=b,metric_class='MODELADO',model_version=ev['model_version'],
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
