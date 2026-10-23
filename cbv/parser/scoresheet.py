"""VolleyStation digital scoresheets: anchored geometry, explicit coverage, no OCR guesses."""
from pathlib import Path
import re
import pymupdf

PARSER_VERSION='scoresheet-1.2'
ROMAN=('I','II','III','IV','V','VI')


def words(page):
    return [dict(x=(w[0]+w[2])/2,y=(w[1]+w[3])/2,text=w[4],bbox=w[:4]) for w in page.get_text('words')]


def _rows(items,tolerance=1.5):
    result=[]
    for item in sorted(items,key=lambda w:(w['y'],w['x'])):
        if not result or abs(item['y']-result[-1][0]['y'])>tolerance:
            result.append([item])
        else:
            result[-1].append(item)
    return result


def _group(ws,columns,y,unit):
    x0,x1=columns[0]-unit,columns[-1]+unit
    def inside(w):return x0<w['x']<x1
    labels=[w for w in ws if inside(w) and y-2.1*unit<w['y']<y-.3*unit and w['text'] in ('A','B')]
    if len(labels)!=1:
        return None
    letter=labels[0]['text']
    initial=[]
    for x in columns:
        found=[w['text'] for w in ws if abs(w['x']-x)<unit*.7 and abs(w['y']-(y+unit))<unit*.35 and w['text'].isdigit()]
        initial.append(int(found[0]) if len(found)==1 else None)
    if any(n is None for n in initial) or len(set(initial))!=6:
        return None
    cells=[]
    for row in range(4):
        for slot,x in enumerate(columns):
            found=[w['text'] for w in ws if abs(w['x']-(x-unit*.5))<unit*.65 and abs(w['y']-(y+5*unit+row*unit))<unit*.35 and (w['text'].isdigit() or w['text']=='X')]
            cells.append(found[0] if len(found)==1 else None)
    occupied=[i for i,v in enumerate(cells) if v is not None]
    if not occupied:
        return None
    contiguous=all(v is not None for v in cells[:max(occupied)+1])
    first_receiving=cells[0]=='X'
    ends=[int(v) for v in cells if v is not None and v!='X']
    substitutions=[]
    for slot,x in enumerate(columns):
        jersey=[int(w['text']) for w in ws if abs(w['x']-x)<unit*.65 and y+1.5*unit<w['y']<y+2.6*unit and w['text'].isdigit()]
        scores=sorted([w for w in ws if abs(w['x']-x)<unit*.9 and y+2.4*unit<w['y']<y+4.5*unit and re.fullmatch(r'\d+:\d+',w['text'])],key=lambda w:w['y'])
        if scores and len(jersey)==1 and len(scores)<=2:
            for i,score in enumerate(scores):
                own,opponent=map(int,score['text'].split(':'))
                substitutions.append(dict(kind='SUBSTITUTION',team_letter=letter,slot=slot,
                    player_out=initial[slot] if i==0 else jersey[0],player_in=jersey[0] if i==0 else initial[slot],
                    own_score=own,opponent_score=opponent,source='OBSERVED_SCORESHEET'))
        elif scores:
            substitutions.append(dict(kind='UNRESOLVED_SUBSTITUTION',team_letter=letter,slot=slot,raw_scores=[s['text'] for s in scores]))
    # Timeout scores are printed immediately to the right of the service grid.
    timeouts=[dict(kind='TIMEOUT',team_letter=letter,own_score=int(w['text'].split(':')[0]),opponent_score=int(w['text'].split(':')[1]),source='OBSERVED_SCORESHEET')
        for w in ws if x1<w['x']<x1+3.3*unit and y+6.2*unit<w['y']<y+8.5*unit and re.fullmatch(r'\d+:\d+',w['text'])]
    return dict(team_letter=letter,initial=initial,receiving_first=first_receiving,
                service_ends=ends,grid_complete=contiguous,substitutions=substitutions,timeouts=timeouts,
                raw_cells=cells)


def parse_scoresheet(path,match_id):
    doc=pymupdf.open(path)
    if len(doc)!=1:
        raise ValueError('Formato de súmula não suportado: esperado PDF digital de uma página')
    page=doc[0];ws=words(page)
    if 'VOLLEYSTATION' not in page.get_text().upper():
        raise ValueError('Súmula não identificada como VolleyStation digital')
    roman_rows=_rows([w for w in ws if w['text'] in ROMAN])
    panels=[]
    for row_index,row in enumerate(roman_rows):
        row=sorted(row,key=lambda w:w['x'])
        groups=[]
        for i in range(0,len(row),6):
            part=row[i:i+6]
            if [w['text'] for w in part]!=list(ROMAN):
                continue
            columns=[w['x'] for w in part]
            unit=(columns[-1]-columns[0])/10
            group=_group(ws,columns,sum(w['y'] for w in part)/6,unit)
            groups.append(group)
        if len(groups)>=2:
            for i in range(0,min(4,len(groups)),2):
                if i+1<len(groups) and groups[i] and groups[i+1]:
                    if len(groups)==3 and i==0 and groups[2] and groups[2]['team_letter']==groups[0]['team_letter']:
                        # Tie-break continuation repeats the same initial order; retain its more complete grid.
                        if len(groups[2]['service_ends'])>=len(groups[0]['service_ends']):
                            groups[0]=groups[2]
                    panels.append(dict(printed_set=5 if len(groups)==3 else row_index*2+i//2+1,teams=[groups[i],groups[i+1]]))
    if not panels:
        raise ValueError('Nenhuma formação e grade de saque legível; não executar inferência por OCR')
    for number,panel in enumerate(panels,1):
        panel['set_number']=number
    # Names in the original header connect A/B to the Match Report's canonical team names.
    header_lines=[]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            x0,y0,x1,y1=line['bbox']
            if .045*page.rect.height<y0<.11*page.rect.height and x0>.45*page.rect.width:
                header_lines.append(dict(text=''.join(span['text'] for span in line['spans']).strip(),x0=x0,x1=x1,y=(y0+y1)/2))
    names={}
    # Accented letters can be separate font spans. Join the original PDF line,
    # and bound the two name boxes independently so a short name cannot select
    # the other team's name or the printed "A ou B" legend.
    for letter in ('A','B'):
        labels=[w for w in ws if w['text']==letter and .045*page.rect.height<w['y']<.11*page.rect.height
                and w['x']>.45*page.rect.width and w['bbox'][3]-w['bbox'][1]>.015*page.rect.height]
        if len(labels)!=1:continue
        label=labels[0]
        right=.595*page.rect.width if label['x']<.6*page.rect.width else .80*page.rect.width
        candidates=[line for line in header_lines if label['x']+12<line['x0']<right and line['x1']<right
            and abs(line['y']-label['y'])<6 and line['text'].upper() not in ('EQUIPES','VS','A','B')]
        if candidates:
            names[letter]=' '.join(line['text'] for line in sorted(candidates,key=lambda line:line['y']))
    return dict(match_id=int(match_id),parser_version=PARSER_VERSION,sets=panels,team_names=names,
        coverage=dict(initial_lineup=True,service_order=all(t['grid_complete'] for p in panels for t in p['teams']),
                      substitutions=not any(e['kind']=='UNRESOLVED_SUBSTITUTION' for p in panels for t in p['teams'] for e in t['substitutions']),
                      timeouts=True,setter_identity=False,sanctions=False),
        limitations=['Identidade da levantadora não é assumida da ordem de saque.','Sanções não são extraídas por este contrato.'])


def parse_libero_report(path,match_id):
    page=pymupdf.open(path)[0];ws=words(page)
    if 'LIBERO' not in page.get_text().upper():
        raise ValueError('Documento não identificado como controle de líbero')
    headings=sorted([w for w in ws if 'PONTUA' in w['text'].upper()],key=lambda w:w['x'])
    if len(headings)<2:
        raise ValueError('Cabeçalhos de controle de líbero ausentes')
    spacing=headings[1]['x']-headings[0]['x'];intervals=[];warnings=[]
    for index,head in enumerate(headings):
        left,right=head['x']-.75*spacing,head['x']+.25*spacing
        letters=[w for w in ws if left<w['x']<right and w['y']<head['y'] and w['text'] in ('A','B')]
        if not letters:
            warnings.append(f'Bloco {index}: equipe desconhecida');continue
        letter=max(letters,key=lambda w:w['y'])['text']
        legend=[w for w in ws if left<w['x']<right and w['y']<head['y'] and w['text'].lower()=='libero']
        if not legend:
            warnings.append(f'Bloco {index}: líbero não identificado');continue
        legend=legend[-1]
        jersey=[w for w in ws if legend['x']<w['x']<right and abs(w['y']-legend['y'])<3 and w['text'].isdigit()]
        if not jersey:
            warnings.append(f'Bloco {index}: camisa do líbero ausente');continue
        libero=int(min(jersey,key=lambda w:w['x'])['text'])
        scores=sorted([w for w in ws if head['x']-.25*spacing<w['x']<right and w['y']>head['y'] and re.fullmatch(r'\d+-\d+',w['text'])],key=lambda w:w['y'])
        for i in range(0,len(scores),2):
            start=scores[i];end=scores[i+1] if i+1<len(scores) else None
            bottom=end['y']+3 if end else start['y']+16
            players=[w for w in ws if left+.2*spacing<w['x']<head['x']-.25*spacing and start['y']-3<w['y']<bottom and w['text'].isdigit()]
            if len(players)!=1:
                warnings.append(f'Bloco {index}: troca ambígua');continue
            intervals.append(dict(set_number=index//2+1,team_letter=letter,libero=libero,player_out=int(players[0]['text']),
                start_score=list(map(int,start['text'].split('-'))),end_score=list(map(int,end['text'].split('-'))) if end else None,
                source='OBSERVED_LIBERO_REPORT'))
    return dict(match_id=int(match_id),parser_version='libero-1.0',intervals=intervals,warnings=warnings,complete=not warnings)


def parse_setter_markers(path,home_team,away_team):
    """Use the report's outlined starter cells, as defined in its printed legend.

    Filled grey cells are other starters. Short hollow rectangles are substitutes.
    No identity is inferred from player performance or the match result.
    """
    page=pymupdf.open(path)[0];ws=words(page);width=page.rect.width
    if 'Levantador' not in page.get_text():
        return {}
    headers=[]
    for header in ws:
        if header['text']!='Set' or not .25*width<header['x']<.4*width:
            continue
        candidates=[w for w in ws if .26*width<w['x']<.4*width and header['y']+4<w['y']<header['y']+18 and w['text'] in ('1','2','3','4','5')]
        for row in _rows(candidates):
            row=sorted(row,key=lambda w:w['x'])
            if [w['text'] for w in row]==['1','2','3','4','5']:
                headers.append(dict(y=header['y'],columns=[w['x']+(row[1]['x']-row[0]['x'])*.4 for w in row]));break
    headers=sorted(headers,key=lambda h:h['y'])
    if len(headers)!=2:
        return {}
    drawings=page.get_drawings();result={home_team:{},away_team:{}}
    player_rows=_rows([w for w in ws if w['x']<.1*width and re.fullmatch(r'\d{2}',w['text'])])
    for row in player_rows:
        jersey=row[0];index=1 if jersey['y']>headers[1]['y'] else 0
        if jersey['y']<headers[0]['y']:continue
        header=headers[index];team=(home_team,away_team)[index];columns=header['columns'];gap=columns[1]-columns[0]
        for set_index,x in enumerate(columns,1):
            values=[w for w in ws if abs(w['x']-x)<gap*.25 and abs(w['y']-jersey['y'])<2 and w['text'] in ('1','2','3','4','5','6')]
            if len(values)!=1:continue
            word=values[0]
            outlined=[d for d in drawings if d.get('fill') is None and d.get('color') is not None
                and gap*.65<d['rect'].height<gap*1.05 and gap*.65<d['rect'].width<gap*1.05
                and d['rect'].contains(pymupdf.Point(word['x'],word['y']))]
            if outlined:
                candidate=dict(player=int(jersey['text']),position=int(word['text']),source='OBSERVED_MATCH_REPORT_SETTER_MARKER')
                if set_index in result[team]:
                    result[team][set_index]=None # Ambiguous marker: never pick an arbitrary setter.
                else:
                    result[team][set_index]=candidate
    return result
