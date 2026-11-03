"""Query helpers for the Atlas presumed activation model.

This module exposes the ecological-Bayesian rotation/pass estimates without
falling back to the legacy hard-coded setter multipliers.
"""
import math


PHASE_ALIASES = {
    'positive': 'positive', 'pos': 'positive', 'k1+': 'positive', '+': 'positive',
    'negative': 'negative', 'neg': 'negative', 'k1-': 'negative', '-': 'negative',
    'transition': 'transition', 'trans': 'transition', 'k2': 'transition',
}


def _rotation_number(rotation):
    text = str(rotation or '').strip().upper()
    if text.startswith('P'):
        text = text[1:]
    try:
        value = int(text)
    except (TypeError, ValueError):
        raise ValueError('rotation must be P1..P6')
    if value not in range(1, 7):
        raise ValueError('rotation must be P1..P6')
    return value


def _phase_name(pass_quality):
    key = str(pass_quality or '').strip().lower()
    if key not in PHASE_ALIASES:
        raise ValueError('pass_quality must be positive, negative or transition')
    return PHASE_ALIASES[key]


def activation_from_distributions(distributions, rotation, pass_quality, *, team, cohort=None):
    """Select one P x phase scenario from ``estimate_distributions`` output."""
    position = _rotation_number(rotation)
    phase = _phase_name(pass_quality)
    cell = next((r for r in distributions or [] if r.get('position') == position), None)
    if cell is None:
        return None
    scenario = (cell.get('pass_scenarios') or {}).get(phase)
    if not scenario:
        return None

    items = []
    for row in scenario.get('distribution') or []:
        probability = max(0.0, float(row.get('probability') or 0.0))
        items.append(dict(
            player_name=row.get('name'),
            zone=row.get('zone'),
            probability=probability,
            probability_pct=100.0 * probability,
            structural_zero=bool(row.get('structural_zero')),
            margin_error_pct=None,
            ci_95=None,
        ))
    items.sort(key=lambda x: (x['probability'], x.get('player_name') or ''), reverse=True)

    active = [x['probability'] for x in items if x['probability'] > 0]
    if len(active) > 1:
        entropy = -sum(p * math.log(p) for p in active)
        predictability = 100.0 * (1.0 - entropy / math.log(len(active)))
    else:
        predictability = 100.0 if active else 0.0

    return dict(
        team=team,
        cohort=cohort or {},
        rotation=f'P{position}',
        pass_quality=phase,
        distribution=items,
        predictability_pct=predictability,
        identified=bool(scenario.get('identified')),
        support_games=int(scenario.get('support_games') or 0),
        method=scenario.get('method'),
        metric_class=cell.get('metric_class', 'EXPERIMENTAL'),
        model_version=cell.get('model_version'),
        availability_rallies=cell.get('availability_rallies'),
        source_match_count=cell.get('source_match_count'),
        pass_condition_effect=cell.get('pass_condition_effect'),
        limitation=cell.get('limitation'),
    )


def compute_presumed_activation(team, rotation='P1', pass_quality='positive', *, season=None,
                                 competition=None, category=None, gender=None):
    """Resolve one team cohort and compute the current experimental scenario.

    Optional cohort fields prevent cross-season/category ambiguity. When omitted,
    the most recent validated cohort for the team is selected and reported back.
    """
    from cbv.database.repository import default_repo
    from cbv.analysis.atlas import load_atlas
    from cbv.analysis.volume_distribution import estimate_distributions

    filters = ['LOWER(p.team) = LOWER(?)', "m.validation_status = 'VALID'"]
    params = [team]
    for column, value in (
        ('m.season', season), ('m.competition', competition),
        ('m.category', category), ('m.gender', gender),
    ):
        if value is not None:
            filters.append(f'{column} = ?')
            params.append(value)
    where = ' AND '.join(filters)

    with default_repo.get_connection() as conn:
        cohort_row = conn.execute(
            f'''SELECT p.team, m.competition, m.category, m.gender, m.season,
                       MAX(m.date) AS last_date, COUNT(DISTINCT m.match_id) AS games
                FROM player_match_stats p JOIN matches m USING(match_id)
                WHERE {where}
                GROUP BY p.team, m.competition, m.category, m.gender, m.season
                ORDER BY last_date DESC, games DESC LIMIT 1''',
            params,
        ).fetchone()
        if not cohort_row:
            return None
        actual_team, comp, cat, gen, sea, _, games = cohort_row
        ids = {
            r[0] for r in conn.execute(
                '''SELECT DISTINCT m.match_id FROM matches m
                   JOIN player_match_stats p USING(match_id)
                   WHERE p.team = ? AND m.competition = ? AND m.category = ?
                     AND m.gender = ? AND m.season = ? AND m.validation_status = 'VALID' ''',
                [actual_team, comp, cat, gen, sea],
            ).fetchall()
        }
        if not ids:
            return None
        players = conn.execute(
            '''SELECT * FROM player_match_stats WHERE team = ?''', [actual_team]
        ).fetchdf().to_dict(orient='records')
        players = [r for r in players if r.get('match_id') in ids]
        tactical = conn.execute(
            '''SELECT match_id, team, pos_rec_att_attempts, neg_rec_att_attempts,
                      trans_att_attempts FROM team_tactical_stats WHERE team = ?''',
            [actual_team],
        ).fetchdf().to_dict(orient='records')
        tactical = [r for r in tactical if r.get('match_id') in ids]
        atlas = load_atlas(conn)
        rally_rows = [r for r in atlas.get('rows', []) if r.get('match_id') in ids]

    distributions = estimate_distributions(rally_rows, players, actual_team, tactical=tactical)
    cohort = dict(competition=comp, category=cat, gender=gen, season=sea, games=int(games or 0))
    return activation_from_distributions(
        distributions, rotation, pass_quality, team=actual_team, cohort=cohort
    )
