"""Regularized logistic model. Every training feature uses strictly earlier dates."""
from collections import defaultdict
from itertools import groupby
import math
import numpy as np
from cbv.analysis.scouting import enrich_record, metric_values

FEATURES = ('so', 'bp', 'eff', 'pos_rec', 'neg_rec', 'trans')
MIN_TRAIN = 20


def feature_vector(a, b):
    ma, mb = metric_values(a), metric_values(b)
    if any(ma[k]['value'] is None or mb[k]['value'] is None for k in FEATURES):
        return None
    # Fixed scaling; no full-dataset normalization or retrospective priors.
    return np.array([(ma[k]['value']-mb[k]['value'])/20 for k in FEATURES]+[(sum(r['_win'] for r in a[-5:])/len(a[-5:])-sum(r['_win'] for r in b[-5:])/len(b[-5:]))])


def fit(x, y):
    if len(x) < MIN_TRAIN:
        return None
    x, y = np.array(x), np.array(y)
    weights = np.zeros(x.shape[1])
    penalty = np.eye(len(weights))*2.0
    for _ in range(30):
        p = 1/(1+np.exp(-np.clip(x@weights, -30, 30)))
        step = np.linalg.solve(x.T@((p*(1-p))[:,None]*x)+penalty, x.T@(p-y)+penalty@weights)
        weights -= step
        if np.max(np.abs(step)) < 1e-7:
            break
    return weights


def probability(weights, vector):
    return float(1/(1+math.exp(-float(np.clip(vector@weights,-30,30)))))


def walk_forward(matches, rows):
    lookup = {(r['match_id'],r['team']):r for r in rows}
    history, xs, ys = defaultdict(list), [], []
    predictions, training_dates = [], []
    dated = sorted([m for m in matches if m.get('date') and m.get('validation_status')=='VALID' and m.get('home_sets') is not None and m.get('away_sets') is not None and m['home_sets']!=m['away_sets']], key=lambda m:(m['date'],m['match_id']))
    for day, batch in groupby(dated, key=lambda m:m['date']):
        weights = fit(xs, ys)
        pending = []
        for m in batch:
            h,a = m['home_team'],m['away_team']
            vector = feature_vector(history[h],history[a]) if history[h] and history[a] else None
            outcome = int(m['home_sets']>m['away_sets'])
            if vector is not None and weights is not None:
                predictions.append(dict(match_id=m['match_id'],date=day,trained_through=max(training_dates),training_matches=len(xs),home_team=h,away_team=a,probability_home=probability(weights,vector),actual_home_win=outcome))
            pending.append((m,vector,outcome))
        # Same-day games are never used to predict or construct features for each other.
        for m,vector,outcome in pending:
            if vector is not None:
                xs.append(vector); ys.append(outcome); training_dates.append(day)
            for team, won in [(m['home_team'],outcome),(m['away_team'],1-outcome)]:
                r = lookup.get((m['match_id'],team))
                if r:
                    history[team].append(dict(enrich_record(dict(r)),_win=won))
    return predictions, history, fit(xs,ys), len(xs)


def evaluation(predictions):
    n = len(predictions)
    bins = {k:dict(pred_count=0, actual_wins=0, probability_sum=0) for k in ('50-60%','60-70%','70-80%','80-100%')}
    brier,loss,correct = 0,0,0
    for r in predictions:
        p,y = r['probability_home'],r['actual_home_win']
        brier += (p-y)**2
        loss -= y*math.log(max(p,1e-15))+(1-y)*math.log(max(1-p,1e-15))
        win = int((p>=.5)==bool(y)); correct += win
        favorite = max(p,1-p)
        key = '50-60%' if favorite<.6 else '60-70%' if favorite<.7 else '70-80%' if favorite<.8 else '80-100%'
        bins[key]['pred_count']+=1; bins[key]['actual_wins']+=win; bins[key]['probability_sum']+=favorite
    ece=0
    for b in bins.values():
        count=b['pred_count']
        b['mean_probability']=b['probability_sum']/count if count else None
        b['observed_frequency']=b['actual_wins']/count if count else None
        if count:
            ece+=count*abs(b['mean_probability']-b['observed_frequency'])
    return dict(total_matches=n,correct_predictions=correct,accuracy_pct=100*correct/n if n else None,brier_score=brier/n if n else None,log_loss=loss/n if n else None,calibration_error=ece/n if n else None,calibration=bins,method='walk-forward; datas estritamente anteriores; mesmo dia em bloco',model_version='logistic-l2-v1',predictions=predictions)
