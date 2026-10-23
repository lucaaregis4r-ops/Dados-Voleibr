from copy import deepcopy
import pytest
from cbv.parser.scoresheet import parse_scoresheet,parse_libero_report
from cbv.reconstruction.rallies import rebuild_from_scoresheet,reconcile,rotation_after_sideout,ReconstructionError

SETS=[dict(set_number=1,home_points=19,away_points=25),dict(set_number=2,home_points=25,away_points=19),dict(set_number=3,home_points=13,away_points=15)]


def test_real_scoresheet_and_deciding_panel():
    sheet=parse_scoresheet('tests/fixtures/scoresheet_2590834.pdf',2590834)
    assert sheet['team_names']=={'A':'RIO DE JANEIRO','B':'MINAS GERAIS'}
    assert [s['printed_set'] for s in sheet['sets']]==[1,2,5]
    rallies,events=rebuild_from_scoresheet(sheet,{'A':'home','B':'away'},SETS)
    assert len(rallies)==116
    assert reconcile(rallies,SETS)['status']=='VALID'
    assert rallies[0]['serving_side']=='away'
    assert all(r['metric_class']=='RECONSTRUÍDO' for r in rallies)
    assert all(r['home_rotation'] is None for r in rallies)
    assert any(e['kind']=='SUBSTITUTION' for e in events)
    assert any(e['kind']=='TIMEOUT' for e in events)


def test_rotation_cycle_and_long_service_runs():
    position=1;cycle=[]
    for _ in range(6):
        cycle.append(position);position=rotation_after_sideout(position)
    assert cycle==[1,6,5,4,3,2]
    sheet=parse_scoresheet('tests/fixtures/scoresheet_2590834.pdf',2590834)
    rallies,_=rebuild_from_scoresheet(sheet,{'A':'home','B':'away'},SETS)
    for first,second in zip(rallies,rallies[1:]):
        if first['set_number']!=second['set_number']:continue
        assert second['serving_side']==first['winner_side']
        for side in ('home','away'):
            previous=first[side+'_relative_rotation']
            expected=rotation_after_sideout(previous) if first['is_sideout'] and first['winner_side']==side else previous
            assert second[side+'_relative_rotation']==expected
    assert all(r['away_relative_rotation']==1 for r in rallies[:4])
    assert rallies[44]['serving_side']=='home' # Different first server in set 2.


def test_missing_grid_and_changed_score_fail_closed():
    sheet=parse_scoresheet('tests/fixtures/scoresheet_2590834.pdf',2590834)
    sheet['sets'][0]['teams'][0]['grid_complete']=False
    with pytest.raises(ReconstructionError):rebuild_from_scoresheet(sheet,{'A':'home','B':'away'},SETS)


def test_libero_intervals_are_observed_not_guessed():
    data=parse_libero_report('tests/fixtures/libero_2590834.pdf',2590834)
    assert not data['warnings']
    first=data['intervals'][0]
    assert first['team_letter']=='A'
    assert first['libero']==3
    assert first['player_out']==14
    assert first['start_score']==[0,0]
    assert first['end_score']==[2,8]


def test_report_setter_markers_and_substitutions_preserve_rotation():
    from cbv.parser.scoresheet import parse_setter_markers
    from cbv.reconstruction.lineups import apply_positions
    markers=parse_setter_markers('tests/fixtures/match_2590834.pdf','RIO DE JANEIRO','MINAS GERAIS')
    assert markers['RIO DE JANEIRO'][1]['player']==8
    assert markers['RIO DE JANEIRO'][2]['player']==1
    assert markers['MINAS GERAIS'][1]['position']==2
    sheet=parse_scoresheet('tests/fixtures/scoresheet_2590834.pdf',2590834)
    rallies,events=rebuild_from_scoresheet(sheet,{'A':'home','B':'away'},SETS)
    libero=parse_libero_report('tests/fixtures/libero_2590834.pdf',2590834)
    segments,warnings=apply_positions(rallies,sheet,events,{'A':'home','B':'away'},
        {'home':markers['RIO DE JANEIRO'],'away':markers['MINAS GERAIS']},libero)
    assert rallies[0]['home_rotation']==1
    assert rallies[0]['away_rotation']==2
    assert rallies[0]['home_lineup'][-1]==3 # Observed libero replaces 14 at 0–0.
    assert all(r['home_rotation'] in range(1,7) for r in rallies)
    assert segments
    assert not warnings


def test_structured_feed_rejects_unknown_schema_duplicate_and_server_change():
    from cbv.parser.play_by_play import parse_play_by_play
    doc=dict(schema='cbv-normalized-pbp-v1',match_id=1,events=[dict(set_number=1,rally_number=1,
        score_home_before=0,score_away_before=0,score_home_after=1,score_away_after=0,serving_side='home')])
    assert parse_play_by_play(doc,1)[0]['is_breakpoint']
    with pytest.raises(ReconstructionError):parse_play_by_play(doc,2)
    doc['events'].append(dict(doc['events'][0]))
    with pytest.raises(ReconstructionError):parse_play_by_play(doc,1)


def test_short_and_split_font_accented_team_names_are_not_cross_matched():
    sheet=parse_scoresheet('tests/fixtures/scoresheet_2590824.pdf',2590824)
    assert sheet['team_names']=={'B':'SÃO PAULO','A':'AMAPÁ'}
