from cbv.analysis.presumed_distribution import build_distribution, calibrate


def row(match, team, name, n):
    return dict(match_id=match, team=team, player_name=name, is_libero=False, attack_attempts=n)


def test_team_season_isolation_and_smoothed_probabilities():
    matches=[dict(match_id=1,date='2026-01-01', competition='CBS',category='U19',gender='F',season='2026'),dict(match_id=2,date='2026-01-01', competition='CBS',category='U19',gender='M',season='2026'),dict(match_id=3,date='2025-01-01',competition='CBS',category='U19',gender='F',season='2025')]
    players=[row(1,'Minas','Ana',3),row(1,'Minas','Bia',1),row(2,'Minas','Ana',1000),row(3,'Minas','Ana',1000)]
    result=build_distribution(matches,players,('CBS','U19','F','2026'),'Minas',1)
    assert result['attempts']==4
    assert result['distribution'][0]['probability']==.7
    assert result['distribution'][1]['probability']==.3
    assert result['conditional_available'] is False


def test_unidentified_cohort_cannot_leak_and_one_attacker_is_not_certain():
    matches=[dict(match_id=1,date='2026-01-01',competition='CBS',category=None,gender='F',season='2026')]
    assert build_distribution(matches,[row(1,'Minas','Ana',3)],('CBS',None,'F','2026'),'Minas',1) is None
    matches[0]['category']='U19'
    assert build_distribution(matches,[row(1,'Minas','Ana',3)],('CBS','U19','F','2026'),'Minas',1) is None


def test_calibration_uses_only_prior_games_and_reports_coverage():
    matches=[dict(match_id=i,date=d,competition='CBS',category='U19',gender='F',season='2026') for i,d in [(1,'2026-01-01'),(2,'2026-01-02')]]
    players=[row(1,'Minas','A',3),row(1,'Minas','B',2),row(2,'Minas','A',4),row(2,'Minas','B',1),row(2,'Minas','C',2)]
    result=calibrate(matches,players,('CBS','U19','F','2026'))
    assert result['evaluated_attempts']==5
    assert result['unseen_attempts']==7
    assert result['method']=='chronological_log_loss'


def test_same_day_never_trains_another_match():
    matches=[dict(match_id=i,date='2026-01-01',competition='CBS',category='U19',gender='F',season='2026') for i in (1,2)]
    players=[row(1,'Minas','A',50),row(1,'Minas','B',50),row(2,'Minas','A',50),row(2,'Minas','B',50)]
    result=calibrate(matches,players,('CBS','U19','F','2026'))
    assert result['evaluated_attempts']==0
    assert not result['calibrated']
