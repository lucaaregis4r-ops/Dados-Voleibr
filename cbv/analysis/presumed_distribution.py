"""Experimental Bayesian attack-volume distribution from match aggregates.

The result predicts relative attack volume, not observed setter decisions.
"""
from collections import Counter, defaultdict
from math import log

FIELDS = ('competition', 'category', 'gender', 'season')
CANDIDATES = (0.5, 1., 2., 4., 8., 16., 32., 64.)


def _matches(matches, cohort):
    if len(cohort) != 4 or any(v is None or not str(v).strip() for v in cohort):
        return {}
    return {m['match_id']: m for m in matches if tuple(m.get(k) for k in FIELDS) == tuple(cohort)}


def _attempts(row):
    n = row.get('attack_attempts')
    return n if isinstance(n, (int, float)) and n > 0 and not row.get('is_libero') and row.get('player_name') else 0


def calibrate(matches, players, cohort, minimum_attempts=100):
    """Select symmetric prior mass by same-cohort forward match log score.

    Current and same-date matches cannot enter training. Previously unseen
    players are excluded and counted, since no trustworthy roster is available.
    """
    valid = _matches(matches, cohort)
    groups = defaultdict(lambda: defaultdict(Counter))
    for p in players:
        m = valid.get(p.get('match_id'))
        n = _attempts(p)
        if m and m.get('date') and p.get('team') and n:
            groups[p['team']][(str(m['date'])[:10], p['match_id'])][p['player_name']] += n
    losses = {s: 0. for s in CANDIDATES}
    evaluated = unseen = games = 0
    for team_games in groups.values():
        previous = Counter()
        by_date = defaultdict(list)
        for (day, mid), counts in team_games.items():
            by_date[day].append(counts)
        for day in sorted(by_date):
            for counts in by_date[day]:
                known = {k: n for k, n in counts.items() if k in previous}
                unseen += sum(n for k, n in counts.items() if k not in previous)
                if len(previous) < 2 or not known:
                    continue
                games += 1
                total, k = sum(previous.values()), len(previous)
                for strength in CANDIDATES:
                    losses[strength] -= sum(n * log((previous[name]+strength/k)/(total+strength)) for name,n in known.items())
                evaluated += sum(known.values())
            for counts in by_date[day]:
                previous.update(counts)
    calibrated = evaluated >= minimum_attempts and games >= 3
    strength = min(CANDIDATES, key=lambda s: losses[s]) if calibrated else 1.
    return dict(strength=strength, calibrated=calibrated, method='chronological_log_loss',
                evaluated_attempts=evaluated, unseen_attempts=unseen, evaluated_games=games,
                log_loss=losses[strength]/evaluated if evaluated else None)


def build_distribution(matches, players, cohort, team, strength):
    valid = _matches(matches, cohort)
    if not valid or not team or not strength or strength <= 0:
        return None
    counts = Counter()
    games = set()
    for p in players:
        n = _attempts(p)
        if p.get('match_id') in valid and p.get('team') == team and n:
            counts[p['player_name']] += n
            games.add(p['match_id'])
    if len(counts) < 2:
        return None
    total, k = sum(counts.values()), len(counts)
    probabilities = [dict(name=name, attempts=n, probability=(n+strength/k)/(total+strength))
                     for name,n in counts.most_common()]
    entropy = -sum(x['probability']*log(x['probability']) for x in probabilities)
    return dict(distribution=probabilities, attempts=total, games=len(games),
                strength=strength, predictability=100*(1-entropy/log(k)),
                conditional_available=False,
                limitation='Participação ofensiva presumida; não identifica passe, levantadora, rotação ou opções presentes em quadra.')


def build_phase_scenarios(matches, players, tactical, cohort, team):
    """Match-level proportional scenario and mathematically feasible margins.

    This is ecological analysis, not observed contact or a validated forecast.
    The allocation is independent within each match. Only exact reconciliations
    are used so the bounds have their stated meaning.
    """
    valid = _matches(matches, cohort)
    grouped = defaultdict(list)
    for row in players:
        if row.get('match_id') in valid and row.get('team') == team:
            grouped[row['match_id']].append(row)
    phase_fields = {'positive': 'pos_rec_att_attempts', 'negative': 'neg_rec_att_attempts', 'transition': 'trans_att_attempts'}
    out = {phase: dict(method='proportional_by_match', attempts=0, games=0,
                       excluded_games=0, distribution=[]) for phase in phase_fields}
    accum = {phase: defaultdict(lambda: [0., 0, 0]) for phase in phase_fields}
    for row in tactical:
        mid = row.get('match_id')
        if mid not in valid or row.get('team') != team:
            continue
        individual = grouped.get(mid, [])
        phase_values = [row.get(f) for f in phase_fields.values()]
        valid_counts = bool(individual) and all(isinstance(x,(int,float)) and x >= 0 for x in phase_values)
        valid_counts = valid_counts and all(p.get('attack_attempts') is None or (isinstance(p['attack_attempts'],(int,float)) and p['attack_attempts'] >= 0 and (not p['attack_attempts'] or p.get('player_name'))) for p in individual)
        if not valid_counts:
            for value in out.values(): value['excluded_games'] += 1
            continue
        counts = Counter()
        for p in individual:
            if p.get('attack_attempts') is not None and p['attack_attempts'] > 0:
                counts[p['player_name']] += p['attack_attempts']
        total = sum(counts.values())
        if not total or total != sum(phase_values):
            for value in out.values(): value['excluded_games'] += 1
            continue
        for phase, field in phase_fields.items():
            n = row[field]
            if n <= 0: continue
            out[phase]['attempts'] += n
            out[phase]['games'] += 1
            for name, attacks in counts.items():
                stat = accum[phase][name]
                stat[0] += attacks*n/total
                stat[1] += max(0, attacks-(total-n))
                stat[2] += min(attacks,n)
    for phase, result in out.items():
        total = result['attempts']
        if total:
            result['distribution'] = sorted((dict(name=name,scenario=v[0]/total,minimum=v[1]/total,maximum=v[2]/total) for name,v in accum[phase].items()),key=lambda v:-v['scenario'])
    return out
