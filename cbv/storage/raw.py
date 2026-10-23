"""Atomic immutable-byte snapshots and per-match provenance, independent of DuckDB."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os

SOURCE_VERSION = 'atlas-source-1.0'


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def digest(content):
    return hashlib.sha256(content).hexdigest()


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+f'.{os.getpid()}.tmp')
    temporary.write_bytes(content)
    os.replace(temporary, path)


class RawStore:
    def __init__(self, root, match_id):
        self.root = Path(root)/str(int(match_id))
        self.match_id = int(match_id)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root/'manifest.json'
        self.manifest = json.loads(self.manifest_path.read_text()) if self.manifest_path.exists() else dict(match_id=self.match_id,sources={})

    def _save(self):
        atomic_write(self.manifest_path,json.dumps(self.manifest,ensure_ascii=False,indent=2,allow_nan=False).encode())

    def cached(self, kind):
        entry = self.manifest['sources'].get(kind)
        if not entry or entry['status']!='AVAILABLE':
            return None
        path = self.root/entry['filename']
        if path.exists() and digest(path.read_bytes())==entry['sha256']:
            return path
        self.failure(kind,entry.get('source_url'),'CORRUPT','Snapshot ausente ou hash divergente')
        return None

    def put(self, kind, content, url, filename, content_type, fetched_at=None, legacy=False):
        old = self.manifest['sources'].get(kind)
        sha = digest(content)
        path = self.root/filename
        if not path.exists() or digest(path.read_bytes())!=sha:
            # Preserve previous bytes before replacing a changed upstream source.
            if old and path.exists() and old.get('sha256')!=sha:
                previous = self.root/'versions'/f"{kind}-{digest(path.read_bytes())}{path.suffix}"
                if not previous.exists():
                    atomic_write(previous,path.read_bytes())
            atomic_write(path,content)
        if legacy and old and old.get('sha256')==sha:
            fetched_at=old.get('fetched_at')
            legacy=old.get('legacy_cache',False)
        self.manifest['sources'][kind] = dict(match_id=self.match_id,source_url=url,
            fetched_at=fetched_at,stored_at=utcnow(),sha256=sha,content_type=content_type,
            parser_version=SOURCE_VERSION,status='AVAILABLE',filename=filename,legacy_cache=legacy)
        self._save()
        return path

    def failure(self,kind,url,status,reason,http_status=None):
        previous=self.manifest['sources'].get(kind)
        attempt=dict(match_id=self.match_id,source_url=url,attempted_at=utcnow(),
            status=status,error=str(reason)[:600],http_status=http_status,parser_version=SOURCE_VERSION,
            fetched_at=None,sha256=None,content_type=None)
        # A transient error never destroys the last valid snapshot.
        if previous and previous.get('status')=='AVAILABLE' and status!='CORRUPT':
            previous['last_failed_attempt']=attempt
        else:
            self.manifest['sources'][kind]=attempt
        self._save()
