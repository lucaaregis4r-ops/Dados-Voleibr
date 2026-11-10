"""Import completed CBI Sub-16 final matches from the official CBV pages."""
import re
import hashlib
from bs4 import BeautifulSoup

from cbv.scraper.client import default_client
from cbv.scraper.downloader import download_match_report
from cbv.scraper.game_page import fetch_game_page, extract_game_links
from cbv.parser.match_report import parse_match_report_pdf, save_processed_match
from cbv.database.repository import default_repo


def final_url(gender, season):
    if gender not in ('feminino', 'masculino'):
        raise ValueError('Gênero inválido')
    return f'https://cbv.com.br/volei-de-quadra/cbi/{season}/sub-16/{gender}/fase-final'


def finished_match_ids(html):
    result = []
    for card in BeautifulSoup(html, 'lxml').find_all('article'):
        if not re.search(r'\bEncerrado\b', card.get_text(' ', strip=True), re.I):
            continue
        for link in card.find_all('a', href=True):
            match = re.search(r'/jogo/(\d+)(?:[/?#]|$)', link['href'])
            if match and int(match.group(1)) not in result:
                result.append(int(match.group(1)))
    return result


def sync_cbi_final(gender, season=2026):
    url = final_url(gender, season)
    html = default_client.get(url).text
    ids = finished_match_ids(html)
    from cbv.seasons import register_edition
    with default_repo.get_connection() as conn:
        register_edition(conn, 'CBI', 'sub16', gender, str(season), url,
                         hashlib.sha256(html.encode('utf-8')).hexdigest())
    imported, skipped, pending, failed = [], [], [], []
    for mid in ids:
        try:
            if default_repo.match_exists(mid):
                skipped.append(mid)
                continue
            html, _ = fetch_game_page(mid, force=True)
            report_url = extract_game_links(html).get('match_report_url')
            if not report_url:
                pending.append(mid)
                continue
            path = download_match_report(mid, report_url)
            data = parse_match_report_pdf(path, mid, competition='CBI', category='sub16', gender=gender)
            data.match.season = str(season)
            save_processed_match(data)
            default_repo.save_match_data(data)
            imported.append(mid)
        except Exception as exc:
            failed.append((mid, str(exc)))
    return {'found': ids, 'imported': imported, 'skipped': skipped, 'pending': pending, 'failed': failed}
