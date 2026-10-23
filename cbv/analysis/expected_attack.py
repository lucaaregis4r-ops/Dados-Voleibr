"""Phase-specific historical expectation; rounded kills remain approximate."""
from collections import defaultdict
from itertools import groupby


def walk_forward_attack(matches,records):
    match_by={m['match_id']:m for m in matches};totals=defaultdict(lambda:[0.,0]);output=[]
    dated=sorted([r for r in records if r['match_id'] in match_by and match_by[r['match_id']].get('date')],key=lambda r:(str(match_by[r['match_id']]['date'])[:10],r['match_id']))
    for day,batch in groupby(dated,key=lambda r:str(match_by[r['match_id']]['date'])[:10]):
        batch=list(batch);pending=[]
        for r in batch:
            for phase in ('pos_rec','neg_rec','trans'):
                n,k=r.get(phase+'_att_attempts'),r.get(phase+'_att_points');pk,pn=totals[phase]
                if n is None or k is None or n<=0:continue
                expected=n*pk/pn if pn else None
                output.append(dict(match_id=r['match_id'],team=r['team'],phase=phase,n=n,kills=k,
                    expected_kill_pct=100*pk/pn if pn else None,expected_kills=expected,above_expected=k-expected if expected is not None else None,
                    training_attempts=pn,training_cutoff_exclusive=day,metric_class='EXPERIMENTAL',model_version='phase-prior-v1',
                    limitation='Kills reconstruídos de percentuais arredondados; baseline de fase, sem ajuste por adversário.'))
                pending.append((phase,k,n))
        for phase,k,n in pending:totals[phase][0]+=k;totals[phase][1]+=n
    return output
