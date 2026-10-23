"""Regularized, associational on/off; only source-confirmed presence is eligible."""
from collections import defaultdict
from itertools import groupby
import math
import numpy as np

VERSION='lineup-context-l2-v1'
PENALTY=100.
MIN_TRAIN_MATCHES=3
MIN_EVALUATION_MATCHES=5


def _fit(rows,players):
    names=sorted({r['opponent'] for r in rows});athletes=sorted({p for r in rows for p in r['own_lineup_names']}) if players else []
    spec=dict(opponents=names,players=athletes)
    x=np.array([_features(r,spec) for r in rows]);y=np.array([r['winner_side']=='own' for r in rows],dtype=float)
    w=np.zeros(x.shape[1]);penalty=np.eye(len(w))*PENALTY;penalty[0,0]=.01
    for _ in range(20):
        p=1/(1+np.exp(-np.clip(x@w,-25,25)))
        step=np.linalg.solve(x.T@((p*(1-p))[:,None]*x)+penalty,x.T@(p-y)+penalty@w);w-=step
        if max(abs(step))<1e-7:break
    return spec,w


def _features(r,spec):
    own_home=r['home_team']==r['team'];h,a=r['score_home_before'],r['score_away_before']
    return [1.,float(r['serving_side']=='own'),(h+a)/50,(h-a)*(1 if own_home else -1)/10,r['set_number']/5]+[float(r['own_rotation']==p) for p in range(1,7)]+[float(r['opponent']==name) for name in spec['opponents']]+[float(name in r['own_lineup_names']) for name in spec['players']]


def _predict(fit,row):
    spec,w=fit;z=float(np.clip(np.array(_features(row,spec))@w,-25,25));return 1/(1+math.exp(-z))


def _scores(rows):
    games=defaultdict(list)
    for mid,p,y in rows:games[mid].append((p,y))
    if not games:return dict(matches=0,rallies=0,brier=None,log_loss=None,calibration_error=None,calibration=[])
    bins=[]
    for index in range(10):
        bucket=[(p,y) for _,p,y in rows if min(9,int(p*10))==index]
        if bucket:bins.append(dict(n=len(bucket),probability=sum(p for p,y in bucket)/len(bucket),observed=sum(y for p,y in bucket)/len(bucket)))
    ece=sum(b['n']*abs(b['probability']-b['observed']) for b in bins)/len(rows)
    return dict(matches=len(games),rallies=len(rows),calibration_error=ece,calibration=bins,brier=sum(sum((p-y)**2 for p,y in g)/len(g) for g in games.values())/len(games),
        log_loss=sum(-sum(y*math.log(max(p,1e-12))+(1-y)*math.log(max(1-p,1e-12)) for p,y in g)/len(g) for g in games.values())/len(games))


def contextual_effects(rows,team):
    eligible=[]
    for r in rows:
        if r.get('own_lineup_confidence')!='RECONSTRUCTED_HIGH' or not r.get('own_lineup_names') or len(set(r['own_lineup_names']))!=6 or r.get('own_rotation') is None or not r.get('date'):continue
        opponent=r['away_team'] if r['home_team']==team else r['home_team']
        eligible.append(dict(r,team=team,opponent=opponent,day=str(r['date'])[:10]))
    history=[];candidate=[];baseline=[];folds=[]
    for day,batch in groupby(sorted(eligible,key=lambda r:(r['day'],r['match_id'],r['set_number'],r['rally_number'])),key=lambda r:r['day']):
        batch=list(batch)
        if len({r['match_id'] for r in history})>=MIN_TRAIN_MATCHES:
            extended=_fit(history,True);simple=_fit(history,False)
            for row in batch:
                y=float(row['winner_side']=='own');candidate.append((row['match_id'],_predict(extended,row),y));baseline.append((row['match_id'],_predict(simple,row),y))
            folds.append(dict(day=day,trained_through=max(r['day'] for r in history),training_matches=len({r['match_id'] for r in history})))
        history.extend(batch)
    a,b=_scores(candidate),_scores(baseline)
    accepted=a['matches']>=MIN_EVALUATION_MATCHES and a['brier']<b['brier'] and a['log_loss']<b['log_loss'] and a['calibration_error']<=b['calibration_error']
    effects=[];parameters=None
    if history:
        spec,w=_fit(history,True);parameters=dict(spec=spec,coefficients=w.tolist(),penalty=PENALTY)
        offset=11+len(spec['opponents'])
        for i,name in enumerate(spec['players']):
            on=sum(name in r['own_lineup_names'] for r in history);off=len(history)-on
            if on>=20 and off>=20:
                effects.append(dict(player=name,value=float(w[offset+i]) if accepted else None,unit='log-odds',n_on=on,n_off=off,
                    metric_class='EXPERIMENTAL',model_version=VERSION))
    return dict(model_version=VERSION,metric_class='EXPERIMENTAL',accepted=accepted,effects=effects,candidate=a,baseline=b,folds=folds,parameters=parameters,
        training_matches=len({r['match_id'] for r in history}),minimum_training_matches=MIN_TRAIN_MATCHES,minimum_evaluation_matches=MIN_EVALUATION_MATCHES,
        features=['opponent','rotation','serve_receive','score_before','set','all_six_teammates'],
        limitation='Associação regularizada, não causal. β em log-odds sob convenção L2 e colinearidade de seis atletas. Sem intervalo validado. Exige melhora em Brier/log loss por jogo e amostra com/sem ≥20; nunca substituir baseline pré-jogo.')
