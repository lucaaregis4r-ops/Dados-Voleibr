"""Versioned metric catalog without database dependencies."""
VERSION = 'scouting-1.0'
# key, label, numerator columns, denominator, class, definition
METRICS = [
    ('so', 'Side-Out', ['sideout_points'], 'sideout_receptions', 'DERIVADO', 'Rallies vencidos recebendo / rallies de recepção'),
    ('bp', 'Break Point', ['breakpoint_points'], 'breakpoint_serves', 'DERIVADO', 'Rallies vencidos sacando / rallies de saque'),
    ('kill', 'Attack Kill%', ['attack_points'], 'attack_attempts', 'DERIVADO', 'Kills / tentativas de ataque'),
    ('eff', 'Eficiência de ataque', ['attack_points', '-attack_errors', '-attack_blocked'], 'attack_attempts', 'DERIVADO', '(kills − erros − bloqueios sofridos) / tentativas'),
    ('positive', 'Passe positivo', ['reception_positive_count'], 'positive_receptions', 'DERIVADO', 'Média dos percentuais publicados ponderada por recepções; contagem aproximada'),
    ('excellent', 'Passe excelente', ['reception_excellent_count'], 'excellent_receptions', 'DERIVADO', 'Média dos percentuais publicados ponderada por recepções; contagem aproximada'),
    ('error', 'Erro de saque', ['serve_errors'], 'serve_attempts', 'DERIVADO', 'Erros de saque / saques; não representa erros por rally'),
    ('rec_error', 'Erro de recepção', ['reception_errors'], 'reception_attempts', 'DERIVADO', 'Erros de recepção / recepções'),
    ('attack_error', 'Erro de ataque', ['attack_errors'], 'attack_attempts', 'DERIVADO', 'Erros de ataque / tentativas'),
]
for prefix, label in [('pos_rec', 'K1 / passe +'), ('neg_rec', 'K1 / passe −'), ('trans', 'K2 / transição')]:
    METRICS.extend([
        (prefix, label + ' · Kill%', [prefix+'_att_points'], prefix+'_att_attempts', 'DERIVADO', 'Kills reconstruídos do percentual arredondado do relatório / tentativas'),
        (prefix+'_eff', label + ' · eficiência', [prefix+'_att_points', '-'+prefix+'_att_errors', '-'+prefix+'_att_blocked'], prefix+'_att_attempts', 'DERIVADO', '(kills reconstruídos − erros − bloqueados) / tentativas'),
        (prefix+'_error', label + ' · erro', [prefix+'_att_errors'], prefix+'_att_attempts', 'DERIVADO', 'Erros / tentativas na fase'),
        (prefix+'_blocked', label + ' · bloqueado', [prefix+'_att_blocked'], prefix+'_att_attempts', 'DERIVADO', 'Bloqueados / tentativas na fase'),
    ])
