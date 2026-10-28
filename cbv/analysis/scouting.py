"""Auditable descriptive statistics, scoped to competition/category/gender/season."""
import math
from collections import defaultdict
from statistics import mean, pvariance

from cbv.metric_definitions import METRICS, VERSION


def wilson(k, n):
    if n is None or n <= 0 or k is None or k < 0 or k > n:
        return None
    p, z = k/n, 1.959963984540054
    center = (p + z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [100*(center-half), 100*(center+half)]


def sample_label(n):
    return 'muito baixa' if n < 20 else 'baixa' if n < 50 else 'moderada' if n < 100 else 'estável para leitura descritiva'


def eb_prior(pairs):
    """Method-of-moments Beta prior; removes average binomial sampling variance."""
    pairs = [(k, n) for k, n in pairs if n > 0 and 0 <= k <= n]
    if len(pairs) < 3:
        return None
    mu = sum(k for k, n in pairs)/sum(n for k, n in pairs)
    if not 0 < mu < 1:
        return None
    variance = max(0, pvariance([k/n for k, n in pairs]) - mean([mu*(1-mu)/n for k, n in pairs]))
    strength = min(10000, max(2, mu*(1-mu)/max(variance, 1e-8)-1))
    return mu*strength, (1-mu)*strength


def metric_values(rows):
    result = {}
    for key, label, columns, denominator, cls, formula in METRICS:
        valid = [r for r in rows if r.get(denominator) is not None and r[denominator] > 0 and all(r.get(c.lstrip('-')) is not None for c in columns)]
        n = sum(r[denominator] for r in valid)
        k = sum(sum((-1 if c.startswith('-') else 1)*r[c.lstrip('-')] for c in columns) for r in valid)
        approximate = key in ('positive', 'excellent') or key.startswith(('pos_rec', 'neg_rec', 'trans'))
        result[key] = dict(label=label, value=100*k/n if n else None, numerator=k if n else None, n=n,
                           ci=wilson(k, n) if not approximate and key != 'eff' else None,
                           metric_class=cls, source_type='MATCH_REPORT',source_match_count=len(valid),sample_size=n,data_version=VERSION,model_version=None, formula=formula, approximate=approximate, sample=sample_label(n),
                           covered_matches=len(valid), total_matches=len(rows), adjusted=None)
    return result


def enrich_record(row):
    for label in ('positive', 'excellent'):
        n, p = row.get('reception_attempts'), row.get('reception_'+label+'_pct')
        row['reception_'+label+'_count'] = n*p/100 if n and p is not None else None
        row[label+'_receptions'] = n if p is not None else None
    return row


def aggregate_cohort(matches, rows, players, registered_teams=()):
    by_team = defaultdict(list)
    for r in rows:
        by_team[r['team']].append(enrich_record(dict(r)))
    for name in registered_teams:by_team[name]
    teams = []
    for name, records in sorted(by_team.items()):
        games = [m for m in matches if name in (m['home_team'], m['away_team']) and m['validation_status']=='VALID']
        wins = sum((m['home_sets'] > m['away_sets']) == (name == m['home_team']) for m in games if m['home_sets'] is not None and m['away_sets'] is not None)
        ordered = sorted([r for r in records if r.get('date')], key=lambda r:(r['date'], r['match_id']))
        trend = []
        for i, r in enumerate(ordered):
            vals = metric_values(ordered[max(0, i-4):i+1])
            trend.append(dict(date=r['date'], match_id=r['match_id'], so=vals['so']['value'], bp=vals['bp']['value'], n=vals['so']['n']))
        pr = defaultdict(list)
        for p in players:
            if p['team']==name:
                pr[p['player_name']].append(enrich_record(dict(p)))
        athletes = [dict(name=pn, games=len({r['match_id'] for r in rr}), receptions=sum(r.get('reception_attempts') or 0 for r in rr), metrics={k:v for k,v in metric_values(rr).items() if k in ('kill','eff','positive','excellent','rec_error','attack_error')}, points=sum(r.get('points_total') or 0 for r in rr)) for pn, rr in pr.items()]
        for athlete in athletes:
            source=pr[athlete['name']]
            fields=['points_total','break_points','win_loss','serve_attempts','serve_points','serve_errors','reception_attempts','reception_errors','attack_attempts','attack_points','attack_errors','attack_blocked','block_points']
            athlete['observed']={key:sum(r[key] for r in source if r.get(key) is not None) if any(r.get(key) is not None for r in source) else None for key in fields}
            athlete['observed_matches']={key:sum(r.get(key) is not None for r in source) for key in fields}
            obs=athlete['observed']
            serves=obs.get('serve_attempts') or 0
            aces=obs.get('serve_points') or 0
            srv_errs=obs.get('serve_errors') or 0
            attacks=obs.get('attack_attempts') or 0
            blocked=obs.get('attack_blocked') or 0
            blocks=obs.get('block_points') or 0
            pts=obs.get('points_total') or athlete.get('points') or 0
            n_games=max(1,athlete.get('games') or 1)
            if serves>0:
                athlete['metrics']['ace']=dict(label='Ace%',value=round(100.0*aces/serves,1),numerator=aces,n=serves,ci=wilson(aces,serves),metric_class='DERIVADO',formula='100 × serve_points / serve_attempts',sample=sample_label(serves))
                athlete['metrics']['serve_error']=dict(label='Erro de Saque%',value=round(100.0*srv_errs/serves,1),numerator=srv_errs,n=serves,ci=wilson(srv_errs,serves),metric_class='DERIVADO',formula='100 × serve_errors / serve_attempts',sample=sample_label(serves))
            if attacks>0:
                athlete['metrics']['attack_blocked']=dict(label='Bloqueado%',value=round(100.0*blocked/attacks,1),numerator=blocked,n=attacks,ci=wilson(blocked,attacks),metric_class='DERIVADO',formula='100 × attack_blocked / attack_attempts',sample=sample_label(attacks))
            athlete['metrics']['block_points']=dict(label='Bloqueios',value=blocks,numerator=blocks,n=n_games,ci=None,metric_class='OBSERVADO',formula='Soma de block_points',sample=f'{n_games} jogos')
            athlete['metrics']['block_per_game']=dict(label='Bloqueios/Jogo',value=round(blocks/n_games,2),numerator=blocks,n=n_games,ci=None,metric_class='DERIVADO',formula='block_points / jogos',sample=f'{n_games} jogos')
            athlete['metrics']['points_per_game']=dict(label='Pontos/Jogo',value=round(pts/n_games,1),numerator=pts,n=n_games,ci=None,metric_class='DERIVADO',formula='points_total / jogos',sample=f'{n_games} jogos')
        rotations = [dict(rotation=f'P{i}', observed_balance=sum(r[f'p{i}_diff'] for r in records if r.get(f'p{i}_diff') is not None), covered_matches=sum(r.get(f'p{i}_diff') is not None for r in records), so=None, bp=None) for i in range(1,7)]
        teams.append(dict(team=name, games=len(games), wins=wins, losses=len(games)-wins, metrics=metric_values(records), rotations=rotations, trend=trend, athletes=sorted(athletes,key=lambda a:-a['points'])))
    overall = metric_values([r for rr in by_team.values() for r in rr])
    base_k = (overall['kill']['value']/100.0) if overall.get('kill') and overall['kill']['value'] is not None else 0.38
    base_pos = (overall['positive']['value']/100.0) if overall.get('positive') and overall['positive']['value'] is not None else 0.60
    for t in teams:
        for a in t.get('athletes',[]):
            obs=a.get('observed',{})
            att=obs.get('attack_attempts') or 0
            kills=obs.get('attack_points') or 0
            atk_err=obs.get('attack_errors') or 0
            blocked=obs.get('attack_blocked') or 0
            serves=obs.get('serve_attempts') or 0
            aces=obs.get('serve_points') or 0
            srv_err=obs.get('serve_errors') or 0
            rec=obs.get('reception_attempts') or 0
            pos_pct=a['metrics'].get('positive',{}).get('value')
            pos_rec=round(rec*(pos_pct/100.0),1) if rec and pos_pct is not None else 0
            rec_err=obs.get('reception_errors') or 0
            blocks=obs.get('block_points') or 0
            n_games=max(1,a.get('games') or 1)
            x_kills = att * base_k if att > 0 else 0
            ava = kills - x_kills
            if att > 0:
                a['metrics']['ava']=dict(label='Attack Value Added (AVA)',value=round(ava,1),numerator=round(ava,1),n=att,ci=None,metric_class='EXPERIMENTAL',formula='attack_points − (attack_attempts × kill%_baseline)',unit='kills acima do esperado',sample=sample_label(att))
            epa = (0.30 * ava) - (0.70 * atk_err) - (0.85 * blocked) + (0.65 * aces) - (0.35 * srv_err) + (0.10 * (pos_rec - rec*base_pos)) - (0.65 * rec_err) + (0.65 * blocks)
            a['metrics']['epa']=dict(label='EPA Estimado',value=round(epa,1),numerator=round(epa,1),n=n_games,ci=None,metric_class='EXPERIMENTAL',formula='Decomposição Markoviana: 0.30×AVA − 0.70×AtkErr − 0.85×Bloq + 0.65×Ace − 0.35×SrvErr + 0.10×PosRec − 0.65×RecErr + 0.65×Blocks',unit='pontos líquidos estimados',sample=f'{n_games} jogos')
            a['metrics']['epa_per_game']=dict(label='EPA/Jogo',value=round(epa/n_games,2),numerator=round(epa,1),n=n_games,ci=None,metric_class='EXPERIMENTAL',formula='EPA Estimado / jogos',unit='pontos por jogo',sample=f'{n_games} jogos')
    for key, *_ in METRICS:
        rates = sorted(t['metrics'][key]['value'] for t in teams if t['metrics'][key]['value'] is not None)
        prior = eb_prior([(t['metrics'][key]['numerator'], t['metrics'][key]['n']) for t in teams if t['metrics'][key]['n']]) if key not in ('eff','positive','excellent') and not key.startswith(('pos_rec','neg_rec','trans')) else None
        for t in teams:
            m = t['metrics'][key]
            m['delta'] = m['value']-overall[key]['value'] if m['value'] is not None and overall[key]['value'] is not None else None
            m['percentile'] = 100*(sum(v < m['value'] for v in rates)+0.5*sum(v == m['value'] for v in rates))/len(rates) if m['value'] is not None and rates else None
            m['p25'] = rates[int((len(rates)-1)*.25)] if rates else None
            m['p75'] = rates[int((len(rates)-1)*.75)] if rates else None
            if prior and m['n']:
                a,b = prior
                m['adjusted'] = 100*(m['numerator']+a)/(m['n']+a+b)
                m['adjusted_metric_class']='MODELADO'
                m['adjusted_model_version']='eb-moments-v1'
                m['adjusted_prior']=dict(alpha=a,beta=b,scope='coorte completa; apenas descritivo')
    return dict(teams=teams, metrics=overall, matches=matches)
