"""Strict import boundary for original structured feeds; no vendor endpoint guessed.

The live VolleyStation widget is blocked. Until its schema is verifiable, only
an explicit normalized-v1 envelope is supported. Unknown schemas fail closed.
"""
from cbv.reconstruction.rallies import ReconstructionError


def parse_play_by_play(document,match_id):
    if document.get('schema')!='cbv-normalized-pbp-v1' or document.get('match_id')!=match_id:
        raise ReconstructionError('Schema ou identidade do ponto a ponto não confirmado')
    result=[];previous={}
    for original in document.get('events',[]):
        row=dict(original);number=row['set_number'];last=previous.get(number)
        if row['rally_number']!=(last['rally_number']+1 if last else 1):
            raise ReconstructionError('Lacuna ou duplicação de rally')
        before=(row['score_home_before'],row['score_away_before']);after=(row['score_home_after'],row['score_away_after'])
        if last and before!=(last['score_home_after'],last['score_away_after']):
            raise ReconstructionError('Descontinuidade no placar')
        if not last and before!=(0,0):raise ReconstructionError('Set não começa em 0–0')
        delta=(after[0]-before[0],after[1]-before[1])
        if delta not in ((1,0),(0,1)):raise ReconstructionError('Evento não representa um ponto')
        winner='home' if delta==(1,0) else 'away';server=row.get('serving_side')
        if server not in ('home','away'):raise ReconstructionError('Sacador desconhecido')
        if last and server!=last['winner_side']:raise ReconstructionError('Troca de saque incompatível')
        row.update(match_id=match_id,winner_side=winner,receiving_side='away' if server=='home' else 'home',
            rally_id=f'{match_id}:{number}:{row["rally_number"]}',is_breakpoint=winner==server,is_sideout=winner!=server,
            timestamp=row.get('timestamp'),raw_event=dict(original),metric_class='OBSERVADO',source_type='STRUCTURED_PLAY_BY_PLAY')
        result.append(row);previous[number]=row
    if not result:raise ReconstructionError('Ponto a ponto vazio')
    return result
