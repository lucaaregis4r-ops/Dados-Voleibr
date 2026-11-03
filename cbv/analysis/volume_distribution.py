"""Experimental ecological-Bayesian attack activation model.

The model never invents observed setter contacts. It combines three things that
are available in Atlas: player attack totals by match, reconstructed lineup /
rotation exposure, and team attack-phase totals (K1+, K1-, transition).

Phase-conditioned player contacts are unobserved. Phase scenarios therefore
fall back to the rotation / availability reference and are not predictions.
"""
from collections import Counter, defaultdict
import math

import numpy as np
from cbv.analysis.rotation_allocation import allocate_scenarios, disambiguate_players

VERSION = 'lineup-ecological-bayes-v2'
PHASES = ('positive', 'negative', 'transition')
PHASE_FIELDS = {
    'positive': 'pos_rec_att_attempts',
    'negative': 'neg_rec_att_attempts',
    'transition': 'trans_att_attempts',
}
DEFAULT_PRIOR_STRENGTH = 8.0


def _team_side(row, team):
    if row.get('home_team') == team:
        return 'home'
    if row.get('away_team') == team:
        return 'away'
    return None


def _player_maps(players, team):
    volumes = defaultdict(float)
    by_match = defaultdict(lambda: defaultdict(float))
    liberos = set()
    match_ids = set()
    for p in players:
        if p.get('team') != team or not p.get('player_name'):
            continue
        name = p['player_name']
        if p.get('is_libero'):
            liberos.add(name)
        value = p.get('attack_attempts')
        if isinstance(value, (int, float)) and value >= 0:
            volumes[name] += float(value)
            by_match[p.get('match_id')][name] += float(value)
            match_ids.add(p.get('match_id'))
    return volumes, by_match, liberos, {m for m in match_ids if m is not None}


def _exposure(rows, team):
    """Return reliable lineup exposure by match/rotation/player and modal lineups."""
    rotation_lineups = defaultdict(list)
    match_rotation_total = Counter()
    player_rotation = Counter()
    match_total = Counter()
    source_matches = defaultdict(set)

    for row in rows:
        side = _team_side(row, team)
        if not side:
            continue
        rotation = row.get(side + '_rotation')
        names = row.get(side + '_lineup_names')
        numbers = row.get(side + '_lineup')
        confidence = row.get(side + '_lineup_confidence')
        mid = row.get('match_id')
        if (
            rotation not in range(1, 7)
            or confidence != 'RECONSTRUCTED_HIGH'
            or not names
            or not all(names)
            or len(names) != 6
            or len(set(names)) != 6
        ):
            continue
        names = tuple(names)
        numbers = tuple(numbers or [None] * 6)
        rotation_lineups[rotation].append((names, numbers, mid))
        match_rotation_total[(mid, rotation)] += 1
        match_total[mid] += 1
        source_matches[rotation].add(mid)
        for name in names:
            player_rotation[(mid, name, rotation)] += 1

    return dict(
        rotation_lineups=rotation_lineups,
        match_rotation_total=match_rotation_total,
        player_rotation=player_rotation,
        match_total=match_total,
        source_matches=source_matches,
    )


def _load_tactical(match_ids, team):
    if not match_ids:
        return []
    try:
        from cbv.database.repository import default_repo
        with default_repo.get_connection() as conn:
            rows = conn.execute(
                '''SELECT match_id, team, pos_rec_att_attempts, neg_rec_att_attempts,
                          trans_att_attempts
                   FROM team_tactical_stats WHERE team = ?''',
                [team],
            ).fetchdf().to_dict(orient='records')
        return [r for r in rows if r.get('match_id') in match_ids]
    except Exception:
        return []


def _tactical_by_match(tactical, team, valid_match_ids):
    out = {}
    for row in tactical or []:
        mid = row.get('match_id')
        if row.get('team') != team or mid not in valid_match_ids:
            continue
        values = []
        ok = True
        for phase in PHASES:
            v = row.get(PHASE_FIELDS[phase])
            if not isinstance(v, (int, float)) or v < 0:
                ok = False
                break
            values.append(float(v))
        if ok and sum(values) > 0:
            out[mid] = dict(zip(PHASES, values))
    return out


def _base_rates(by_match, exposures, liberos):
    """Exposure-adjusted season attack intensity used as the Bayesian prior mean."""
    match_total_attacks = {mid: sum(counts.values()) for mid, counts in by_match.items()}
    opportunity = defaultdict(float)
    attacks = defaultdict(float)
    all_names = set()
    for mid, counts in by_match.items():
        total_attacks = match_total_attacks.get(mid, 0.0)
        reliable = exposures['match_total'].get(mid, 0)
        all_names.update(counts)
        if total_attacks <= 0:
            continue
        for name, n in counts.items():
            attacks[name] += n
            if reliable:
                present = sum(exposures['player_rotation'].get((mid, name, r), 0) for r in range(1, 7))
                opportunity[name] += total_attacks * min(1.0, present / reliable)
            else:
                opportunity[name] += total_attacks
    rates = {}
    for name in all_names:
        if name in liberos:
            rates[name] = 0.0
        else:
            denom = opportunity.get(name, 0.0)
            rates[name] = attacks.get(name, 0.0) / denom if denom > 0 else attacks.get(name, 0.0)
    return rates, match_total_attacks


def _fit_latent_phase_rates(by_match, exposures, tactical_by_match, liberos, prior_strength):
    """Fit per-player rotation x phase latent rates with a Gaussian ridge prior."""
    usable = []
    positive_shares = []
    for mid, phase_counts in tactical_by_match.items():
        individual = by_match.get(mid)
        reliable = exposures['match_total'].get(mid, 0)
        if not individual or reliable <= 0:
            continue
        team_total = sum(individual.values())
        phase_total = sum(phase_counts.values())
        if team_total <= 0 or abs(team_total - phase_total) > 1e-9:
            continue
        phase_share = {p: phase_counts[p] / phase_total for p in PHASES}
        positive_shares.append(phase_share['positive'])
        usable.append((mid, team_total, phase_share))

    support_games = len(usable)
    positive_sd = float(np.std(positive_shares)) if positive_shares else 0.0
    # Aggregated match totals do not observe phase-to-player contacts. Variation
    # alone cannot identify 18 rotation/phase effects or validate predictions.
    # Keep phase-specific output gated until independent contact data validate it.
    identified = False
    # No phase-conditioned player outcomes are observed: even a well-fitting
    # ecological model cannot establish the requested conditional probabilities.
    return {}, dict(identified=False, support_games=support_games,
                    positive_share_sd=positive_sd, reason='phase_player_contacts_unobserved')



def _normalize(entries, key):
    total = sum(max(0.0, float(e.get(key, 0.0) or 0.0)) for e in entries)
    if total <= 0:
        return None
    return {e['name']: max(0.0, float(e.get(key, 0.0) or 0.0)) / total for e in entries}


def estimate_distributions(rows, players, team, tactical=None, prior_strength=DEFAULT_PRIOR_STRENGTH):
    """Estimate rotation priors and pass-conditioned activation scenarios."""
    rows, players = disambiguate_players(rows, players, team)
    volumes, by_match, liberos, match_ids = _player_maps(players, team)
    exposures = _exposure(rows, team)
    base_rates, _ = _base_rates(by_match, exposures, liberos)
    if tactical is None:
        tactical = _load_tactical(match_ids, team)
    tactical_map = _tactical_by_match(tactical, team, match_ids)
    allocations = allocate_scenarios(rows, players, team, tactical)
    latent_rates, model_diag = _fit_latent_phase_rates(
        by_match, exposures, tactical_map, liberos, prior_strength
    )

    results = []
    for position in range(1, 7):
        eligible = exposures['rotation_lineups'].get(position, [])
        if not eligible:
            continue
        counts = Counter((names, numbers) for names, numbers, _ in eligible)
        names, numbers = max(counts, key=lambda key: (counts[key], key))

        base_entries = []
        for i, name in enumerate(names):
            base_entries.append(dict(
                name=name,
                number=numbers[i] if i < len(numbers) else None,
                zone=i + 1,
                raw_rate=0.0 if name in liberos else float(base_rates.get(name, 0.0)),
                attacks=float(volumes.get(name, 0.0)),
                structural_zero=name in liberos,
            ))
        estimate = allocations.get(position)
        allocated = estimate.get('all', {}) if estimate else {}
        for entry in base_entries:
            entry['allocated_score'] = 0.0 if entry['structural_zero'] else allocated.get(entry['name'], 0.0)
        allocated_probs = _normalize(base_entries, 'allocated_score')
        base_probs = allocated_probs or _normalize(base_entries, 'raw_rate')
        if base_probs is None:
            continue
        distribution = []
        for entry in base_entries:
            item = dict(entry)
            item['weight'] = 0.0 if item['structural_zero'] else base_probs.get(item['name'], 0.0)
            distribution.append(item)

        entropy = -sum(
            p['weight'] * math.log2(p['weight'])
            for p in distribution if p['weight'] > 0
        )

        scenarios = {}
        game_allocations = estimate.get('game_allocations', {}) if estimate else {}
        def sensitivity(name, phase, totals):
            eligible_games = [game for game in game_allocations.values()
                              if sum(game.get(phase, {}).values()) > 0]
            if len(eligible_games) < 3:
                return None
            values = []
            for game in eligible_games:
                remaining = {key: max(0.0, totals.get(key, 0.0) - game.get(phase, {}).get(key, 0.0))
                             for key in names}
                denominator = sum(remaining.values())
                if denominator > 0:
                    values.append(remaining.get(name, 0.0) / denominator)
            return dict(min=min(values), max=max(values), method='leave_one_game_out') if len(values) >= 3 else None

        for item in distribution:
            item['sensitivity'] = sensitivity(item['name'], 'all', allocated) if allocated_probs else None

        for phase in PHASES:
            phase_totals = estimate.get(phase, {}) if estimate else {}
            phase_entries = [dict(name=item['name'], number=item['number'], zone=item['zone'],
                                  score=0.0 if item['structural_zero'] else phase_totals.get(item['name'], 0.0),
                                  structural_zero=item['structural_zero']) for item in distribution]
            probs = _normalize(phase_entries, 'score')
            if probs is None:
                scenarios[phase] = dict(distribution=[], identified=False, support_games=int((estimate or {}).get('phase_games', 0)), method='insufficient_data')
                continue
            for entry in phase_entries:
                entry['probability'] = float(probs.get(entry['name'], 0.0))
                entry['sensitivity'] = sensitivity(entry['name'], phase, phase_totals)
            scenarios[phase] = dict(distribution=phase_entries, identified=False,
                support_games=int(estimate['phase_games']), method='proportional_match_allocation',
                interpretation='Cenário proporcional; não estima efeito do passe observado ou validado.')

        effect = None

        results.append(dict(
            position=position,
            distribution=distribution,
            entropy=entropy,
            n_lineup=counts[(names, numbers)],
            availability_rallies=len(eligible),
            source_match_count=len(exposures['source_matches'].get(position, set())),
            volume_match_count=len(match_ids),
            allocation_method='proportional_match_allocation' if allocated_probs else 'overall_fallback',
            allocation_match_count=int(estimate['games']) if allocated_probs else 0,
            confidence=dict(
                status='NOT_VALIDATED', prediction_score=None,
                lineup_rallies=counts[(names, numbers)],
                lineup_share=counts[(names, numbers)] / len(eligible),
                source_games=len(exposures['source_matches'].get(position, set())),
                support_index=round(100 * counts[(names, numbers)] / len(eligible)
                                    * min(1, len(eligible) / 100)
                                    * min(1, len(exposures['source_matches'].get(position, set())) / 5)),
                description='Indicador heurístico de suporte da formação, não probabilidade de acerto nem validação do modelo.',
            ),
            metric_class='EXPERIMENTAL',
            model_version=VERSION,
            pass_condition_effect=effect,
            pass_scenarios=scenarios,
            definition='Cenário proporcional: os ataques de cada partida são distribuídos segundo a exposição reconstruída e as fases agregadas daquela partida.',
            limitation='Não há contatos observados por fase e atleta. A alocação supõe uso constante em cada jogo ao longo das rotações e mesma distribuição por fase; não é previsão validada.',
        ))
    return results

