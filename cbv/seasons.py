"""Competition edition identity comes from the official source, never a date cutoff."""
import re
from bs4 import BeautifulSoup


def source_season(html, expected=None):
    text=BeautifulSoup(html,'lxml').get_text(' ',strip=True)
    found=set()
    for start,end in re.findall(r'Temporada\s+(\d{2}(?:\d{2})?)\s*[/–-]\s*(\d{2}(?:\d{2})?)',text,re.I):
        first=int(start)+(2000 if len(start)==2 else 0)
        last=int(end)+(2000 if len(end)==2 else 0)
        if last==first+1:found.add(f'{first}-{last}')
    if len(found)>1:raise ValueError('Identidade de temporada ambígua na página oficial')
    season=next(iter(found),None)
    if expected and season and season!=expected:raise ValueError(f'Temporada oficial {season} diverge da edição solicitada {expected}')
    if not season and not expected:raise ValueError('Página oficial sem identificação da temporada; recorte não será presumido')
    return season or expected


def edition_status(season, current_season):
    if season==current_season:return 'CURRENT'
    if not season:return 'UNKNOWN'
    return 'COMPLETED' if season<current_season else 'UPCOMING'


def default_match_season(competition,match_date):
    # CBS is an annual tournament; Superliga requires explicit edition metadata.
    if competition=='CBS' and match_date:return str(match_date.year)
    return None


def register_edition(conn,competition,category,gender,season,source_url,sha256):
    conn.execute('''CREATE TABLE IF NOT EXISTS competition_editions(competition VARCHAR,category VARCHAR,gender VARCHAR,
        season VARCHAR,source_url VARCHAR,sha256 VARCHAR,verified_at TIMESTAMP,PRIMARY KEY(competition,category,gender))''')
    conn.execute('INSERT OR REPLACE INTO competition_editions VALUES (?,?,?,?,?,?,current_timestamp)',[competition,category,gender,season,source_url,sha256])


def assign_source_matches(conn,match_ids,metadata,source_url,sha256):
    """Correct only identities explicitly present in a verified edition source."""
    conn.execute('''CREATE TABLE IF NOT EXISTS season_assignments(match_id BIGINT PRIMARY KEY,previous_season VARCHAR,
        season VARCHAR,source_url VARCHAR,sha256 VARCHAR,assigned_at TIMESTAMP)''')
    changed=[]
    for mid in sorted(set(match_ids)):
        previous=conn.execute('SELECT competition,category,gender,season FROM matches WHERE match_id=?',[mid]).fetchone()
        if not previous:continue
        if tuple(previous[:3])!=tuple(metadata[k] for k in ('competition','category','gender')):
            raise ValueError(f'Identidade de competição/gênero diverge para {mid}')
        season=metadata['season']
        if previous[3]!=season:
            conn.execute('INSERT OR REPLACE INTO season_assignments VALUES (?,?,?,?,?,current_timestamp)',[mid,previous[3],season,source_url,sha256])
            conn.execute('UPDATE matches SET season=? WHERE match_id=?',[season,mid]);changed.append(mid)
    return changed
