"""Isolated staging and quality gates. Never publish a partially parsed database."""
from pathlib import Path
from contextlib import contextmanager
import fcntl
import tempfile
import shutil
import os
import duckdb


@contextmanager
def publication_lock(data_dir):
    path=Path(data_dir)/'.atlas-sync.lock';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Já existe atualização em andamento')
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)


def quality_gate(path,minimum_matches=0):
    with duckdb.connect(str(path),read_only=True) as conn:
        count=conn.execute('SELECT count(*) FROM matches').fetchone()[0]
        if count<minimum_matches:raise RuntimeError('Regressão no inventário de partidas')
        duplicates=conn.execute('SELECT count(*)-count(DISTINCT match_id) FROM matches').fetchone()[0]
        if duplicates:raise RuntimeError('Identidades duplicadas')
        tables={r[0] for r in conn.execute('SHOW TABLES').fetchall()}
        if 'season_assignments' in tables:
            mismatch=conn.execute('SELECT count(*) FROM season_assignments s JOIN matches m USING(match_id) WHERE s.season IS DISTINCT FROM m.season').fetchone()[0]
            if mismatch:raise RuntimeError('Identidade da temporada diverge da fonte oficial')
        if 'validation_reports' in tables:
            invalid=conn.execute('''SELECT count(*) FROM rallies r JOIN validation_reports v USING(match_id)
                WHERE v.status='FAILED' OR (r.home_rotation IS NOT NULL AND r.home_rotation NOT BETWEEN 1 AND 6)
                OR (r.away_rotation IS NOT NULL AND r.away_rotation NOT BETWEEN 1 AND 6)
                OR r.score_home_after+r.score_away_after != r.score_home_before+r.score_away_before+1''').fetchone()[0]
            if invalid:raise RuntimeError('Invariantes de rallies violados')
    return count


def staged_update(root,worker):
    root=Path(root);data=root/'data';production=data/'cbv.duckdb'
    with publication_lock(data):
        # A fresh GitHub runner can start without the cached raw directory. The
        # staging area exposes raw as a symlink, so its real target must exist
        # before cbv.config runs mkdir(..., exist_ok=True) inside the worker.
        (data/'raw').mkdir(parents=True,exist_ok=True)
        old_count=quality_gate(production)
        with tempfile.TemporaryDirectory(prefix='.atlas-daily-',dir=data) as directory:
            stage=Path(directory);stage_data=stage/'data';stage_data.mkdir();shutil.copy2(production,stage_data/'cbv.duckdb')
            (data/'raw').mkdir(parents=True,exist_ok=True)
            (stage_data/'raw').symlink_to((data/'raw').resolve(),target_is_directory=True)
            worker(stage_data,stage)
            compact_database(stage_data/'cbv.duckdb')
            quality_gate(stage_data/'cbv.duckdb',old_count)
            artifacts=[stage/'index.html',stage/'docs/index.html',stage/'exports/dashboard.html',stage/'docs/CADERNO_METODOLOGICO.md']
            if any(not p.exists() or not p.stat().st_size for p in artifacts):raise RuntimeError('Build incompleto: produção preservada')
            if '__SCOUTING_DATA__' in artifacts[0].read_text():raise RuntimeError('Payload ausente no HTML')
            backup=data/'cbv.last-valid.duckdb';shutil.copy2(production,backup)
            # All expensive/fallible operations complete before publication. Preserve
            # previous bytes for rollback if a filesystem operation fails midway.
            targets=[(stage_data/'cbv.duckdb',production)]
            for folder in ('exports','docs'):
                targets.extend((p,root/p.relative_to(stage)) for p in (stage/folder).rglob('*') if p.is_file())
            targets.append((stage/'index.html',root/'index.html'))
            rollback=stage/'rollback';rollback.mkdir();written=[]
            try:
                for index,(source,target) in enumerate(targets):
                    target.parent.mkdir(parents=True,exist_ok=True);prior=rollback/str(index)
                    if target.exists():shutil.copy2(target,prior)
                    temporary=target.with_name(target.name+'.atlas-publish');shutil.copy2(source,temporary);os.replace(temporary,target)
                    written.append((target,prior))
            except Exception:
                for target,prior in reversed(written):
                    if prior.exists():os.replace(prior,target)
                    else:target.unlink(missing_ok=True)
                raise


def compact_database(path):
    """Copy live rows into a fresh DuckDB file; reclaim old reconstruction versions."""
    path=Path(path);temporary=path.with_name(path.stem+'.compact.duckdb');temporary.unlink(missing_ok=True)
    with duckdb.connect(str(path)) as conn:
        original=conn.execute('SELECT current_database()').fetchone()[0]
        literal="'"+str(temporary).replace("'","''")+"'"
        conn.execute(f'ATTACH {literal} AS atlas_compact')
        quoted='"'+original.replace('"','""')+'"'
        conn.execute(f'COPY FROM DATABASE {quoted} TO atlas_compact')
        conn.execute('DETACH atlas_compact');conn.execute('CHECKPOINT')
    quality_gate(temporary)
    os.replace(temporary,path)
