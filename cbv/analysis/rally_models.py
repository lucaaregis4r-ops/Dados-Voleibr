"""Auditable day-blocked rally models. Experimental until common-sample validation.

All priors are fit on earlier days in the same competition. Current score is a
state, never a training observation. No contact or player effects are invented.
"""
from collections import defaultdict
from itertools import groupby
from functools import lru_cache
import math
import numpy as np

VERSION='atlas-rally-beta-v1'
PRIOR_STRENGTH=30


def loss(rows):
    if not rows:return dict(n=0,brier=None,log_loss=None)
    return dict(n=len(rows),brier=sum((p-y)**2 for p,y in rows)/len(rows),
        log_loss=-sum(y*math.log(max(p,1e-12))+(1-y)*math.log(max(1-p,1e-12)) for p,y in rows)/len(rows))


class ScoreModel:
    """Exact absorbing-state set model with distinct serve/receive probabilities."""
    def __init__(self,home_serve,home_receive,sets_to_win):
        self.hs=home_serve;self.hr=home_receive;self.needed=sets_to_win
        self.set_probability=lru_cache(None)(self._set_probability)
        self.match_probability=lru_cache(None)(self._match_probability)
        self.deuce={}

    def _deuce(self,target):
        if target in self.deuce:return self.deuce[target]
        # States: tied/H serve, tied/A serve, H advantage/H serve, A advantage/A serve.
        matrix=np.eye(4);rhs=np.zeros(4)
        for index,server in [(0,'home'),(1,'away')]:
            p=self.hs if server=='home' else self.hr
            matrix[index,2]-=p;matrix[index,3]-=1-p
        rhs[2]=self.hs;matrix[2,1]-=1-self.hs
        matrix[3,0]-=self.hr
        result=np.linalg.solve(matrix,rhs);self.deuce[target]=result;return result

    def _set_probability(self,h,a,server,target):
        if h>=target and h-a>=2:return 1.
        if a>=target and a-h>=2:return 0.
        if h>=target-1 and a>=target-1:
            values=self._deuce(target)
            if h==a:return float(values[0 if server=='home' else 1])
            return float(values[2 if h>a else 3])
        p=self.hs if server=='home' else self.hr
        return p*self.set_probability(h+1,a,'home',target)+(1-p)*self.set_probability(h,a+1,'away',target)

    def _match_probability(self,hs,aws,h,a,server):
        if hs>=self.needed:return 1.
        if aws>=self.needed:return 0.
        target=15 if hs==aws==self.needed-1 else 25
        q=self.set_probability(h,a,server,target)
        def next_set(x,y):
            if x>=self.needed:return 1.
            if y>=self.needed:return 0.
            # Future first server is unobserved pre-match: explicit equal mixture.
            return .5*(self.match_probability(x,y,0,0,'home')+self.match_probability(x,y,0,0,'away'))
        return q*next_set(hs+1,aws)+(1-q)*next_set(hs,aws+1)


def enrich_temporal(matches,rows):
    by_match=defaultdict(list)
    for r in rows:by_match[r['match_id']].append(r)
    global_counts={False:[0,0],True:[0,0]};team_counts=defaultdict(lambda:[0,0]);history=[];evaluated=[];baseline=[];runs=[]
    dated=sorted([m for m in matches if m.get('date') and m['match_id'] in by_match],key=lambda m:(str(m['date'])[:10],m['match_id']))
    for day,batch in groupby(dated,key=lambda m:str(m['date'])[:10]):
        batch=list(batch);pending=[]
        for m in batch:
            rr=by_match[m['match_id']];h,a=m['home_team'],m['away_team'];prior_dates=[d for d in history if d<day]
            def expected(team,serving):
                gk,gn=global_counts[serving];k,n=team_counts[(team,serving)]
                if not gn:return None
                return (k+PRIOR_STRENGTH*(gk+.5)/(gn+1))/(n+PRIOR_STRENGTH)
            hs,hr=expected(h,True),expected(h,False)
            model=ScoreModel(hs,hr,2 if m['competition']=='CBS' else 3) if hs is not None and hr is not None else None
            sets_h=sets_a=0;previous_set=None
            for r in rr:
                if previous_set is not None and r['set_number']!=previous_set:
                    if previous['score_home_after']>previous['score_away_after']:sets_h+=1
                    else:sets_a+=1
                previous_set=r['set_number'];previous=r
                server=r['serving_side'];target=15 if sets_h==sets_a==(model.needed-1 if model else (1 if m['competition']=='CBS' else 2)) else 25
                sh,sa=r['score_home_before'],r['score_away_before'];ah,aa=r['score_home_after'],r['score_away_after']
                r.update(wp_before=None,wp_after=None,wpa=None,leverage=None,expected_home=None,
                    crunch=min(sh,sa)>=target-5 and abs(sh-sa)<=2,super_crunch=min(sh,sa)>=target-2 and abs(sh-sa)<=1,
                    model_version=VERSION,model_class='EXPERIMENTAL',trained_through=max(prior_dates) if prior_dates else None)
                p=expected(h,server=='home')
                if model:
                    before=model.match_probability(sets_h,sets_a,sh,sa,server)
                    win=model.match_probability(sets_h,sets_a,sh+1,sa,'home');lose=model.match_probability(sets_h,sets_a,sh,sa+1,'away')
                    after=model.match_probability(sets_h,sets_a,ah,aa,r['winner_side'])
                    r.update(wp_before=before,wp_after=after,wpa=after-before,leverage=win-lose,expected_home=p)
                    evaluated.append((p,int(r['winner_side']=='home')))
                    gk,gn=global_counts[server=='home'];baseline.append(((gk+.5)/(gn+1),int(r['winner_side']=='home')))
                pending.append(r)
            if model:
                model.set_probability.cache_clear();model.match_probability.cache_clear()
            runs.append(dict(match_id=m['match_id'],training_window=[min(prior_dates),max(prior_dates)] if prior_dates else None,
                training_matches=len(history),features=['team','serve_receive','prior_scoreboard_points'],parameters=dict(prior_strength=PRIOR_STRENGTH,home_serve=hs,home_receive=hr),
                model_version=VERSION,model_class='EXPERIMENTAL',format_source='CBS best-of-three; Superliga best-of-five; validate competition rules before extending'))
        for r in pending:
            for side in ('home','away'):
                serving=r['serving_side']==side;won=int(r['winner_side']==side);team=r[side+'_team']
                global_counts[serving][0]+=won;global_counts[serving][1]+=1
                team_counts[(team,serving)][0]+=won;team_counts[(team,serving)][1]+=1
        history.extend([day]*len(batch))
    result=loss(evaluated);simple=loss(baseline)
    # These are rally probability scores, not match-WP calibration. Never promote WP on their basis.
    return dict(model_version=VERSION,status='EXPERIMENTAL',candidate=result,baseline=simple,common_sample=True,runs=runs,
        wp_validation='Não validado em outcomes de partida; WP, WPA e leverage permanecem experimentais.',
        evaluation_unit='ponto do placar; dependência intrapartida; desempenho preditivo não implica causalidade')
