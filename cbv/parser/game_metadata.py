"""Observed Next.js Flight JSON, decoded as JSON only; never execute page scripts."""
import json
from bs4 import BeautifulSoup


def parse_game_metadata(html,match_id):
    candidates=[]
    def visit(node):
        if isinstance(node,dict):
            match=node.get('updatedMatch')
            if isinstance(match,dict) and match.get('ChampionshipMatch_ID')==int(match_id):candidates.append(match)
            for value in node.values():visit(value)
        elif isinstance(node,list):
            for value in node:visit(value)
    prefix='self.__next_f.push('
    for script in BeautifulSoup(html,'lxml').find_all('script'):
        text=script.string or ''
        if not text.startswith(prefix):continue
        try:envelope=json.JSONDecoder().raw_decode(text[len(prefix):])[0]
        except (ValueError,TypeError):continue
        if len(envelope)<2 or not isinstance(envelope[1],str):continue
        for line in envelope[1].splitlines():
            if ':' not in line:continue
            try:visit(json.loads(line.split(':',1)[1]))
            except (ValueError,TypeError):continue
    if not candidates:return None
    keys=['HomeTeam','GuestTeam','WonSetHome','WonSetGuest']+[f'Set{i}{side}' for i in range(1,6) for side in ('Home','Guest')]
    signatures={json.dumps({k:m.get(k) for k in keys},sort_keys=True) for m in candidates}
    if len(signatures)!=1:raise ValueError('Snapshots da página divergem: identidade ou resultado ambíguo')
    m=candidates[0];sets=[]
    for number in range(1,6):
        h,a=m.get(f'Set{number}Home'),m.get(f'Set{number}Guest')
        if isinstance(h,int) and isinstance(a,int) and h+a>0:
            sets.append(dict(set_number=number,home_points=h,away_points=a))
    return dict(match_id=int(match_id),home_team=m.get('HomeTeam'),away_team=m.get('GuestTeam'),home_sets=m.get('WonSetHome'),away_sets=m.get('WonSetGuest'),
        start_time=m.get('MatchDateTime'),hall=None if str(m.get('hall','')).startswith('$') else m.get('hall'),sets=sets,
        source_type='OBSERVED_GAME_PAGE_FLIGHT',parser_version='game-metadata-1.0')
