from cbv.analysis.atlas import rate,serve_runs,summarize_team


def test_denominators_and_empty_are_explicit():
    rows=[dict(match_id=1,serving_side='home',winner_side=w) for w in ['home','home','away']]
    assert rate(rows,'home',True)['value']==200/3
    assert rate(rows,'home',False)['value'] is None
    assert rate(rows,'home',False)['n']==0


def test_completed_and_censored_service_turns_separated():
    rows=[dict(match_id=1,set_number=1,rally_number=i,serving_side='home',winner_side=w,home_rotation=1) for i,w in enumerate(['home','home','away'],1)]
    rows.append(dict(match_id=1,set_number=2,rally_number=1,serving_side='home',winner_side='home',home_rotation=1))
    result=serve_runs(rows,'home')
    assert result['mean']==2 and result['censored']==1 and result['n']==1
    assert result['survival'][1]['value']==1


def test_unknown_rotations_do_not_become_p1_or_reliable_lineups():
    rows=[dict(match_id=1,set_number=1,rally_number=1,home_team='A',away_team='B',serving_side='home',winner_side='away',home_rotation=None,away_rotation=None)]
    result=summarize_team(rows,'A')
    assert result['coverage']['rallies']==1
    assert result['coverage']['rotation_rallies']==0
    assert all(r['points']['n']==0 for r in result['matrix'])
    assert not result['on_off']
