"""Reconstruct registered positions, actual libero presence and source-bounded lineups."""
import hashlib
import json
from cbv.reconstruction.rallies import rotation_after_sideout


def apply_positions(rallies,sheet,events,team_map,setters,libero=None):
    warnings=[];segments=[]
    for panel in sheet['sets']:
        number=panel['set_number'];rows=[r for r in rallies if r['set_number']==number]
        groups={team_map[g['team_letter']]:g for g in panel['teams']}
        starts={(r['score_home_before'],r['score_away_before']):i for i,r in enumerate(rows)}
        if rows:
            starts[(rows[-1]['score_home_after'],rows[-1]['score_away_after'])]=len(rows)
        setter_positions={};registered={};substitutions={};libero_intervals={}
        for side in ('home','away'):
            group=groups[side];registered[side]=list(group['initial'])
            marker=setters.get(side,{}).get(number)
            if marker and marker['player'] in group['initial'] and group['initial'].index(marker['player'])+1==marker['position']:
                setter_positions[side]=marker['position']
            else:
                setter_positions[side]=None
                warnings.append(f'Set {number} {side}: marcador de levantador ausente ou divergente')
            substitutions[side]={}
            for event in events:
                if event['set_number']!=number or event['team_side']!=side:continue
                if event['kind']=='SUBSTITUTION':
                    index=starts.get((event['score_home'],event['score_away']))
                    if index is None:
                        warnings.append('Substituição com placar não encontrado');continue
                    substitutions[side].setdefault(index,[]).append(event)
            libero_intervals[side]=[]
            if libero:
                for interval in libero['intervals']:
                    if interval['set_number']!=number or team_map.get(interval['team_letter'])!=side:continue
                    def index_of(score):
                        if score is None:return len(rows)
                        home,away=score if side=='home' else score[::-1]
                        return starts.get((home,away))
                    start,end=index_of(interval['start_score']),index_of(interval['end_score'])
                    if start is None or end is None or end<start:
                        warnings.append('Troca de líbero com placar não reconciliado');continue
                    libero_intervals[side].append(dict(interval,start=start,end=end))
        last_lineup={side:None for side in ('home','away')}
        for i,row in enumerate(rows):
            for side in ('home','away'):
                for event in substitutions[side].get(i,[]):
                    slot=event['slot']
                    if registered[side][slot]!=event['player_out']:
                        warnings.append('Substituição incompatível com formação registrada')
                        registered[side][slot]=None
                    else:
                        registered[side][slot]=event['player_in']
                relative=row[side+'_relative_rotation']
                rotation=setter_positions[side]
                actual=((rotation+relative-2)%6)+1 if rotation is not None else None
                row[side+'_rotation']=actual;row[side+'_setter_position']=actual
                row[side+'_rotation_source']='RECONSTRUCTED_FROM_OBSERVED_SETTER' if actual else 'UNKNOWN'
                row[side+'_rotation_confidence']='RECONSTRUCTED_HIGH' if actual else 'UNKNOWN'
                active=list(registered[side]);complete=bool(libero and libero.get('complete'))
                for interval in libero_intervals[side]:
                    if interval['start']<=i<interval['end']:
                        if interval['player_out'] in active:
                            active[active.index(interval['player_out'])]=interval['libero']
                        else:
                            complete=False;warnings.append('Líbero substitui atleta ausente da formação registrada')
                # Slot I starts in zone 1. Both slot and setter move only after a side-out.
                zones=[None]*6
                for slot,player in enumerate(active):
                    position=((slot+relative-1)%6)+1
                    zones[position-1]=player
                complete=complete and len(set(active))==6 and None not in active
                row[side+'_lineup']=zones
                row[side+'_lineup_confidence']='RECONSTRUCTED_HIGH' if complete else 'RECONSTRUCTED_PARTIAL'
                identity=json.dumps([side,number,sorted(p for p in active if p is not None),actual,complete])
                key=hashlib.sha256(identity.encode()).hexdigest()[:20]
                row[side+'_lineup_id']=key
                if last_lineup[side] is None or last_lineup[side]['lineup_id']!=key:
                    segment=dict(lineup_id=key,team_side=side,set_number=number,start_rally=row['rally_number'],end_rally=row['rally_number'],
                        players=zones,setter=groups[side]['initial'][setter_positions[side]-1] if setter_positions[side] else None,
                        rotation=actual,confidence=row[side+'_lineup_confidence'],source='SCORESHEET+LIBERO_REPORT' if complete else 'SCORESHEET_REGISTERED')
                    segments.append(segment);last_lineup[side]=segment
                else:
                    last_lineup[side]['end_rally']=row['rally_number']
            row['rotation_source']='RECONSTRUCTED_HIGH' if row['home_rotation'] and row['away_rotation'] else 'RECONSTRUCTED_PARTIAL' if row['home_rotation'] or row['away_rotation'] else 'UNKNOWN'
            row['rotation_confidence']=row['rotation_source']
    return segments,sorted(set(warnings))
