from datetime import date
import json
from pathlib import Path
import duckdb
import pytest
from cbv.seasons import source_season,default_match_season,assign_source_matches,edition_status
from cbv.analysis.scouting import aggregate_cohort


def test_official_edition_identity_does_not_guess_from_dates():
    assert source_season('<header>Temporada 26/27</header>')=='2026-2027'
    assert source_season('<h1>Temporada 2025/2026</h1>',expected='2025-2026')=='2025-2026'
    with pytest.raises(ValueError):source_season('<h1>Superliga</h1>')
    with pytest.raises(ValueError):source_season('Temporada 26/27',expected='2025-2026')
    with pytest.raises(ValueError):source_season('Temporada 26/27 Temporada 25/26')
    assert default_match_season('SUPERLIGA',date(2026,10,17)) is None
    assert default_match_season('CBS',date(2026,10,17))=='2026'
    assert edition_status('2025-2026','2026-2027')=='COMPLETED'


def test_verified_source_corrects_only_listed_ids_with_audit():
    c=duckdb.connect(':memory:');c.execute(Path('cbv/database/schema.sql').read_text())
    c.execute("INSERT INTO matches(match_id,competition,category,gender,season,home_team,away_team) VALUES (1,'SUPERLIGA','A','feminino','2025-2026','A','B'),(2,'SUPERLIGA','A','feminino','2025-2026','A','B')")
    meta=dict(competition='SUPERLIGA',category='A',gender='feminino',season='2026-2027')
    assert assign_source_matches(c,[1],meta,'https://cbv.com.br/edition','abc')==[1]
    assert c.execute('select season from matches order by match_id').fetchall()==[('2026-2027',),('2025-2026',)]
    assert c.execute('select previous_season,season,sha256 from season_assignments').fetchone()==('2025-2026','2026-2027','abc')
    assert assign_source_matches(c,[1],meta,'https://cbv.com.br/edition','abc')==[]
    with pytest.raises(ValueError):assign_source_matches(c,[2],dict(meta,gender='masculino'),'url','hash')


def test_calendar_only_edition_has_teams_without_borrowed_statistics():
    cohort=aggregate_cohort([],[],[],registered_teams=['A','B'])
    assert {t['team'] for t in cohort['teams']}=={'A','B'}
    assert all(t['games']==0 and t['metrics']['so']['value'] is None for t in cohort['teams'])
    assert cohort['metrics']['so']['value'] is None


def test_automatic_forecast_never_falls_back_to_previous_edition(monkeypatch):
    import cbv.analysis.predictions as p
    old=dict(competition='SUPERLIGA',category='A',gender='feminino',season='2025-2026',teams=[dict(team='A'),dict(team='B')],model_matchups=[dict(team_a='A',team_b='B',probability_a=.7)])
    current=dict(old,season='2026-2027',model_matchups=[])
    monkeypatch.setattr(p,'_cohorts',lambda:[current,old])
    assert p.predict_matchup('A','B') is None


def test_dossier_does_not_mix_editions_or_fallback(monkeypatch,tmp_path):
    from cbv.database.repository import DatabaseRepository
    import cbv.analysis.tactics as tactics
    repo=DatabaseRepository(tmp_path/'test.duckdb');monkeypatch.setattr(tactics,'default_repo',repo)
    with repo.get_connection() as c:
        for mid,season,points in [(1,'2025-2026',90),(2,'2026-2027',4)]:
            c.execute("INSERT INTO matches(match_id,competition,gender,season,home_team,away_team,home_sets,away_sets) VALUES (?,'SUPERLIGA','feminino',?,'A','B',3,0)",[mid,season])
            c.execute('INSERT INTO team_tactical_stats(match_id,team,sideout_points,sideout_receptions,breakpoint_points,breakpoint_serves) VALUES (?,?,?,?,?,?)',[mid,'A',points,100,10,100])
    tactics.get_team_tactical_dossier.cache_clear()
    result=tactics.get_team_tactical_dossier('A','2026-2027')
    assert result['totals']['so_pct']==4
    assert result['record']['prior_weight_pct']==0
    assert tactics.get_team_tactical_dossier('A','2027-2028') is None
    tactics.get_team_tactical_dossier.cache_clear();repo._conn.close()


def test_legacy_rankings_and_tactical_exports_keep_editions_separate(monkeypatch,tmp_path):
    from cbv.database.repository import DatabaseRepository
    import cbv.analysis.tactics as tactics
    import cbv.analysis.rankings as rankings
    repo=DatabaseRepository(tmp_path/'rankings.duckdb')
    monkeypatch.setattr(tactics,'default_repo',repo);monkeypatch.setattr(rankings,'default_repo',repo)
    with repo.get_connection() as c:
        for mid,season,points in [(1,'2025-2026',90),(2,'2026-2027',4)]:
            c.execute("INSERT INTO matches(match_id,competition,category,gender,season,home_team,away_team,validation_status) VALUES (?,'SUPERLIGA','A','feminino',?,'A','B','VALID')",[mid,season])
            c.execute('INSERT INTO team_tactical_stats(match_id,team,sideout_points,sideout_receptions) VALUES (?,?,?,100)',[mid,'A',points])
            c.execute("INSERT INTO player_match_stats(match_id,team,player_number,player_name,points_total,attack_attempts,attack_points) VALUES (?,'A',9,'Atleta',?,100,?)",[mid,points,points])
    stats=rankings.get_aggregated_player_stats()
    assert {r['season']:r['total_points'] for r in stats}=={'2025-2026':90,'2026-2027':4}
    summary=tactics.get_competition_tactical_summary()
    assert dict(zip(summary['sideout_breakpoint'].season,summary['sideout_breakpoint'].so_pct))=={'2025-2026':90,'2026-2027':4}
    assert summary['offensive_usage'].usage_pct.tolist()==[100,100]
    repo._conn.close()
