import pytest
from cbv.analysis.volume_distribution import estimate_distributions


def test_volume_prior_is_scoped_normalized_and_never_invents_pass_condition():
    names=['a','b','c','d','e','libero'];row=dict(match_id=1,home_team='A',away_team='B',home_rotation=1,home_lineup_confidence='RECONSTRUCTED_HIGH',home_lineup_names=names,home_lineup=[1,2,3,4,5,6])
    players=[dict(match_id=1,team='A',player_name=name,is_libero=name=='libero',attack_attempts=20 if name in ('a','b') else 0) for name in names]
    players.append(dict(match_id=2,team='B',player_name='a',is_libero=False,attack_attempts=1000))
    result=estimate_distributions([row],players,'A')[0]
    assert sum(p['weight'] for p in result['distribution'])==pytest.approx(1)
    assert result['entropy']==pytest.approx(1)
    assert result['pass_condition_effect'] is None
    assert result['metric_class']=='EXPERIMENTAL'
    assert not estimate_distributions([dict(row,home_lineup_confidence='RECONSTRUCTED_PARTIAL')],players,'A')
