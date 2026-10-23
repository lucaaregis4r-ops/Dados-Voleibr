"""Resumable rate-limited archive, with a staged historical reconstruction."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import shutil
import os
import tempfile
import json
import duckdb
from cbv.scraper.sources import SourceCollector,RequestGate
from cbv.reconstruction.store import rebuild_all,validate_official


def _run_backfill(db_path,raw_root,competition=None,season=None,limit=None,workers=3,interval=.6,collect=True):
    db_path=Path(db_path);raw_root=Path(raw_root)
    # Read-only inventory is closed before HTTP workers or a staged writer start.
    with duckdb.connect(str(db_path),read_only=True) as conn:
        sql='SELECT match_id FROM matches WHERE 1=1';args=[]
        if competition:sql+=' AND lower(competition)=lower(?)';args.append(competition)
        if season:sql+=' AND season=?';args.append(season)
        sql+=' ORDER BY match_id DESC'
        if limit:sql+=' LIMIT ?';args.append(limit)
        ids=[r[0] for r in conn.execute(sql,args).fetchall()]
    from cbv.pipeline import quality_gate,compact_database
    minimum_matches=quality_gate(db_path)
    gate=RequestGate(interval);failures=[]
    if collect:
        def one(mid):return SourceCollector(raw_root,raw_root.parent,gate=gate).collect(mid)
        with ThreadPoolExecutor(max_workers=max(1,min(workers,4))) as pool:
            pending={pool.submit(one,mid):mid for mid in ids}
            for future in as_completed(pending):
                try:future.result()
                except Exception as exc:failures.append(dict(match_id=pending[future],error=str(exc)))
    with tempfile.TemporaryDirectory(prefix='.atlas-backfill-',dir=db_path.parent) as directory:
        stage=Path(directory)/'cbv.duckdb';shutil.copy2(db_path,stage)
        with duckdb.connect(str(stage)) as conn:
            summary=rebuild_all(conn,raw_root,competition,season,limit)
            validate_official(conn)
            errors=conn.execute('SELECT count(*) FROM rallies r LEFT JOIN matches m USING(match_id) WHERE m.match_id IS NULL').fetchone()[0]
            if errors:raise RuntimeError('Rallies órfãos: produção preservada')
            conn.execute('CHECKPOINT')
        compact_database(stage)
        quality_gate(stage,minimum_matches)
        backup=db_path.with_suffix('.last-valid.duckdb');shutil.copy2(db_path,backup)
        os.replace(stage,db_path)
    return dict(discovered=len(ids),reconstruction=summary,source_failures=failures)


def run_backfill(db_path,raw_root,competition=None,season=None,limit=None,workers=3,interval=.6,collect=True):
    from cbv.pipeline import publication_lock
    with publication_lock(Path(db_path).parent):
        return _run_backfill(db_path,raw_root,competition,season,limit,workers,interval,collect)
