"""Experimental observed-contact model; never derives contacts from match totals.

A caller must provide audited sequential distribution observations. No default
adapter asserts that reconstructed rallies contain actions they do not record.
"""
from collections import Counter, defaultdict
import math


def team_season_id(team, category, gender, season):
    """Identity is an opaque tuple: no guesses for missing cohort fields."""
    values = (team, category, gender, season)
    if any(not isinstance(v, str) or not v.strip() for v in values):
        return None
    return tuple(v.strip().casefold() for v in values)


def _identity(row):
    return team_season_id(*(row.get(x) for x in ('team', 'category', 'gender', 'season')))


def _matches(row, conditions):
    return all(row.get(key) == value for key, value in conditions.items())


def predict(records, team, category, gender, season, *, setter=None, rotation=None,
            pass_quality=None, live=(), prior_strength=1.0):
    """Posterior for documented targets; None when no defensible support exists.

    Parent and child levels use disjoint data to prevent repeated evidence.
    `prior_strength` is provisional and must be calibrated out of sample.
    """
    identity = team_season_id(team, category, gender, season)
    if identity is None or not math.isfinite(prior_strength) or prior_strength <= 0:
        return None
    history = [r for r in records if _identity(r) == identity and r.get('target')]
    candidates = sorted({r['target'] for r in history})
    if len(candidates) < 2:
        return None
    conditions = {}
    levels = [{}]
    if pass_quality is not None:
        conditions['pass_quality'] = pass_quality
        levels.append(dict(conditions))
    if rotation is not None:
        conditions['rotation'] = rotation
        levels.append(dict(conditions))
    if setter is not None:
        conditions['setter'] = setter
        levels.append(dict(conditions))
    # Build each conditional prior from the complement of its child subset.
    alpha = {target: prior_strength / len(candidates) for target in candidates}
    samples = []
    for i, level in enumerate(levels):
        current = [r for r in history if _matches(r, level)]
        child = levels[i+1] if i+1 < len(levels) else None
        segment = [r for r in current if child is None or not _matches(r, child)]
        counts = Counter(r['target'] for r in segment)
        if i:
            parent_total = sum(alpha.values())
            alpha = {k: prior_strength * alpha[k] / parent_total for k in candidates}
        alpha = {k: alpha[k] + counts[k] for k in candidates}
        samples.append(len(current))
    total = sum(alpha.values())
    historical = {k: alpha[k] / total for k in candidates}
    relevant_live = [r for r in live if _identity(r) == identity and r.get('target')
                     and _matches(r, levels[-1])]
    # Never silently discard a previously unseen attacker from the current game.
    if any(r['target'] not in alpha for r in relevant_live):
        return None
    counts = Counter(r['target'] for r in relevant_live)
    alpha = {k: alpha[k] + counts[k] for k in candidates}
    total = sum(alpha.values())
    probabilities = {k: alpha[k] / total for k in candidates}
    entropy = -sum(p * math.log(p) for p in probabilities.values() if p > 0)
    return dict(probabilities=probabilities, historical_probabilities=historical,
                posterior_sd={k: math.sqrt(p*(1-p)/(total+1)) for k,p in probabilities.items()},
                predictability=100*(1-entropy/math.log(len(candidates))),
                historical_count=len(history), context_count=samples[-1],
                live_count=len(relevant_live), prior_strength=prior_strength,
                prior_calibrated=False, options_basis='atacantes observadas no histórico; disponibilidade em quadra não confirmada')


def evaluate(records, prior_strength=1.0):
    """Walk forward by date; earlier actions in the same game are live data.

    Within each match input rows must be in observed order. Dates without a
    usable chronological identity and targets unseen in training are skipped.
    """
    valid = [r for r in records if r.get('date') and r.get('match_id') is not None and _identity(r) and r.get('target')]
    by_day = defaultdict(list)
    for row in valid:
        by_day[str(row['date'])].append(row)
    previous, predictions, skipped = [], [], len(records)-len(valid)
    for day in sorted(by_day):
        live = defaultdict(list)
        for row in by_day[day]:
            game_key = (row['match_id'], _identity(row))
            pred = predict(previous, row['team'], row['category'], row['gender'], row['season'],
                           setter=row.get('setter'), rotation=row.get('rotation'),
                           pass_quality=row.get('pass_quality'), live=live[game_key], prior_strength=prior_strength)
            if pred is None or row['target'] not in pred['probabilities']:
                skipped += 1
            else:
                predictions.append((pred['probabilities'], row['target']))
            live[game_key].append(row)
        previous.extend(by_day[day])
    n = len(predictions)
    if not n:
        return dict(predicted=0, skipped=skipped, log_loss=None, brier=None, top1=None, top2=None, calibration=[])
    loss = brier = top1 = top2 = 0.0
    bins = defaultdict(list)
    for probs, target in predictions:
        loss -= math.log(probs[target])
        brier += sum((p - (k == target))**2 for k,p in probs.items())
        ranked = sorted(probs, key=probs.get, reverse=True)
        top1 += target == ranked[0]
        top2 += target in ranked[:2]
        for k,p in probs.items():
            bins[min(9, int(p*10))].append((p, int(k == target)))
    calibration = [dict(bin=i, count=len(v), mean_probability=sum(x for x,_ in v)/len(v),
                        observed_frequency=sum(y for _,y in v)/len(v)) for i,v in sorted(bins.items())]
    return dict(predicted=n, skipped=skipped, log_loss=loss/n, brier=brier/n,
                top1=top1/n, top2=top2/n, calibration=calibration)


def calibrate_strength(records, strengths=(0.5, 1.0, 2.0, 4.0, 8.0, 16.0)):
    """Choose by chronological log loss; reserve later games for evaluation."""
    scored = []
    for value in strengths:
        if not math.isfinite(value) or value <= 0:
            raise ValueError('Prior strength must be finite and positive')
        metrics = evaluate(records, prior_strength=value)
        if metrics['predicted']:
            scored.append((metrics['log_loss'], value, metrics['predicted']))
    if not scored:
        return None
    loss, strength, n = min(scored)
    return dict(strength=strength, log_loss=loss, predicted=n,
                warning='Selecionado nesta amostra; avaliar em período posterior independente.')
