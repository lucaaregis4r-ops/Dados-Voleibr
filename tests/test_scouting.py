import pytest
from cbv.analysis.scouting import wilson,metric_values,eb_prior,aggregate_cohort


def test_wilson_reference_and_boundaries():
    assert wilson(50,100)==pytest.approx([40.383153,59.616847],abs=1e-5)
    assert wilson(0,0) is None
    assert wilson(11,10) is None
    assert wilson(0,10)[0]==pytest.approx(0)
    assert wilson(10,10)[1]==pytest.approx(100)


def test_weighted_counts_missing_data_and_efficiency():
    rows=[dict(attack_attempts=10,attack_points=6,attack_errors=1,attack_blocked=2,sideout_receptions=10,sideout_points=6),dict(attack_attempts=90,attack_points=36,attack_errors=None,attack_blocked=5,sideout_receptions=90,sideout_points=45)]
    m=metric_values(rows)
    assert m['so']['value']==51
    assert m['kill']['value']==42
    assert m['eff']['value']==30
    assert m['eff']['n']==10 # Missing error is not silently treated as zero.
    assert m['eff']['ci'] is None
    assert m['positive']['value'] is None


def test_empirical_prior_shrinks_small_sample():
    a,b=eb_prior([(1,2),(50,100),(70,100),(40,100)])
    assert 1<(1+a)/(2+a+b)*2
    assert a>0 and b>0


def test_rounded_reception_has_no_fabricated_binomial_interval():
    from cbv.analysis.scouting import enrich_record
    m=metric_values([enrich_record(dict(reception_attempts=17,reception_positive_pct=53))])['positive']
    assert m['value']==pytest.approx(53)
    assert m['approximate']
    assert m['ci'] is None
