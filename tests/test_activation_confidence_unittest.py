import unittest
from cbv.analysis.volume_distribution import estimate_distributions

class ConfidenceTests(unittest.TestCase):
    def test_confidence_distinguishes_formation_support_from_prediction(self):
        names=['a','b','c','d','e','libero']
        row=dict(match_id=1,home_team='A',away_team='B',home_rotation=1,home_lineup_confidence='RECONSTRUCTED_HIGH',home_lineup_names=names,home_lineup=[1,2,3,4,5,6])
        players=[dict(match_id=1,team='A',player_name=n,is_libero=n=='libero',attack_attempts=10 if n!='libero' else 0) for n in names]
        result=estimate_distributions([row],players,'A',tactical=[])[0]
        confidence=result['confidence']
        self.assertIsNone(confidence['prediction_score'])
        self.assertEqual(confidence['status'], 'NOT_VALIDATED')
        self.assertEqual(confidence['lineup_share'], 1)
        self.assertEqual(confidence['lineup_rallies'], 1)

    def test_six_games_cannot_identify_eighteen_parameters(self):
        from cbv.analysis.volume_distribution import _fit_latent_phase_rates
        from collections import Counter
        by_match={m:{'a':40,'b':60} for m in range(1,7)}
        exposure={'match_total':Counter({m:100 for m in range(1,7)}), 'player_rotation':Counter({(m,n,1):100 for m in range(1,7) for n in ['a','b']})}
        tactical={m:{'positive':20 if m%2 else 80,'negative':80 if m%2 else 20,'transition':0} for m in range(1,7)}
        _, diag=_fit_latent_phase_rates(by_match,exposure,tactical,set(),8)
        self.assertFalse(diag['identified'])

if __name__=='__main__': unittest.main()
