import json
from pathlib import Path
import duckdb
from cbv.storage.raw import RawStore
from cbv.reconstruction.store import rebuild_all
from cbv.pipeline import staged_update


def test_rebuild_is_idempotent_and_bad_refresh_preserves_valid_match(tmp_path):
    conn=duckdb.connect(':memory:');conn.execute(Path('cbv/database/schema.sql').read_text())
    conn.execute("INSERT INTO matches(match_id,home_team,away_team,validation_status) VALUES (2590834,'RIO DE JANEIRO','MINAS GERAIS','VALID')")
    for n,h,a in [(1,19,25),(2,25,19),(3,13,15)]:conn.execute('INSERT INTO sets(match_id,set_number,home_points,away_points) VALUES (?,?,?,?)',[2590834,n,h,a])
    raw=tmp_path/'raw';store=RawStore(raw,2590834)
    for kind,file in [('scoresheet','scoresheet_2590834.pdf'),('match_report','match_2590834.pdf'),('libero_report','libero_2590834.pdf')]:
        store.put(kind,Path('tests/fixtures',file).read_bytes(),'https://example.org/'+file,kind+'.pdf','application/pdf')
    for _ in range(2):
        result=rebuild_all(conn,raw)
        assert result=={'VALID':1}
        assert json.loads(conn.execute("SELECT metadata FROM source_snapshots WHERE source_type='scoresheet'").fetchone()[0])['parser_version']=='scoresheet-1.2'
        assert conn.execute('SELECT count(*) FROM rallies').fetchone()[0]==116
    store.put('scoresheet',b'%PDF-not-a-valid-document','https://example.org/scoresheet.pdf','scoresheet.pdf','application/pdf')
    result=rebuild_all(conn,raw)
    assert result=={'FAILED':1}
    assert conn.execute('SELECT count(*) FROM rallies').fetchone()[0]==116
    assert conn.execute('SELECT status FROM validation_reports').fetchone()[0]=='VALID'
    assert conn.execute('SELECT status FROM reconstruction_attempts').fetchone()[0]=='FAILED'
    from cbv.analysis.atlas import load_atlas
    assert not load_atlas(conn)['rows']  # Preserve stored history, exclude failed refresh from models.
    conn.close()


def test_daily_stage_failure_keeps_production_bytes(tmp_path):
    data=tmp_path/'data';data.mkdir();db=data/'cbv.duckdb'
    with duckdb.connect(str(db)) as conn:conn.execute('CREATE TABLE matches(match_id INTEGER); INSERT INTO matches VALUES (1)')
    before=db.read_bytes()
    def broken(stage,publish):
        with duckdb.connect(str(stage/'cbv.duckdb')) as conn:conn.execute('DELETE FROM matches')
        raise ValueError('source parser failed')
    import pytest
    with pytest.raises(ValueError):staged_update(tmp_path,broken)
    assert db.read_bytes()==before
