"""Temporal audit of team attack shares. Run from repository root.

Conditional diagnostic: each test game's attackers are known when normalizing
both methods. This does not validate next-ball, rotation, or phase predictions.
"""
import collections
import itertools
import json
import math
from pathlib import Path


def load(name):
    return json.loads((Path('exports') / f'{name}.json').read_text())


def main():
    matches = {m['match_id']: m for m in load('matches')
               if m.get('validation_status') == 'VALID' and m.get('date') and m.get('season')}
    games = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(float)))
    for player in load('players'):
        match = matches.get(player['match_id'])
        count, team, name = player.get('attack_attempts'), player.get('team'), player.get('player_name')
        if (not match or not team or not name or not isinstance(count, (int, float))
                or not math.isfinite(count) or count < 0):
            continue
        cohort = (match.get('competition'), match.get('category'), match.get('gender'), match['season'], team)
        games[cohort][(match['date'][:10], match['match_id'])][name] += count

    rows, eligible = [], 0
    for cohort, team_games in games.items():
        history, played = collections.Counter(), 0
        # Games on the same day cannot train one another without reliable times.
        for _, day in itertools.groupby(sorted(team_games), key=lambda k: k[0]):
            pending = []
            for game in day:
                current = {n: v for n, v in team_games[game].items() if v > 0}
                total = sum(current.values())
                if not total:
                    continue
                if played >= 3:
                    eligible += 1
                    if all(history[n] > 0 for n in current):
                        names = sorted(current)
                        hist_total = sum(history[n] for n in names)
                        observed = {n: current[n] / total for n in names}
                        prior = {n: history[n] / hist_total for n in names}
                        error = sum(abs(observed[n] - prior[n]) for n in names) / 2
                        uniform_error = sum(abs(observed[n] - 1 / len(names)) for n in names) / 2
                        rows.append((cohort, error, uniform_error, total))
                pending.append(current)
            for current in pending:
                history.update(current)
                played += 1
    print(f'Jogos avaliados: {len(rows)} / {eligible} elegíveis; coortes: {len({r[0] for r in rows})}')
    if rows:
        print(f'Desvio médio, histórico: {sum(r[1] for r in rows)/len(rows):.4f}; uniforme: {sum(r[2] for r in rows)/len(rows):.4f}')
        print(f'Histórico mais próximo em {sum(r[1] < r[2] for r in rows)} jogos; ataques: {sum(r[3] for r in rows):.0f}')
    print('Diagnóstico condicional ao conjunto de atacantes do jogo; não valida fase, rotação ou próxima bola.')


if __name__ == '__main__':
    main()
