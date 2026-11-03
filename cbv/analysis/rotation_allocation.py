"""Proportional scenarios from game totals and reconstructed presence.

Not observed attacks by phase/rotation, not causal effects or validated forecasts.
"""
from collections import Counter, defaultdict
import math

PHASES = {'positive': 'pos_rec_att_attempts', 'negative': 'neg_rec_att_attempts',
          'transition': 'trans_att_attempts'}


def _jersey(value):
    if value is None:
        return None
    try:
        if not math.isfinite(float(value)):
            return None
        return str(int(value)) if float(value).is_integer() else str(value)
    except (ValueError, TypeError):
        return str(value)


def _side(row, team):
    return 'home' if row.get('home_team') == team else 'away' if row.get('away_team') == team else None


def disambiguate_players(rows, players, team):
    jerseys = defaultdict(set)
    for player in players:
        if player.get('team') == team and player.get('player_name') and _jersey(player.get('player_number')) is not None:
            jerseys[player['player_name']].add(_jersey(player['player_number']))
    collisions = {name for name, values in jerseys.items() if len(values) > 1}

    def label(name, number):
        if name in collisions:
            number = _jersey(number)
            return f'{name} · #{number}' if number is not None else None
        return name

    adjusted_players = []
    for p in players:
        p = dict(p)
        if p.get('team') == team:
            p['player_name'] = label(p.get('player_name'), p.get('player_number'))
        adjusted_players.append(p)
    adjusted_rows = []
    for row in rows:
        side = _side(row, team)
        if side and row.get(side + '_lineup_names'):
            row = dict(row)
            names = row[side + '_lineup_names']
            numbers = row.get(side + '_lineup') or []
            row[side + '_lineup_names'] = [label(name, numbers[i] if i < len(numbers) else None)
                                          for i, name in enumerate(names)]
        adjusted_rows.append(row)
    return adjusted_rows, adjusted_players


def allocate_scenarios(rows, players, team, tactical, min_coverage=.8):
    """Allocate match attacks by each player's rotation exposure and phase shares.

    Each match retains its actual total attacks per athlete. Phase shares are
    multiplied within that game only when phase totals exactly reconcile.
    Results are normalized only after the caller selects a modal formation.
    """
    matches = defaultdict(Counter)
    for p in players:
        n = p.get('attack_attempts')
        if (p.get('team') == team and p.get('player_name') and isinstance(n, (int, float))
                and math.isfinite(n) and n >= 0):
            matches[p.get('match_id')][p['player_name']] += float(n)

    total = Counter()
    good = Counter()
    exposure = Counter()
    for row in rows:
        side = _side(row, team)
        if not side:
            continue
        mid = row.get('match_id')
        total[mid] += 1
        pos, names = row.get(side+'_rotation'), row.get(side+'_lineup_names')
        if (pos not in range(1, 7) or row.get(side+'_lineup_confidence') != 'RECONSTRUCTED_HIGH'
                or not names or len(names) != 6 or not all(names) or len(set(names)) != 6):
            continue
        good[mid] += 1
        for name in names:
            exposure[mid, name, pos] += 1

    phases_by_game = {}
    for item in tactical or []:
        if item.get('team') != team:
            continue
        vals = [item.get(k) for k in PHASES.values()]
        if all(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0 for x in vals):
            phases_by_game[item.get('match_id')] = dict(zip(PHASES, vals))

    allocation = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    active_games = defaultdict(set)
    phase_games = defaultdict(set)
    per_game = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    for mid, athletes in matches.items():
        attacks = sum(athletes.values())
        if not total[mid] or good[mid] / total[mid] < min_coverage or attacks <= 0:
            continue
        if any(n > 0 and sum(exposure[mid, name, pos] for pos in range(1, 7)) == 0
               for name, n in athletes.items()):
            continue
        phase = phases_by_game.get(mid)
        valid_phases = bool(phase and abs(sum(phase.values()) - attacks) < 1e-9)
        if not valid_phases:
            continue  # Individual and team totals must reconcile before allocation.
        for name, n in athletes.items():
            if n <= 0:
                continue
            person_total = sum(exposure[mid, name, pos] for pos in range(1, 7))
            for pos in range(1, 7):
                amount = n * exposure[mid, name, pos] / person_total
                if amount <= 0:
                    continue
                allocation[pos]['all'][name] += amount
                per_game[pos][mid]['all'][name] += amount
                active_games[pos].add(mid)
                if valid_phases:
                    for phase_name in PHASES:
                        value = amount * phase[phase_name] / attacks
                        allocation[pos][phase_name][name] += value
                        per_game[pos][mid][phase_name][name] += value
                    phase_games[pos].add(mid)
    return {pos: dict(all=dict(phase_map['all']),
                      **{key: dict(phase_map[key]) for key in PHASES},
                      games=len(active_games[pos]), phase_games=len(phase_games[pos]),
                      game_allocations={mid: {phase: dict(values) for phase, values in phases.items()}
                                        for mid, phases in per_game[pos].items()})
            for pos, phase_map in allocation.items()}
