"""Canonical, machine-readable definitions shared by code, UI and methodology."""
from dataclasses import dataclass,asdict
from enum import Enum
from cbv.metrics.legacy import METRICS as LEGACY_BINDINGS

VERSION='atlas-metrics-1.0'

class MetricClass(str,Enum):
    OBSERVED='OBSERVADO'
    RECONSTRUCTED='RECONSTRUÍDO'
    DERIVED='DERIVADO'
    MODELED='MODELADO'
    EXPERIMENTAL='EXPERIMENTAL'

@dataclass(frozen=True)
class Metric:
    metric_id:str
    name:str
    short_name:str
    description:str
    question_answered:str
    metric_class:str
    formula:str
    numerator:str
    denominator:str
    unit:str
    minimum_data_required:str
    required_sources:tuple
    aggregation_level:str
    sample_definition:str
    small_sample_policy:str
    confidence_interval:str
    shrinkage_method:str
    model_name:str|None
    model_version:str|None
    validation_method:str
    interpretation:str
    limitations:str
    literature_basis:str
    source_notes:str
    introduced_version:str=VERSION
    example:str='Ausência de denominador → NULL, nunca 0%.'
    ui_location:str='Detalhe contextual e Dados → caderno.'
    not_interpreted_as:str='Não demonstra causalidade ou qualidade individual.'
    implementation_status:str='IMPLEMENTED'

REGISTRY={}

def register(key,name,formula,cls='DERIVADO',sources=('Match Report',),unit='%',level='equipe/jogo/coorte',**kwargs):
    values=dict(metric_id=key,name=name,short_name=name,description=name,question_answered=f'Qual o valor de {name} neste contexto?',
        metric_class=cls,formula=formula,numerator=formula.split('/')[0],denominator=formula.split('/',1)[1] if '/' in formula else 'Não se aplica',
        unit=unit,minimum_data_required='Fonte presente e denominador positivo; elegibilidade explícita.',required_sources=sources,
        aggregation_level=level,sample_definition='Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.',
        small_sample_policy='Exibir n; amostra pequena não sustenta ranking conclusivo.',confidence_interval='Não aplicável sem hipótese probabilística válida.',
        shrinkage_method='Nenhum na medida bruta.',model_name=None,model_version=None,
        validation_method='Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.',
        interpretation='Comparar somente definições e fontes equivalentes.',limitations='Cobertura parcial; associação descritiva sujeita a adversário e escalação.',
        literature_basis='Definição operacional do projeto; não reivindica padronização externa.',source_notes='Sem eventos individuais, não atribuir ponto a atacante ou levantadora.')
    values.update(kwargs);REGISTRY[key]=Metric(**values)

for key,label,columns,denominator,cls,formula in LEGACY_BINDINGS:
    if key=='so':formula='Pontos creditados em recepção no relatório / recepções do relatório'
    if key=='bp':formula='Pontos creditados em saque no relatório / saques do relatório'
    approximate=key in ('positive','excellent') or key.startswith(('pos_rec','neg_rec','trans'))
    register(key,label,formula,cls,numerator=' + '.join(columns),denominator=denominator,
        confidence_interval='Wilson 95% somente para contagem binomial exata.' if not approximate and key!='eff' else 'Não calculado: agregado arredondado ou contraste não binomial.',
        limitations='Percentuais arredondados; contagem reconstruída aproximada.' if approximate else 'SO/BP do relatório excluem pontos creditados a erro adversário; não equivalem à sequência completa de placar.' if key in ('so','bp') else 'Agregado sem sequência de contatos.')

for key,name,formula in [
 ('points','Pontos','Contagem de pontos no placar'),('sets','Sets','Sets vencidos e perdidos'),('record','Campanha','Vitórias / jogos'),
 ('serve','Saque','Aces, erros e tentativas publicados'),('reception','Recepção','Contagens publicadas de recepções'),('attack','Ataque','Kills, erros, bloqueados e tentativas'),
 ('block','Bloqueio','Pontos de bloqueio publicados'),('blocked','Bloqueado%','Ataques bloqueados / tentativas'),('rotation_balance','Saldo P1–P6','Pontos ganhos − pontos perdidos na passagem publicada')]:
    register(key,name,formula,'OBSERVADO' if key not in ('record','blocked') else 'DERIVADO',unit='contagem' if key not in ('record','blocked') else '%')
for key,name,formula in [
 ('rally_so','Side-Out do placar','Pontos ganhos recebendo / pontos disputados recebendo'),('rally_bp','Break Point do placar','Pontos ganhos sacando / pontos disputados sacando'),
 ('rotation_so','SO por rotação','Pontos ganhos recebendo em P / pontos recebendo em P'),('rotation_bp','BP por rotação','Pontos ganhos sacando em P / pontos sacando em P'),
 ('rotation_matchup','Matchup 6×6','Pontos ganhos em P própria × P adversária / pontos nesse par'),
 ('serve_run','Passagem de saque','Pontos consecutivos ganhos sacando antes do side-out ou fim do set'),
 ('run_survival','Sobrevivência da passagem','Passagens completas com pelo menos k pontos / passagens completas'),('streak','Sequência de pontos','Comprimento de pontos consecutivos ganhos'),
 ('lineup_efficiency','Eficiência da formação','Pontos ganhos com seis atletas reconciliados / rallies com essa formação'),
 ('on_off','On/off bruto','Taxa com atleta presente − taxa sem atleta; apenas presença confiável')]:
    register(key,name,formula,sources=('Scoresheet','Match Report','Libero Report quando exigido'),level='rally/rotação/lineup/equipe',
        source_notes='Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.',
        confidence_interval='Wilson 95% para proporções exatas; não para diferença on/off.',
        limitations='Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.')
for key,name,formula in [
 ('wilson','Intervalo de Wilson','Centro=(p+z²/2n)/(1+z²/n); meia largura=z√(p(1-p)/n+z²/4n²)/(1+z²/n), z=1,95996'),
 ('percentile','Percentil','100 × quantidade de valores inferiores / número de equipes cobertas'),('delta','Delta','Valor da equipe − referência da coorte'),
 ('shrinkage','Empirical Bayes','100 × (k+α)/(n+α+β); prior beta por momentos da coorte'),('trend','Tendência','Métrica em blocos cronológicos de partidas')]:
    register(key,name,formula,unit='pp, % ou intervalo',limitations='Prior descritivo da coorte completa; não usar em previsão temporal retrospectiva. Aproximações de percentuais não são contagens binomiais exatas.')
for key,name,formula in [
 ('xso','xSO','E[P(ganhar recebendo) | histórico anterior à data]'),('xbp','xBP','E[P(ganhar sacando) | histórico anterior à data]'),
 ('soae','SO acima do esperado','SO observado − xSO'),('bpae','BP acima do esperado','BP observado − xBP'),
 ('xpoints','xPoints/100','100 × soma de probabilidades históricas de vitória dos rallies / rallies'),('rotation_ae','Rotation Above Expected','Pontos por 100 − xPoints/100'),
 ('xattack','xAttack','Tentativas atuais × kill% histórico anterior na mesma fase K1+/K1−/K2'),('attack_ae','Attack Above Expected','Kills publicados/reconstruídos − kills esperados'),
 ('wp','Probabilidade de vitória durante o jogo','Recorrência de placar e saque com probabilidade de rally fixada antes do jogo'),('wpa','Win Probability Added','WP_after − WP_before'),
 ('leverage','Sensibilidade do rally','WP(se ganhar o próximo ponto) − WP(se perder o próximo ponto)'),
 ('pressure_map','Mapa de pressão','Taxas por rotação e faixas de leverage estimadas em histórico anterior'),
 ('contextual_effect','Efeito contextual estimado','Contraste regularizado com/sem atleta condicionado a adversário, rotação e companheiras'),
 ('opponent_rating','Força ajustada por adversário','Efeito regularizado de equipe e oponente sobre resultado da fase')]:
    register(key,name,formula,'EXPERIMENTAL',sources=('Histórico de fontes reconciliadas',),level='rally/rotação/equipe/modelo',model_name=name,model_version='atlas-context-v1',
        minimum_data_required='Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.',
        validation_method='Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.',
        limitations='Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.',implementation_status='CONDITIONAL')
for key,name,formula in [('crunch','Crunch','Placar de ambos ≥ alvo−5 e diferença ≤2'),('super_crunch','Super Crunch','Placar de ambos ≥ alvo−2 e diferença ≤1')]:
    register(key,name,formula,sources=('Sequência de placar reconciliada',),level='rally',unit='booleano',limitations='Convenção descritiva local, explícita; não mede leverage nem psicologia.')
for key,name,formula in [('prematch','Previsão pré-jogo','sigmoid(w · diferenças de SO/BP/eff/K1+/K1−/K2 e forma recente)'),
 ('logistic','Regressão logística L2 baseline','Argmin log loss + penalidade L2; escala fixa diferenças/20; sem intercepto'),
 ('brier','Brier Score','Média de (p−y)²'),('log_loss','Log Loss','−média[y log(p)+(1−y) log(1−p)]'),
 ('calibration','Curva de calibração','Frequência observada × probabilidade média por faixa do favorito'),
 ('calibration_error','Calibration Error','Soma de n_faixa × |frequência−p médio| / n'),('accuracy','Acurácia','Previsões com favorito correto / previsões')]:
    register(key,name,formula,'MODELADO' if key in ('prematch','logistic') else 'DERIVADO',sources=('Match Report legado','Resultados'),level='jogo/coorte/modelo',
        model_name='logistic-l2' if key in ('prematch','logistic') else None,model_version='logistic-l2-v1',
        minimum_data_required='Mínimo 20 exemplos de treino com features históricas completas.',
        validation_method='Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.',
        limitations='Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.',unit='probabilidade ou escore')
for key,name,formula in [('setter_distribution','Distribuição estimada — experimental','Pesos heurísticos normalizados sobre atacantes elegíveis'),
 ('entropy','Entropia do modelo','−Σ p_i log₂(p_i) da distribuição estimada'),('predictability_efficiency','Diversidade × eficiência','Associação entre entropia do modelo e eficiência ofensiva agregada')]:
    register(key,name,formula,'EXPERIMENTAL',sources=('Volume ofensivo agregado','Funções estimadas'),level='equipe/rotação/condição de passe',
        model_name='setter-heuristic',model_version='legacy-experimental',limitations='Sem encadeamento recepção→levantamento→ataque observado. Pesos heurísticos não validados; entropia alta não significa melhor.',implementation_status='LEGACY_EXPERIMENTAL')


def catalog():return [asdict(m) for m in REGISTRY.values()]


def legacy_bindings():
    return [(key,label,cols,den,REGISTRY[key].metric_class,REGISTRY[key].formula) for key,label,cols,den,_,_ in LEGACY_BINDINGS]
