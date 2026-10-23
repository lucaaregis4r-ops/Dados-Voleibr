"""Pre-match intercept challenger, evaluated against preserved baseline on common days."""
from collections import defaultdict
from itertools import groupby
import numpy as np
from cbv.analysis.temporal import fit,feature_vector,probability,evaluation
from cbv.analysis.scouting import enrich_record


def evaluate_intercept(matches,records):
    lookup={(r['match_id'],r['team']):r for r in records};history=defaultdict(list);xs=[];ys=[];base=[];candidate=[];dates=[]
    eligible=sorted([m for m in matches if m.get('date') and m.get('validation_status')=='VALID' and m.get('home_sets') is not None and m.get('away_sets') is not None and m['home_sets']!=m['away_sets']],key=lambda m:(m['date'],m['match_id']))
    for day,batch in groupby(eligible,key=lambda m:m['date']):
        w=fit(xs,ys);extended=fit([np.r_[1.,x] for x in xs],ys);pending=[]
        for m in batch:
            h,a=m['home_team'],m['away_team'];vector=feature_vector(history[h],history[a]) if history[h] and history[a] else None;y=int(m['home_sets']>m['away_sets'])
            if vector is not None and w is not None and extended is not None:
                row=dict(match_id=m['match_id'],date=day,trained_through=max(dates),actual_home_win=y)
                base.append(dict(row,probability_home=probability(w,vector)))
                candidate.append(dict(row,probability_home=probability(extended,np.r_[1.,vector])))
            pending.append((m,vector,y))
        for m,vector,y in pending:
            if vector is not None:xs.append(vector);ys.append(y);dates.append(day)
            for team,won in [(m['home_team'],y),(m['away_team'],1-y)]:
                if (m['match_id'],team) in lookup:history[team].append(dict(enrich_record(dict(lookup[(m['match_id'],team)])),_win=won))
    b,c=evaluation(base),evaluation(candidate)
    improved=bool(base) and c['brier_score']<b['brier_score'] and c['log_loss']<b['log_loss'] and c['calibration_error']<=b['calibration_error']
    return dict(model_version='logistic-l2-intercept-v2',baseline=b,candidate=c,common_sample=True,improved=improved,
        active_model='logistic-l2-v1',status='EXPERIMENTAL',features=['intercept_home_contrast','baseline_v1_features'],
        limitation='Intercepto e mando não são identificáveis separadamente quando toda observação é mandante versus visitante. Challenger não promovido automaticamente.')
