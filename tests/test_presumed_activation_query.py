import pytest
from cbv.analysis.presumed_activation_query import activation_from_distributions


def test_activation_query_selects_rotation_and_phase_and_preserves_structural_zero():
    distributions=[{
        'position':3,
        'model_version':'lineup-ecological-bayes-v2',
        'metric_class':'EXPERIMENTAL',
        'availability_rallies':80,
        'source_match_count':7,
        'pass_condition_effect':{'support_games':7,'method':'bayesian_ridge_ecological_mixture'},
        'limitation':'latent',
        'pass_scenarios':{
            'positive':{'identified':True,'support_games':7,'distribution':[
                {'name':'A','zone':3,'probability':0.6,'structural_zero':False},
                {'name':'L','zone':6,'probability':0.0,'structural_zero':True},
                {'name':'B','zone':4,'probability':0.4,'structural_zero':False},
            ]},
            'negative':{'identified':True,'support_games':7,'distribution':[
                {'name':'A','zone':3,'probability':0.2,'structural_zero':False},
                {'name':'L','zone':6,'probability':0.0,'structural_zero':True},
                {'name':'B','zone':4,'probability':0.8,'structural_zero':False},
            ]},
        },
    }]
    result=activation_from_distributions(distributions,'P3','negative',team='A',cohort={'season':'2026-2027'})
    assert result['rotation']=='P3'
    assert result['pass_quality']=='negative'
    assert result['distribution'][0]['player_name']=='B'
    assert result['distribution'][0]['probability_pct']==pytest.approx(80)
    libero=next(x for x in result['distribution'] if x['player_name']=='L')
    assert libero['structural_zero'] is True
    assert libero['probability_pct']==0


def test_activation_query_rejects_unknown_phase_or_missing_rotation():
    assert activation_from_distributions([], 'P1', 'positive', team='A') is None
    with pytest.raises(ValueError):
        activation_from_distributions([{'position':1,'pass_scenarios':{}}], 'P1', 'A', team='A')
