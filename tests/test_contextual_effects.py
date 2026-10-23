from cbv.analysis.contextual_effects import contextual_effects


def test_partial_presence_never_generates_adjusted_effect():
    result=contextual_effects([dict(own_lineup_confidence='RECONSTRUCTED_PARTIAL')],'A')
    assert not result['accepted'] and not result['effects']
    assert result['candidate']['matches']==0


def test_context_models_only_predict_later_days_and_constant_player_has_no_off_effect(monkeypatch):
    import cbv.analysis.contextual_effects as module
    original_fit,original_predict=module._fit,module._predict;stamps={}
    def fit(rows,players):
        result=original_fit(rows,players);stamps[id(result[1])]=max(r['day'] for r in rows);return result
    def predict(result,row):
        assert stamps[id(result[1])]<row['day']
        return original_predict(result,row)
    monkeypatch.setattr(module,'_fit',fit);monkeypatch.setattr(module,'_predict',predict)
    rows=[]
    for mid in range(8):
        for i in range(10):
            rows.append(dict(match_id=mid,date=f'2026-01-{mid+1:02}',home_team='A',away_team='B',own_lineup_confidence='RECONSTRUCTED_HIGH',
                own_lineup_names=['constant','p2','p3','p4','p5','p6' if mid%2 else 'p7'],own_rotation=1,
                score_home_before=i//2,score_away_before=i//2,set_number=1,rally_number=i+1,serving_side='own',winner_side='own' if i%2 else 'other'))
    result=contextual_effects(rows,'A')
    assert result['candidate']['matches']==result['baseline']['matches']==5
    assert all(f['trained_through']<f['day'] for f in result['folds'])
    assert not any(e['player']=='constant' for e in result['effects'])
    assert result['metric_class']=='EXPERIMENTAL'
