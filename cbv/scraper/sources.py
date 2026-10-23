"""Collect only URLs observed on CBV pages; record unavailable/blocked sources honestly."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
import html as html_module
import json
import re
import threading
import time
import requests
from bs4 import BeautifulSoup
from cbv.storage.raw import RawStore, utcnow


class RequestGate:
    def __init__(self, interval=0.6):
        self.interval=interval
        self.lock=threading.Lock()
        self.last=0.0
        self.blocked_widget=None

    def wait(self):
        with self.lock:
            delay=self.interval-(time.monotonic()-self.last)
            if delay>0:
                time.sleep(delay)
            self.last=time.monotonic()


def discover_source_links(html, match_id):
    """No URL guessing: PDF IDs must match the requested game, iframe IDs too."""
    soup=BeautifulSoup(html,'lxml')
    links={}
    for a in soup.find_all('a',href=True):
        url=urljoin('https://cbv.com.br',html_module.unescape(a['href']))
        label=a.get_text(' ',strip=True).lower()
        if not re.search(rf'/matches/{int(match_id)}(?:-|/)',url):
            continue
        if 'scoresheet' in label or 'scoresheet' in url:
            links['scoresheet']=url
        elif 'match report' in label or 'relatório' in label:
            links['match_report']=url
    # The public SSR payload also exposes the optional libero-control PDF.
    for url in re.findall(r'https://[^\s"<>\\]+\.pdf',html_module.unescape(html)):
        if re.search(rf'/matches/{int(match_id)}-',url) and 'libero-report' in url:
            links['libero_report']=url
    for frame in soup.find_all('iframe',src=True):
        url=html_module.unescape(frame['src'])
        if re.search(rf'/play-by-play(?:-old)?/{int(match_id)}(?:\?|$)',url):
            links['play_by_play']=url
    return links


class SourceCollector:
    def __init__(self, raw_root, legacy_root=None, gate=None, timeout=20):
        self.raw_root=Path(raw_root)
        self.legacy_root=Path(legacy_root) if legacy_root else None
        self.gate=gate or RequestGate()
        self.timeout=timeout
        self.session=requests.Session()
        self.session.headers.update({'User-Agent':'VoleibrAtlas/1.0 (public CBV scouting research)'})

    def _get(self,url):
        for attempt in range(3):
            self.gate.wait()
            response=self.session.get(url,timeout=self.timeout)
            if response.status_code not in (429,500,502,503,504) or attempt==2:
                return response
            time.sleep(min(8,2**attempt))

    def collect(self, match_id, force=False, collect_widget=True):
        store=RawStore(self.raw_root,match_id)
        url=f'https://cbv.com.br/jogo/{int(match_id)}'
        page=store.cached('game_page')
        if not page and self.legacy_root:
            old=self.legacy_root/'pages'/f'{match_id}.html'
            if old.exists():
                page=store.put('game_page',old.read_bytes(),url,'game_page.html','text/html',legacy=True)
        if not page or force:
            try:
                response=self._get(url)
                response.raise_for_status()
                if str(match_id) not in response.text:
                    raise ValueError('Página sem o identificador esperado')
                page=store.put('game_page',response.content,url,'game_page.html',response.headers.get('content-type','text/html'),utcnow())
            except Exception as exc:
                store.failure('game_page',url,'FAILED',exc)
                if not page:
                    return store.manifest
        links=discover_source_links(page.read_text(encoding='utf-8'),match_id)
        metadata=dict(match_id=int(match_id),source_url=url,links=links)
        from cbv.parser.game_metadata import parse_game_metadata
        metadata['match']=parse_game_metadata(page.read_text(encoding='utf-8'),match_id)
        (store.root/'game_page.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
        for kind in ('match_report','scoresheet','libero_report','play_by_play'):
            if kind=='play_by_play' and not collect_widget:
                continue
            cached=store.cached(kind)
            if cached and not force:
                continue
            source_url=links.get(kind)
            if not source_url:
                store.failure(kind,None,'UNAVAILABLE','Link não publicado na página da partida')
                continue
            if kind=='match_report' and self.legacy_root and not force:
                old=self.legacy_root/'reports'/f'{match_id}.pdf'
                if old.exists() and old.read_bytes().lstrip().startswith(b'%PDF'):
                    store.put(kind,old.read_bytes(),source_url,'match_report.pdf','application/pdf',legacy=True)
                    continue
            previous=store.manifest['sources'].get(kind,{})
            # Do not hammer a blocked origin once per historical match every day.
            if not force and previous.get('attempted_at') and previous['status'] in ('BLOCKED','UNAVAILABLE'):
                if datetime.fromisoformat(previous['attempted_at'])>datetime.now(timezone.utc)-timedelta(days=1):
                    continue
            if kind=='play_by_play' and self.gate.blocked_widget:
                store.failure(kind,source_url,'DEFERRED_PROVIDER_BLOCK',
                    'Requisição não repetida: provedor bloqueou '+self.gate.blocked_widget)
                continue
            try:
                response=self._get(source_url)
                if response.status_code in (401,403):
                    if kind=='play_by_play':
                        self.gate.blocked_widget=source_url
                    store.failure(kind,source_url,'BLOCKED','Acesso negado pelo provedor; não contornado',response.status_code)
                    continue
                if response.status_code==404:
                    store.failure(kind,source_url,'UNAVAILABLE','Documento não publicado',404)
                    continue
                response.raise_for_status()
                if kind=='play_by_play':
                    if 'json' in response.headers.get('content-type',''):
                        response.json()  # Validate syntax, not an invented event schema.
                        store.put(kind,response.content,source_url,'play_by_play.json','application/json',utcnow())
                    else:
                        # Keep original HTML for audit; adapter requires a confirmed structured feed.
                        store.put('play_by_play_html',response.content,source_url,'play_by_play.html','text/html',utcnow())
                        store.failure(kind,source_url,'UNSUPPORTED','Widget HTML sem contrato JSON confirmado')
                else:
                    if not response.content.lstrip().startswith(b'%PDF'):
                        raise ValueError('Resposta não é PDF')
                    store.put(kind,response.content,source_url,kind+'.pdf','application/pdf',utcnow())
            except Exception as exc:
                store.failure(kind,source_url,'FAILED',exc)
        return store.manifest
