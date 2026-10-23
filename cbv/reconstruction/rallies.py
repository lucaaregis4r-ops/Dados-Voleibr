"""Score increments and service-state transitions; never infer a responsible attacker."""
from collections import Counter


class ReconstructionError(ValueError):
    pass


def rotation_after_sideout(position):
    """Setter zone progression: P1→P6→P5→P4→P3→P2→P1."""
    return 6 if position==1 else position-1


def rebuild_from_scoresheet(sheet,team_map,expected_sets):
    all_rallies=[];events=[]
    if len(sheet['sets'])!=len(expected_sets):
        raise ReconstructionError('Quantidade de sets da súmula diverge do relatório')
    for panel,expected in zip(sheet['sets'],expected_sets):
        number=panel['set_number'];groups={team_map[t['team_letter']]:t for t in panel['teams']}
        if set(groups)!={'home','away'}:
            raise ReconstructionError('Identificação de equipes ambígua')
        if any(not t['grid_complete'] for t in groups.values()):
            raise ReconstructionError('Grade de passagens de saque incompleta')
        if groups['home']['receiving_first']==groups['away']['receiving_first']:
            raise ReconstructionError('Primeiro sacador não identificado por marcação inequívoca')
        serving='away' if groups['home']['receiving_first'] else 'home'
        score=dict(home=0,away=0);turn=dict(home=0,away=0);relative=dict(home=1,away=1)
        target=dict(home=expected['home_points'],away=expected['away_points'])
        if target['home']==target['away']:
            raise ReconstructionError('Set empatado não é encerrado')
        rally_number=0
        def point(winner):
            nonlocal serving,rally_number
            before=dict(score);rally_number+=1;receiver='away' if serving=='home' else 'home'
            row=dict(rally_id=f"{sheet['match_id']}:{number}:{rally_number}",match_id=sheet['match_id'],set_number=number,rally_number=rally_number,
                score_home_before=score['home'],score_away_before=score['away'],serving_side=serving,receiving_side=receiver,winner_side=winner,
                home_relative_rotation=relative['home'],away_relative_rotation=relative['away'],home_rotation=None,away_rotation=None,
                home_setter_position=None,away_setter_position=None,is_breakpoint=winner==serving,is_sideout=winner!=serving,
                metric_class='RECONSTRUÍDO',source_type='SCORESHEET_SERVICE_TURNS',rotation_source='UNKNOWN',rotation_confidence='UNKNOWN',
                raw_event={'service_turn':dict(turn),'source':'scoresheet'},timestamp=None)
            score[winner]+=1
            row.update(score_home_after=score['home'],score_away_after=score['away'])
            all_rallies.append(row)
            if winner!=serving:
                relative[winner]=rotation_after_sideout(relative[winner])
            serving=winner
            if score[winner]>target[winner]:
                raise ReconstructionError('Sequência ultrapassou o placar de referência')
        for _ in range(1000):
            if score==target:
                break
            side=serving;ends=groups[side]['service_ends'];i=turn[side]
            if i>=len(ends):
                raise ReconstructionError(f'Set {number}: passagens de saque esgotadas em {score}')
            end=ends[i];turn[side]+=1
            if end<score[side]:
                raise ReconstructionError(f'Set {number}: pontuação de saque regressiva')
            while score[side]<end:
                point(side)
            if score==target:
                break
            opponent='away' if side=='home' else 'home'
            point(opponent)
        if score!=target:
            raise ReconstructionError('Placar final divergente')
        for side in ('home','away'):
            remaining=groups[side]['service_ends'][turn[side]:]
            # The sheet closes a receiving winner's next service cell at the final score,
            # even though no subsequent serve takes place. It adds no rally.
            if remaining and remaining!=[target[side]]:
                raise ReconstructionError('Passagens extras após encerramento do set')
        for side,group in groups.items():
            for e in group['substitutions']+group['timeouts']:
                event=dict(e,set_number=number,team_side=side)
                if 'own_score' in e:
                    event['score_home']=e['own_score'] if side=='home' else e['opponent_score']
                    event['score_away']=e['opponent_score'] if side=='home' else e['own_score']
                events.append(event)
    return all_rallies,events


def reconcile(rallies,expected_sets,tactical=None):
    checks=[];warnings=[]
    for s in expected_sets:
        rows=[r for r in rallies if r['set_number']==s['set_number']]
        checks.append(dict(check='set_score',set=s['set_number'],passed=bool(rows) and (rows[-1]['score_home_after'],rows[-1]['score_away_after'])==(s['home_points'],s['away_points'])))
        checks.append(dict(check='point_count',set=s['set_number'],passed=len(rows)==s['home_points']+s['away_points']))
        for previous,current in zip(rows,rows[1:]):
            if current['serving_side']!=previous['winner_side']:
                checks.append(dict(check='server_transition',passed=False))
    if tactical:
        for side,t in tactical.items():
            so=sum(r['winner_side']==side and r['serving_side']!=side for r in rallies)
            bp=sum(r['winner_side']==side and r['serving_side']==side for r in rallies)
            for name,actual,expected in [('sideout_points',so,t.get('sideout_points')),('breakpoint_points',bp,t.get('breakpoint_points'))]:
                if expected is not None and actual!=expected:
                    warnings.append(dict(check=name,side=side,reconstructed=actual,report=expected))
    failed=any(not c['passed'] for c in checks)
    status='FAILED' if failed else 'VALID_WITH_WARNINGS' if warnings else 'VALID'
    return dict(status=status,checks=checks,warnings=warnings,reconstruction_version='rallies-1.0')
