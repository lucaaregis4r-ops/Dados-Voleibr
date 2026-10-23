"""Regularized team/opponent effects with day-blocked common-sample evaluation.

Report-credit SO/BP remain separate from scoreboard-rally models. Rounded
reception percentages yield a quasi-binomial fit, explicitly experimental.
"""
from collections import defaultdict
from itertools import groupby
import math
import numpy as np
from cbv.analysis.scouting import metric_values,enrich_record

PENALTY=50.


def fit_effects(history):
    names=sorted({r['team'] for r in history}|{r['opponent'] for r in history});index={n:i for i,n in enumerate(names)}
    if not history:return None
    x=np.zeros((len(history),1+2*len(names)));k=np.array([r['k'] for r in history]);n=np.array([r['n'] for r in history])
    for i,r in enumerate(history):x[i,0]=1;x[i,1+index[r['team']]]=1;x[i,1+len(names)+index[r['opponent']]]=1
    penalty=np.eye(x.shape[1])*PENALTY;penalty[0,0]=.01;w=np.zeros(x.shape[1]);w[0]=math.log((sum(k)+.5)/(sum(n-k)+.5))
    for _ in range(20):
        p=1/(1+np.exp(-np.clip(x@w,-25,25)))
        step=np.linalg.solve(x.T@((n*p*(1-p))[:,None]*x)+penalty,x.T@(n*p-k)+penalty@w);w-=step
        if max(abs(step))<1e-7:break
    return names,index,w


def predict(fit,team,opponent):
    names,index,w=fit;z=w[0]
    if team in index:z+=w[1+index[team]]
    if opponent in index:z+=w[1+len(names)+index[opponent]]
    return float(1/(1+math.exp(-float(np.clip(z,-25,25)))))


def scores(predictions):
    n=sum(r['n'] for r in predictions)
    if not n:return dict(n=0,brier=None,log_loss=None,matches=0)
    # Exact average of binary scoring rules from k,n; approximate k is labeled.
    return dict(n=n,matches=len({r['match_id'] for r in predictions}),
        brier=sum(r['k']*(1-r['p'])**2+(r['n']-r['k'])*r['p']**2 for r in predictions)/n,
        log_loss=-sum(r['k']*math.log(max(r['p'],1e-12))+(r['n']-r['k'])*math.log(max(1-r['p'],1e-12)) for r in predictions)/n)


def evaluate_ratings(matches,records):
    lookup={m['match_id']:m for m in matches};events=[]
    for r in records:
        m=lookup.get(r['match_id'])
        if not m or not m.get('date') or m.get('validation_status')!='VALID':continue
        opponent=m['away_team'] if r['team']==m['home_team'] else m['home_team']
        metrics=metric_values([enrich_record(dict(r))])
        for phase in ('so','bp','kill','positive'):
            value=metrics[phase]
            if value['n'] and 0<=value['numerator']<=value['n']:
                events.append(dict(match_id=r['match_id'],day=str(m['date'])[:10],team=r['team'],opponent=opponent,phase=phase,k=value['numerator'],n=value['n']))
    results={}
    for phase in ('so','bp','kill','positive'):
        history=[];candidate=[];baseline=[]
        for day,batch in groupby(sorted([r for r in events if r['phase']==phase],key=lambda r:(r['day'],r['match_id'])),key=lambda r:r['day']):
            batch=list(batch)
            if len({r['match_id'] for r in history})>=20:
                fitted=fit_effects(history);prior=(sum(r['k'] for r in history)+.5)/(sum(r['n'] for r in history)+1)
                for r in batch:
                    candidate.append(dict(r,p=predict(fitted,r['team'],r['opponent']),trained_through=max(x['day'] for x in history)))
                    baseline.append(dict(r,p=prior))
            history.extend(batch)
        a,b=scores(candidate),scores(baseline)
        improved=a['matches']>=20 and a['brier']<b['brier'] and a['log_loss']<b['log_loss']
        fitted=fit_effects(history) if history else None;ratings=[]
        if fitted:
            names,index,w=fitted;center=float(1/(1+math.exp(-w[0])))
            for name in names:
                adjusted=predict(fitted,name,'__AVERAGE_OPPONENT__')
                ratings.append(dict(team=name,strength=100*adjusted,delta=100*(adjusted-center),opponent_allowance_logit=float(w[1+len(names)+index[name]])))
        results[phase]=dict(metric_class='EXPERIMENTAL',model_version='opponent-logistic-l2-v1',penalty=PENALTY,
            candidate=a,baseline=b,common_sample=True,improved=improved,ratings=ratings if improved else [],
            candidate_ratings=ratings,minimum_evaluation_matches=20,training_matches=len({r['match_id'] for r in history}),
            parameters=dict(names=fitted[0],coefficients=fitted[2].tolist(),penalty=PENALTY) if fitted else None,
            predictions=[dict(match_id=r['match_id'],team=r['team'],trained_through=r['trained_through'],probability=r['p']) for r in candidate],
            definition='SO/BP creditados do relatório; Kill% publicado; recepção positiva aproximada.',
            limitation='Modelo associativo; regularização fixa 50, sem causalidade; recepção usa proporção arredondada. Ratings retidos somente com melhora temporal em Brier/log loss e ≥20 jogos de avaliação; ainda experimentais.')
    return results
