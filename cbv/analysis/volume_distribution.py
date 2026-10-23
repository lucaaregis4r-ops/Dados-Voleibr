"""Experimental volume prior on observed lineups, without invented pass contacts."""
from collections import defaultdict,Counter
import math

VERSION='lineup-volume-prior-v1'


def estimate_distributions(rows,players,team):
    volumes=defaultdict(float);liberos=set();matches=set()
    for p in players:
        if p['team']!=team:continue
        if p.get('is_libero'):liberos.add(p['player_name'])
        if p.get('attack_attempts') is not None:
            volumes[p['player_name']]+=p['attack_attempts'];matches.add(p['match_id'])
    results=[]
    for position in range(1,7):
        eligible=[]
        for r in rows:
            side='home' if r['home_team']==team else 'away' if r['away_team']==team else None
            if side and r.get(side+'_rotation')==position and r.get(side+'_lineup_confidence')=='RECONSTRUCTED_HIGH' and r.get(side+'_lineup_names'):
                eligible.append((tuple(r[side+'_lineup_names']),tuple(r[side+'_lineup']),r['match_id']))
        if not eligible:continue
        counts=Counter((names,numbers) for names,numbers,_ in eligible)
        names,numbers=max(counts,key=lambda key:(counts[key],key));total=sum(volumes[name] for name in names if name not in liberos)
        if total<=0:continue
        distribution=[dict(name=name,number=numbers[i],zone=i+1,weight=volumes[name]/total if name not in liberos else 0.,attacks=volumes[name]) for i,name in enumerate(names)]
        entropy=-sum(p['weight']*math.log2(p['weight']) for p in distribution if p['weight']>0)
        results.append(dict(position=position,distribution=distribution,entropy=entropy,n_lineup=counts[(names,numbers)],
            availability_rallies=len(eligible),source_match_count=len({mid for n,j,mid in eligible}),volume_match_count=len(matches),
            metric_class='EXPERIMENTAL',model_version=VERSION,pass_condition_effect=None,
            definition='Pesos de volume ofensivo da coorte normalizados entre atacantes da formação mais frequente com presença reconciliada nesta passagem.',
            limitation='Não estima frequência observada de levantamentos, contatos ou destinos de ataque. Sem eventos, passe não muda os pesos. Entropia alta não significa melhor. Não é escalação provável.'))
    return results
