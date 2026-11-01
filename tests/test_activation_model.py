import unittest
from cbv.analysis.activation_model import team_season_id, predict, evaluate, calibrate_strength


def event(match, day, target, season='2026', rotation='R2', quality='A', setter='7'):
    return dict(match_id=match, date=day, team='Minas', category='U19', gender='F', season=season,
                target=target, rotation=rotation, pass_quality=quality, setter=setter)


class ActivationModelTests(unittest.TestCase):
    def test_complete_identity_required(self):
        self.assertIsNone(team_season_id('Minas', None, 'F', '2026'))
        self.assertNotEqual(team_season_id('Minas','U19','F','2025'), team_season_id('Minas','U19','F','2026'))
        self.assertNotEqual(team_season_id('Minas','U17','F','2026'), team_season_id('Minas','U19','F','2026'))

    def test_empty_or_single_option_unavailable(self):
        self.assertIsNone(predict([], 'Minas', 'U19', 'F', '2026'))
        self.assertIsNone(predict([event(1,'2026-01-01','A')], 'Minas', 'U19', 'F', '2026'))

    def test_season_isolation_and_regularization(self):
        old=[event(1,'2025-01-01','B',season='2025') for _ in range(100)]
        history=[event(2,'2026-01-01','A'),event(2,'2026-01-01','B',rotation='R1'),event(2,'2026-01-01','B',rotation='R1')]
        base=predict(history,'Minas','U19','F','2026',rotation='R2',pass_quality='A',setter='7')
        with_old=predict(old+history,'Minas','U19','F','2026',rotation='R2',pass_quality='A',setter='7')
        self.assertEqual(base,with_old)
        self.assertGreater(base['probabilities']['B'],0)
        self.assertLess(base['probabilities']['A'],1)
        self.assertEqual(base['context_count'],1)
        broad=predict(history,'Minas','U19','F','2026')
        self.assertGreater(base['probabilities']['A'], broad['probabilities']['A'])

    def test_prior_calibration_requires_evaluable_history(self):
        self.assertIsNone(calibrate_strength([]))
        rows=[event(1,'2026-01-01','A'),event(1,'2026-01-01','B'),event(2,'2026-01-02','A')]
        result=calibrate_strength(rows, strengths=(0.5, 2.0))
        self.assertIn(result['strength'], (0.5, 2.0))
        self.assertEqual(result['predicted'], 1)

    def test_live_update_and_evaluation_coverage(self):
        history=[event(1,'2026-01-01','A'),event(1,'2026-01-01','B')]
        live=[event(2,'2026-01-02','A') for _ in range(3)]
        p=predict(history,'Minas','U19','F','2026',rotation='R2',pass_quality='A',setter='7',live=live)
        self.assertGreater(p['probabilities']['A'],p['historical_probabilities']['A'])
        self.assertEqual(p['live_count'],3)
        score=evaluate(history+live)
        self.assertEqual(score['predicted'],3)
        self.assertEqual(score['skipped'],2)
        self.assertIn('brier',score)
        self.assertIn('calibration',score)

if __name__ == '__main__': unittest.main()
