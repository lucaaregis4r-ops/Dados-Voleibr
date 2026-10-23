from cbv.analysis.rally_models import ScoreModel,enrich_temporal


def test_state_probability_symmetry_deuce_terminal_and_bp():
    model=ScoreModel(.4,.6,3)
    assert abs(model.match_probability(0,0,0,0,'home')+model.match_probability(0,0,0,0,'away')-1)<1e-10
    assert model.match_probability(3,1,0,0,'home')==1
    assert model.match_probability(1,3,0,0,'away')==0
    assert model.set_probability(26,24,'home',25)==1
    assert model.set_probability(24,26,'away',25)==0
    assert abs(model.set_probability(24,24,'home',25)-model.set_probability(38,38,'home',25))<1e-12
    assert model.match_probability(2,2,14,13,'home')>model.match_probability(2,2,13,14,'away')


def test_same_day_and_future_do_not_train_rally_models():
    matches=[dict(match_id=i,date=day,home_team='A',away_team='B',competition='CBS') for i,day in [(1,'2026-01-01'),(2,'2026-01-01'),(3,'2026-01-02')]]
    rows=[dict(match_id=i,set_number=1,rally_number=1,home_team='A',away_team='B',serving_side='home',winner_side='home',score_home_before=0,score_away_before=0,score_home_after=1,score_away_after=0) for i in (1,2,3)]
    result=enrich_temporal(matches,rows)
    assert rows[0]['expected_home'] is None and rows[1]['expected_home'] is None
    assert rows[2]['trained_through']=='2026-01-01'
    assert result['runs'][2]['training_matches']==2
    assert result['status']=='EXPERIMENTAL'


def test_expected_attack_never_uses_same_day_or_its_own_kills():
    from cbv.analysis.expected_attack import walk_forward_attack
    matches=[dict(match_id=i,date=d) for i,d in [(1,'2026-01-01'),(2,'2026-01-01'),(3,'2026-01-02')]]
    records=[dict(match_id=i,team='A',pos_rec_att_attempts=10,pos_rec_att_points=k) for i,k in [(1,8),(2,2),(3,10)]]
    result=walk_forward_attack(matches,records)
    assert result[0]['expected_kills'] is None and result[1]['expected_kills'] is None
    assert result[2]['expected_kills']==5
    assert result[2]['above_expected']==5


def test_intercept_challenger_preserves_baseline_and_common_sample():
    from cbv.analysis.challengers import evaluate_intercept
    result=evaluate_intercept([],[])
    assert result['active_model']=='logistic-l2-v1'
    assert result['baseline']['total_matches']==result['candidate']['total_matches']==0
    assert not result['improved']


def test_opponent_effects_are_regularized_and_empty_validation_never_promotes():
    from cbv.analysis.opponent_ratings import fit_effects,predict,evaluate_ratings
    history=[dict(team='A',opponent='B',k=6,n=10),dict(team='B',opponent='A',k=4,n=10)]
    fitted=fit_effects(history)
    assert .5<predict(fitted,'A','B')<.6
    assert .4<predict(fitted,'B','A')<.5
    result=evaluate_ratings([],[])
    assert all(not r['improved'] and not r['ratings'] for r in result.values())


def test_opponent_adjustment_uses_previous_days_and_future_does_not_change_past():
    from datetime import date,timedelta
    from cbv.analysis.opponent_ratings import evaluate_ratings
    matches=[dict(match_id=i,date=(date(2026,1,1)+timedelta(days=i//2)).isoformat(),home_team='A',away_team='B',validation_status='VALID') for i in range(24)]
    records=[]
    for m in matches:
        for team,k in [('A',6),('B',4)]:records.append(dict(match_id=m['match_id'],team=team,sideout_points=k,sideout_receptions=10,breakpoint_points=10-k,breakpoint_serves=10))
    result=evaluate_ratings(matches,records)['so']
    dates={m['match_id']:m['date'] for m in matches}
    assert result['predictions']
    assert all(p['trained_through']<dates[p['match_id']] for p in result['predictions'])
    assert result['candidate']['matches']==result['baseline']['matches']
    changed=[dict(r,sideout_points=10-r['sideout_points']) if r['match_id']>=22 else r for r in records]
    after=evaluate_ratings(matches,changed)['so']
    assert [p for p in after['predictions'] if p['match_id']<22]==[p for p in result['predictions'] if p['match_id']<22]
