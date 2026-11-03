import pytest
from cbv.analysis.volume_distribution import estimate_distributions


def _row(mid, rotation, lineup):
    return dict(
        match_id=mid,
        home_team='A',
        away_team='B',
        serving_side='away',
        home_rotation=rotation,
        home_lineup_confidence='RECONSTRUCTED_HIGH',
        home_lineup_names=lineup,
        home_lineup=[1,2,3,4,5,6],
    )


def _player(mid, name, attacks, libero=False):
    return dict(match_id=mid, team='A', player_name=name, is_libero=libero, attack_attempts=attacks)


def _tactical(mid, pos, neg, trans=0):
    return dict(match_id=mid, team='A', pos_rec_att_attempts=pos, neg_rec_att_attempts=neg, trans_att_attempts=trans)


def test_aggregate_variation_alone_does_not_identify_pass_effect():
    lineup=['middle','wing','opp','setter','oh2','libero']
    rows=[]; players=[]; tactical=[]
    for mid, pos, neg, middle, wing in [
        (1,80,20,44,16),(2,75,25,42,18),(3,70,30,40,20),(4,65,35,38,22),
        (5,35,65,20,40),(6,30,70,18,42),(7,25,75,16,44),(8,20,80,14,46),
    ]:
        for _ in range(20):
            rows.append(_row(mid,1,lineup))
        others=100-middle-wing
        players += [
            _player(mid,'middle',middle), _player(mid,'wing',wing),
            _player(mid,'opp',others//2), _player(mid,'oh2',others-others//2),
            _player(mid,'setter',0), _player(mid,'libero',0,True),
        ]
        tactical.append(_tactical(mid,pos,neg))

    result=estimate_distributions(rows,players,'A',tactical=tactical)
    p1=next(r for r in result if r['position']==1)
    assert p1['pass_condition_effect'] is None
    positive={x['name']:x['probability'] for x in p1['pass_scenarios']['positive']['distribution']}
    negative={x['name']:x['probability'] for x in p1['pass_scenarios']['negative']['distribution']}
    assert positive == pytest.approx(negative)
    assert not p1['pass_scenarios']['positive']['identified']
    assert sum(positive.values()) == pytest.approx(1.0)


def test_structural_availability_comes_from_reconstructed_lineup_and_libero_is_zero():
    p1=['middle','wing','opp','setter','oh2','libero']
    p2=['libero','wing','opp','setter','oh2','other']
    rows=[]
    for mid in range(1,7):
        rows += [_row(mid,1,p1) for _ in range(8)]
        rows += [_row(mid,2,p2) for _ in range(12)]
    players=[]; tactical=[]
    for mid in range(1,7):
        players += [
            _player(mid,'middle',15),_player(mid,'wing',30),_player(mid,'opp',25),
            _player(mid,'oh2',20),_player(mid,'other',10),_player(mid,'setter',0),_player(mid,'libero',0,True),
        ]
        tactical.append(_tactical(mid,55 if mid%2 else 35,35 if mid%2 else 55,10))
    result=estimate_distributions(rows,players,'A',tactical=tactical)
    r2=next(r for r in result if r['position']==2)
    names={x['name'] for x in r2['distribution']}
    assert 'middle' not in names
    libero=next(x for x in r2['distribution'] if x['name']=='libero')
    assert libero['weight']==0
    for scenario in r2['pass_scenarios'].values():
        libero_s=next(x for x in scenario['distribution'] if x['name']=='libero')
        assert libero_s['probability']==0


def test_insufficient_phase_variation_falls_back_to_rotation_prior():
    lineup=['a','b','c','d','e','libero']
    rows=[];players=[];tactical=[]
    for mid in range(1,5):
        rows += [_row(mid,1,lineup) for _ in range(10)]
        players += [_player(mid,'a',30),_player(mid,'b',20),_player(mid,'c',20),_player(mid,'d',15),_player(mid,'e',15),_player(mid,'libero',0,True)]
        tactical.append(_tactical(mid,50,50))
    result=estimate_distributions(rows,players,'A',tactical=tactical)
    p1=result[0]
    assert p1['pass_condition_effect'] is None
    base={x['name']:x['weight'] for x in p1['distribution']}
    pos={x['name']:x['probability'] for x in p1['pass_scenarios']['positive']['distribution']}
    neg={x['name']:x['probability'] for x in p1['pass_scenarios']['negative']['distribution']}
    assert pos==pytest.approx(base)
    assert neg==pytest.approx(base)


def test_volume_prior_is_scoped_normalized_and_never_invents_pass_condition_without_phase_support():
    names=['a','b','c','d','e','libero']
    row=dict(match_id=1,home_team='A',away_team='B',home_rotation=1,home_lineup_confidence='RECONSTRUCTED_HIGH',home_lineup_names=names,home_lineup=[1,2,3,4,5,6])
    players=[dict(match_id=1,team='A',player_name=name,is_libero=name=='libero',attack_attempts=20 if name in ('a','b') else 0) for name in names]
    players.append(dict(match_id=2,team='B',player_name='a',is_libero=False,attack_attempts=1000))
    result=estimate_distributions([row],players,'A',tactical=[])[0]
    assert sum(p['weight'] for p in result['distribution'])==pytest.approx(1)
    assert result['entropy']==pytest.approx(1)
    assert result['pass_condition_effect'] is None
    assert result['metric_class']=='EXPERIMENTAL'
    assert not estimate_distributions([dict(row,home_lineup_confidence='RECONSTRUCTED_PARTIAL')],players,'A',tactical=[])
