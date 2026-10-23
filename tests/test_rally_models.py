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
