"""Tactical summaries over reconciled scoreboard sequences, never report SO aliases."""
from collections import defaultdict,Counter
from statistics import mean,median
from cbv.analysis.scouting import wilson


def rate(rows,side,serving=None):
    sample=[r for r in rows if serving is None or (r['serving_side']==side)==serving]
    n=len(sample);k=sum(r['winner_side']==side for r in sample)
    return dict(value=100*k/n if n else None,n=n,sample_size=n,numerator=k if n else None,ci=wilson(k,n),
        metric_class='DERIVADO',source_type='SCORESHEET_RECONSTRUCTED',source_match_count=len({r['match_id'] for r in sample}),
        data_version='atlas-reconstruction-1.0',model_version=None)


def serve_runs(rows,side):
    runs=[];current=None
    for row in sorted(rows,key=lambda r:(r['match_id'],r['set_number'],r['rally_number'])):
        identity=(row['match_id'],row['set_number'])
        if current and (identity!=current['set'] or row['serving_side']!=side):
            runs.append(current);current=None
        if row['serving_side']!=side:continue
        if current is None:current=dict(set=identity,rotation=row.get(side+'_rotation'),points=0,rallies=0,censored=True)
        current['rallies']+=1
        if row['winner_side']==side:current['points']+=1
        else:
            current['censored']=False;runs.append(current);current=None
    if current:runs.append(current)
    complete=[r['points'] for r in runs if not r['censored']]
    distribution=Counter(complete)
    return dict(n=len(complete),censored=sum(r['censored'] for r in runs),mean=mean(complete) if complete else None,
        median=median(complete) if complete else None,maximum=max((r['points'] for r in runs),default=None),
        distribution=[dict(points=k,n=v) for k,v in sorted(distribution.items())],
        survival=[dict(points=k,value=sum(p>=k for p in complete)/len(complete) if complete else None) for k in range(1,max(complete,default=4)+1)],
        runs=runs,metric_class='DERIVADO',source_type='SCORESHEET_RECONSTRUCTED',
        definition='Pontos ganhos sacando; passagens encerradas pelo fim do set são censuradas e excluídas de média/sobrevivência.')


def summarize_team(rows,team,opponent=None):
    selected=[]
    for row in rows:
        side='home' if row['home_team']==team else 'away' if row['away_team']==team else None
        if side is None or opponent and row[('away' if side=='home' else 'home')+'_team']!=opponent:continue
        item=dict(row)
        # Orient own/other consistently without altering the original snapshot.
        item['own_rotation']=row.get(side+'_rotation');item['other_rotation']=row.get(('away' if side=='home' else 'home')+'_rotation')
        item['serving_side']='own' if row['serving_side']==side else 'other'
        item['winner_side']='own' if row['winner_side']==side else 'other'
        item['expected_own']=row.get('expected_home') if side=='home' else 1-row['expected_home'] if row.get('expected_home') is not None else None
        item['own_lineup_names']=row.get(side+'_lineup_names')
        item['own_lineup']=row.get(side+'_lineup');item['own_lineup_confidence']=row.get(side+'_lineup_confidence')
        selected.append(item)
    def expected_summary(subset):
        covered=[r for r in subset if r.get('expected_own') is not None]
        n=len(covered);observed=100*sum(r['winner_side']=='own' for r in covered)/n if n else None
        expected=100*sum(r['expected_own'] for r in covered)/n if n else None
        return dict(n=n,observed=observed,expected=expected,above_expected=observed-expected if n else None,metric_class='EXPERIMENTAL',model_version='atlas-rally-beta-v2')
    total_so=rate(selected,'own',False);total_bp=rate(selected,'own',True);rotations=[]
    for position in range(1,7):
        subset=[r for r in selected if r['own_rotation']==position]
        so=rate(subset,'own',False);bp=rate(subset,'own',True);allrate=rate(subset,'own')
        rotations.append(dict(position=position,so=so,bp=bp,points=allrate,balance=2*sum(r['winner_side']=='own' for r in subset)-len(subset),
            pressure=dict(expected_summary([r for r in subset if r.get('pressure_band') in ('HIGH','VERY_HIGH')]),value=rate([r for r in subset if r.get('pressure_band') in ('HIGH','VERY_HIGH')],'own')['value']),
            expected=expected_summary(subset),xso=expected_summary([r for r in subset if r['serving_side']!='own']),xbp=expected_summary([r for r in subset if r['serving_side']=='own']),
            so_delta_team=so['value']-total_so['value'] if so['n'] and total_so['n'] else None,
            bp_delta_team=bp['value']-total_bp['value'] if bp['n'] and total_bp['n'] else None))
    matrix=[]
    for own in range(1,7):
        for other in range(1,7):
            subset=[r for r in selected if r['own_rotation']==own and r['other_rotation']==other]
            matrix.append(dict(own=own,other=other,points=rate(subset,'own'),so=rate(subset,'own',False),bp=rate(subset,'own',True),
                matches=sorted({r['match_id'] for r in subset})))
    runs=[]
    # run function needs a consistent side field; own rotation is supplied explicitly.
    runrows=[dict(r,own_rotation=r['own_rotation']) for r in selected]
    runs=serve_runs(runrows,'own')
    readings=[]
    eligible=[r for r in rotations if r['so']['n']>=20]
    if eligible:
        best=max(eligible,key=lambda r:r['so']['value']);worst=min(eligible,key=lambda r:r['so']['value'])
        for rule,r,label in [('rotation_so_highest',best,'maior'),('rotation_so_lowest',worst,'menor')]:
            readings.append(dict(rule_id=rule,metric='rotation_so',comparison=r['so_delta_team'],sample=r['so']['n'],
                text=f"P{r['position']} tem o {label} SO entre rotações com n≥20: {r['so']['value']:.1f}% ({r['so_delta_team']:+.1f} pp vs equipe; n={r['so']['n']})."))
    lineups=defaultdict(list);players=set()
    for r in selected:
        if r['own_lineup_confidence']=='RECONSTRUCTED_HIGH' and r['own_lineup'] and None not in r['own_lineup'] and r['own_lineup_names'] and len(set(r['own_lineup_names']))==6:
            key=tuple(sorted(r['own_lineup_names']));lineups[key].append(r);players.update(key)
    reliable=[r for bucket in lineups.values() for r in bucket]
    formation=[]
    for key,bucket in lineups.items():
        summary=rate(bucket,'own');prior=rate(reliable,'own')['value']
        formation.append(dict(players=sorted(bucket[0]['own_lineup']),identities=list(key),points=summary,so=rate(bucket,'own',False),bp=rate(bucket,'own',True),
            adjusted=100*(summary['numerator']+100*prior/100)/(summary['n']+100) if prior is not None else None,
            shrinkage='Prior da própria equipe, força fixa 100 rallies; análise descritiva, não validação preditiva.'))
    onoff=[]
    for player in sorted(players):
        on=[r for r in reliable if player in r['own_lineup_names']];off=[r for r in reliable if player not in r['own_lineup_names']]
        a,b=rate(on,'own'),rate(off,'own')
        onoff.append(dict(player=player,on=a,off=b,difference=a['value']-b['value'] if a['n'] and b['n'] else None,
            adjusted_contextual_effect=None,limitation='Contraste bruto; sem interpretação causal. Ajuste contextual não validado.'))
    return dict(expected=expected_summary(selected),team=team,so=total_so,bp=total_bp,rotations=rotations,matrix=matrix,serve_runs=runs,readings=readings,
        lineups=sorted(formation,key=lambda r:r['points']['n'],reverse=True),on_off=onoff,
        coverage=dict(rallies=len(selected),rotation_rallies=sum(r['own_rotation'] is not None for r in selected),reliable_presence_rallies=len(reliable)))


def load_atlas(conn):
    import json
    tables={r[0] for r in conn.execute('SHOW TABLES').fetchall()}
    if 'validation_reports' not in tables:return dict(rows=[],coverage={},sources=[],validations=[])
    roster=defaultdict(set)
    for mid,team,jersey,name in conn.execute('SELECT match_id,team,player_number,player_name FROM player_match_stats').fetchall():
        roster[(mid,team,jersey)].add(name)
    rows=[]
    for payload,home,away,date in conn.execute('''SELECT r.payload,m.home_team,m.away_team,CAST(m.date AS VARCHAR) FROM rallies r
        JOIN matches m USING(match_id) JOIN validation_reports v USING(match_id) JOIN reconstruction_attempts a USING(match_id)
        WHERE m.validation_status='VALID' AND a.status IN ('VALID','VALID_WITH_WARNINGS') AND v.status IN ('VALID','VALID_WITH_WARNINGS') AND r.payload IS NOT NULL ORDER BY m.date,r.match_id,r.set_number,r.rally_number''').fetchall():
        row=dict(json.loads(payload),home_team=home,away_team=away,date=date)
        for side,team in [('home',home),('away',away)]:
            names=[roster.get((row['match_id'],team,jersey),set()) for jersey in row.get(side+'_lineup',[])]
            row[side+'_lineup_names']=[next(iter(n)) for n in names] if len(names)==6 and all(len(n)==1 for n in names) else None
        rows.append(row)
    sources=[dict(json.loads(data),match_id=mid,source_type=kind) for mid,kind,data in conn.execute('SELECT * FROM source_snapshots').fetchall()]
    validations=[dict(match_id=mid,status=status,report=json.loads(report),updated_at=updated) for mid,status,report,updated in conn.execute('SELECT * FROM validation_reports').fetchall()]
    attempts=[dict(match_id=mid,status=status,report=json.loads(report)) for mid,status,report,_ in conn.execute('SELECT * FROM reconstruction_attempts').fetchall()]
    return dict(rows=rows,sources=sources,validations=validations,attempts=attempts,coverage=dict(rallies=len(rows),reconstructed_matches=len({r['match_id'] for r in rows}),
        rotation_matches=len({r['match_id'] for r in rows if r.get('home_rotation') and r.get('away_rotation')})))
