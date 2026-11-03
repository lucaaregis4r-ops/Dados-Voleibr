import unittest
from cbv.analysis.rotation_allocation import allocate_scenarios, disambiguate_players


def make_row(mid, pos, names, jerseys):
    return {'match_id': mid, 'home_team': 'A', 'away_team': 'B',
            'home_rotation': pos, 'home_lineup_names': names,
            'home_lineup': jerseys, 'home_lineup_confidence': 'RECONSTRUCTED_HIGH'}


class RotationAllocationTests(unittest.TestCase):
    def test_match_aggregates_and_exposure_allocate_proportionally(self):
        # In game 1 Ana attacks 80 and Bia 20 with mainly P1 exposure.
        # Game 2 reverses that attack share and is mostly played in P2.
        names=['Ana','Bia','C','D','E','F']; jersey=list(range(1,7))
        rows=[]; players=[]; tactical=[]
        for mid, p1, p2, ana, bia, pos in [(1,8,2,80,20,80),(2,2,8,20,80,20)]:
            rows += [make_row(mid,1,names,jersey)]*p1 + [make_row(mid,2,names,jersey)]*p2
            players += [{'match_id':mid,'team':'A','player_name':n,'player_number':i+1,'attack_attempts':v,'is_libero':False} for i,(n,v) in enumerate(zip(names,[ana,bia,0,0,0,0]))]
            tactical += [{'match_id':mid,'team':'A','pos_rec_att_attempts':pos,'neg_rec_att_attempts':100-pos,'trans_att_attempts':0}]
        out=allocate_scenarios(rows,players,'A',tactical,min_coverage=.8)
        self.assertAlmostEqual(out[1]['all']['Ana'],68)
        self.assertAlmostEqual(out[2]['all']['Ana'],32)
        self.assertGreater(out[1]['positive']['Ana'],out[1]['negative']['Ana'])
        self.assertEqual(out[1]['games'],2)
        self.assertEqual(out[1]['phase_games'],2)

    def test_one_game_phase_composition_is_an_assumption_not_a_learned_effect(self):
        names=['Ana','Bia','C','D','E','F']; jerseys=list(range(1,7))
        rows=[make_row(1,1,names,jerseys)] * 10
        players=[{'match_id':1,'team':'A','player_name':name,'player_number':i+1,'attack_attempts':value}
                 for i,(name,value) in enumerate(zip(names,[80,20,0,0,0,0]))]
        tactical=[{'match_id':1,'team':'A','pos_rec_att_attempts':75,'neg_rec_att_attempts':25,'trans_att_attempts':0}]
        allocation=allocate_scenarios(rows,players,'A',tactical)[1]
        positive=allocation['positive']; negative=allocation['negative']
        self.assertAlmostEqual(positive['Ana']/sum(positive.values()), .8)
        self.assertAlmostEqual(negative['Ana']/sum(negative.values()), .8)

    def test_duplicate_names_are_distinct_by_jersey(self):
        rows=[make_row(1,1,['Miguel','Miguel','C','D','E','F'],[5,10,3,4,7,8])]
        players=[{'match_id':1,'team':'A','player_name':'Miguel','player_number':i,'attack_attempts':v} for i,v in [(5,7),(10,5)]]
        rr,pp=disambiguate_players(rows,players,'A')
        self.assertNotEqual(pp[0]['player_name'],pp[1]['player_name'])
        self.assertEqual(rr[0]['home_lineup_names'][:2],[pp[0]['player_name'],pp[1]['player_name']])

    def test_jersey_change_alone_does_not_split_an_athlete(self):
        players=[{'match_id':mid,'team':'A','player_name':'Ana','player_number':number,'attack_attempts':5}
                 for mid,number in [(1,5),(2,10)]]
        _, adjusted = disambiguate_players([],players,'A')
        self.assertEqual([p['player_name'] for p in adjusted], ['Ana','Ana'])

    def test_missing_lineup_excludes_match_and_does_not_invent_allocation(self):
        names=['A1','B1','C1','D1','E1','F1']; jerseys=list(range(1,7))
        rows=[make_row(1,1,names,jerseys)] + [dict(make_row(1,1,names,jerseys),home_lineup_confidence='LOW')]*9
        players=[{'match_id':1,'team':'A','player_name':'A1','player_number':1,'attack_attempts':5}]
        self.assertEqual(allocate_scenarios(rows,players,'A',[],min_coverage=.8),{})

    def test_missing_tactical_phase_omits_phase_scenarios(self):
        names=['A1','B1','C1','D1','E1','F1']; rows=[make_row(1,1,names,list(range(1,7)))]
        players=[{'match_id':1,'team':'A','player_name':'A1','player_number':1,'attack_attempts':5}]
        out=allocate_scenarios(rows,players,'A',[],min_coverage=.8)
        self.assertEqual(out,{})

if __name__=='__main__': unittest.main()
