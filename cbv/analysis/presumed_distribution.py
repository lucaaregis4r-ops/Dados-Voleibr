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
