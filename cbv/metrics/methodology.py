"""Deterministic documentation generation; committed notebook is a build artifact."""
from pathlib import Path
from cbv.metrics.registry import REGISTRY,VERSION

INTRO='''# Caderno metodológico — Atlas Tático

Gerado por `python -m cbv.metrics.methodology`. Não editar este arquivo manualmente.

## Fontes, unidades e ausência

OBSERVADO: publicado pela CBV. RECONSTRUÍDO: transformação determinística da fonte.
DERIVADO: fórmula sobre registros. MODELADO: estimativa com validação registrada.
EXPERIMENTAL: hipótese ou modelo cuja validação ainda é insuficiente.

A súmula registra placares de encerramento das passagens de saque. A sequência
reconstruída inclui todos os pontos do placar, mas não revela ação responsável,
timestamp nem se o ponto foi administrativo. O widget original está bloqueado
(HTTP 403); nenhum endpoint foi presumido. O adaptador estruturado aceita somente
schema explicitamente declarado; isso não comprova cobertura de um feed original.

SO/BP legados são os pontos creditados no Match Report. Excluem erros do adversário;
seus denominadores não coincidem necessariamente com rallies do placar. O baseline
usa essa série preservada. `rally_so` e `rally_bp` usam a sequência completa. Nunca
misturar as séries. Comparações por competição incluem apenas registros cobertos.

Uma rotação absoluta exige marcador independente de levantadora inicial. O ciclo é
P1→P6→P5→P4→P3→P2. Sem marcador, apenas ciclo relativo; P desconhecido é NULL.
Presença real exige substituições e controle de líbero reconciliados. Formação
registrada sem controle de líbero é parcial e não alimenta on/off.

## Avaliação e reprodutibilidade

Datas são blocos indivisíveis: features e treino usam somente datas anteriores à
partida avaliada. Sem horário validado, jogos do mesmo dia não se predizem entre si.
A regressão logística L2 original é o baseline obrigatório. Modelos novos não o
substituem sem comparação na mesma amostra fora do treino. Medidas descritivas de
coorte completa não podem entrar retrospectivamente como features temporais.

Brier e log loss menores são melhores; calibração confronta probabilidades e
frequências. Acurácia é secundária. Pontos não são observações independentes quando
agrupados por jogo; intervalos simples são descritivos e não certificam causalidade.

## Referências metodológicas

Wilson (1927), intervalo de proporção; Brier (1950), escore probabilístico;
Shannon (1948), entropia; regressão logística penalizada e validação temporal
walk-forward. Fórmulas específicas e convenções locais estão registradas abaixo;
nenhuma sigla implica identidade com modelo externo ou validação publicada.
'''
LABELS={'question_answered':'Pergunta','description':'Definição','metric_class':'Classe','formula':'Fórmula','numerator':'Numerador',
'denominator':'Denominador','unit':'Unidade','required_sources':'Fontes','aggregation_level':'Granularidade','minimum_data_required':'Dados mínimos',
'sample_definition':'Amostra','small_sample_policy':'Amostra pequena','confidence_interval':'Intervalo','shrinkage_method':'Ajuste de amostra',
'model_name':'Modelo','model_version':'Versão do modelo','validation_method':'Validação','interpretation':'Interpretação','limitations':'Limitações',
'example':'Exemplo numérico ou caso limite','ui_location':'Interface','not_interpreted_as':'Como não interpretar','literature_basis':'Referência',
'source_notes':'Notas da fonte','introduced_version':'Introduzida em','implementation_status':'Disponibilidade'}


def render():
    parts=[INTRO,f'\nVersão do catálogo: `{VERSION}`. Métricas registradas: {len(REGISTRY)}.\n']
    for key,m in REGISTRY.items():
        parts.append(f'\n## {m.name} — `{key}`\n')
        for field,label in LABELS.items():
            value=getattr(m,field)
            if isinstance(value,tuple):value=', '.join(value)
            if isinstance(value,str):value=value.strip()
            parts.append(f'\n**{label}:** {value if value is not None else "Não se aplica"}\n')
    return ''.join(parts)


def generate(path=None):
    path=Path(path or Path(__file__).resolve().parents[2]/'docs/CADERNO_METODOLOGICO.md');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(render(),encoding='utf-8');return path

if __name__=='__main__':generate()
