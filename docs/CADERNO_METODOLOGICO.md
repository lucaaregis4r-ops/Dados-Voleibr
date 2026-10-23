# Caderno metodológico — Atlas Tático

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

Versão do catálogo: `atlas-metrics-1.0`. Métricas registradas: 74.

## Side-Out — `so`

**Pergunta:** Qual o valor de Side-Out neste contexto?

**Definição:** Pontos creditados em recepção no relatório / recepções do relatório

**Classe:** DERIVADO

**Fórmula:** 100 × (sideout_points) / sideout_receptions

**Numerador:** sideout_points

**Denominador:** sideout_receptions

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% somente para contagem binomial exata.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** SO/BP do relatório excluem pontos creditados a erro adversário; não equivalem à sequência completa de placar.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Break Point — `bp`

**Pergunta:** Qual o valor de Break Point neste contexto?

**Definição:** Pontos creditados em saque no relatório / saques do relatório

**Classe:** DERIVADO

**Fórmula:** 100 × (breakpoint_points) / breakpoint_serves

**Numerador:** breakpoint_points

**Denominador:** breakpoint_serves

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% somente para contagem binomial exata.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** SO/BP do relatório excluem pontos creditados a erro adversário; não equivalem à sequência completa de placar.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Attack Kill% — `kill`

**Pergunta:** Qual o valor de Attack Kill% neste contexto?

**Definição:** Kills / tentativas de ataque

**Classe:** DERIVADO

**Fórmula:** 100 × (attack_points) / attack_attempts

**Numerador:** attack_points

**Denominador:** attack_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% somente para contagem binomial exata.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Agregado sem sequência de contatos.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Eficiência de ataque — `eff`

**Pergunta:** Qual o valor de Eficiência de ataque neste contexto?

**Definição:** (kills − erros − bloqueios sofridos) / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (attack_points − attack_errors − attack_blocked) / attack_attempts

**Numerador:** attack_points + -attack_errors + -attack_blocked

**Denominador:** attack_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Agregado sem sequência de contatos.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Passe positivo — `positive`

**Pergunta:** Qual o valor de Passe positivo neste contexto?

**Definição:** Média dos percentuais publicados ponderada por recepções; contagem aproximada

**Classe:** DERIVADO

**Fórmula:** 100 × (reception_positive_count) / positive_receptions

**Numerador:** reception_positive_count

**Denominador:** positive_receptions

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Passe excelente — `excellent`

**Pergunta:** Qual o valor de Passe excelente neste contexto?

**Definição:** Média dos percentuais publicados ponderada por recepções; contagem aproximada

**Classe:** DERIVADO

**Fórmula:** 100 × (reception_excellent_count) / excellent_receptions

**Numerador:** reception_excellent_count

**Denominador:** excellent_receptions

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Erro de saque — `error`

**Pergunta:** Qual o valor de Erro de saque neste contexto?

**Definição:** Erros de saque / saques; não representa erros por rally

**Classe:** DERIVADO

**Fórmula:** 100 × (serve_errors) / serve_attempts

**Numerador:** serve_errors

**Denominador:** serve_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% somente para contagem binomial exata.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Agregado sem sequência de contatos.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Erro de recepção — `rec_error`

**Pergunta:** Qual o valor de Erro de recepção neste contexto?

**Definição:** Erros de recepção / recepções

**Classe:** DERIVADO

**Fórmula:** 100 × (reception_errors) / reception_attempts

**Numerador:** reception_errors

**Denominador:** reception_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% somente para contagem binomial exata.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Agregado sem sequência de contatos.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Erro de ataque — `attack_error`

**Pergunta:** Qual o valor de Erro de ataque neste contexto?

**Definição:** Erros de ataque / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (attack_errors) / attack_attempts

**Numerador:** attack_errors

**Denominador:** attack_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% somente para contagem binomial exata.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Agregado sem sequência de contatos.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe + · Kill% — `pos_rec`

**Pergunta:** Qual o valor de K1 / passe + · Kill% neste contexto?

**Definição:** Kills reconstruídos do percentual arredondado do relatório / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (pos_rec_att_points) / pos_rec_att_attempts

**Numerador:** pos_rec_att_points

**Denominador:** pos_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe + · eficiência — `pos_rec_eff`

**Pergunta:** Qual o valor de K1 / passe + · eficiência neste contexto?

**Definição:** (kills reconstruídos − erros − bloqueados) / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (pos_rec_att_points − pos_rec_att_errors − pos_rec_att_blocked) / pos_rec_att_attempts

**Numerador:** pos_rec_att_points + -pos_rec_att_errors + -pos_rec_att_blocked

**Denominador:** pos_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe + · erro — `pos_rec_error`

**Pergunta:** Qual o valor de K1 / passe + · erro neste contexto?

**Definição:** Erros / tentativas na fase

**Classe:** DERIVADO

**Fórmula:** 100 × (pos_rec_att_errors) / pos_rec_att_attempts

**Numerador:** pos_rec_att_errors

**Denominador:** pos_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe + · bloqueado — `pos_rec_blocked`

**Pergunta:** Qual o valor de K1 / passe + · bloqueado neste contexto?

**Definição:** Bloqueados / tentativas na fase

**Classe:** DERIVADO

**Fórmula:** 100 × (pos_rec_att_blocked) / pos_rec_att_attempts

**Numerador:** pos_rec_att_blocked

**Denominador:** pos_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe − · Kill% — `neg_rec`

**Pergunta:** Qual o valor de K1 / passe − · Kill% neste contexto?

**Definição:** Kills reconstruídos do percentual arredondado do relatório / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (neg_rec_att_points) / neg_rec_att_attempts

**Numerador:** neg_rec_att_points

**Denominador:** neg_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe − · eficiência — `neg_rec_eff`

**Pergunta:** Qual o valor de K1 / passe − · eficiência neste contexto?

**Definição:** (kills reconstruídos − erros − bloqueados) / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (neg_rec_att_points − neg_rec_att_errors − neg_rec_att_blocked) / neg_rec_att_attempts

**Numerador:** neg_rec_att_points + -neg_rec_att_errors + -neg_rec_att_blocked

**Denominador:** neg_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe − · erro — `neg_rec_error`

**Pergunta:** Qual o valor de K1 / passe − · erro neste contexto?

**Definição:** Erros / tentativas na fase

**Classe:** DERIVADO

**Fórmula:** 100 × (neg_rec_att_errors) / neg_rec_att_attempts

**Numerador:** neg_rec_att_errors

**Denominador:** neg_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K1 / passe − · bloqueado — `neg_rec_blocked`

**Pergunta:** Qual o valor de K1 / passe − · bloqueado neste contexto?

**Definição:** Bloqueados / tentativas na fase

**Classe:** DERIVADO

**Fórmula:** 100 × (neg_rec_att_blocked) / neg_rec_att_attempts

**Numerador:** neg_rec_att_blocked

**Denominador:** neg_rec_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K2 / transição · Kill% — `trans`

**Pergunta:** Qual o valor de K2 / transição · Kill% neste contexto?

**Definição:** Kills reconstruídos do percentual arredondado do relatório / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (trans_att_points) / trans_att_attempts

**Numerador:** trans_att_points

**Denominador:** trans_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K2 / transição · eficiência — `trans_eff`

**Pergunta:** Qual o valor de K2 / transição · eficiência neste contexto?

**Definição:** (kills reconstruídos − erros − bloqueados) / tentativas

**Classe:** DERIVADO

**Fórmula:** 100 × (trans_att_points − trans_att_errors − trans_att_blocked) / trans_att_attempts

**Numerador:** trans_att_points + -trans_att_errors + -trans_att_blocked

**Denominador:** trans_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K2 / transição · erro — `trans_error`

**Pergunta:** Qual o valor de K2 / transição · erro neste contexto?

**Definição:** Erros / tentativas na fase

**Classe:** DERIVADO

**Fórmula:** 100 × (trans_att_errors) / trans_att_attempts

**Numerador:** trans_att_errors

**Denominador:** trans_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## K2 / transição · bloqueado — `trans_blocked`

**Pergunta:** Qual o valor de K2 / transição · bloqueado neste contexto?

**Definição:** Bloqueados / tentativas na fase

**Classe:** DERIVADO

**Fórmula:** 100 × (trans_att_blocked) / trans_att_attempts

**Numerador:** trans_att_blocked

**Denominador:** trans_att_attempts

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não calculado: agregado arredondado ou contraste não binomial.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Percentuais arredondados; contagem reconstruída aproximada.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Pontos — `points`

**Pergunta:** Qual o valor de Pontos neste contexto?

**Definição:** Pontos

**Classe:** OBSERVADO

**Fórmula:** Contagem de pontos no placar

**Numerador:** Contagem de pontos no placar

**Denominador:** Não se aplica

**Unidade:** contagem

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Sets — `sets`

**Pergunta:** Qual o valor de Sets neste contexto?

**Definição:** Sets

**Classe:** OBSERVADO

**Fórmula:** Sets vencidos e perdidos

**Numerador:** Sets vencidos e perdidos

**Denominador:** Não se aplica

**Unidade:** contagem

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Campanha — `record`

**Pergunta:** Qual o valor de Campanha neste contexto?

**Definição:** Campanha

**Classe:** DERIVADO

**Fórmula:** Contagens de jogos, vitórias e derrotas; campanha apresentada como vitórias–derrotas

**Numerador:** Vitórias

**Denominador:** jogos

**Unidade:** jogos, vitórias e derrotas

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Saque — `serve`

**Pergunta:** Qual o valor de Saque neste contexto?

**Definição:** Saque

**Classe:** OBSERVADO

**Fórmula:** Aces, erros e tentativas publicados

**Numerador:** Aces, erros e tentativas publicados

**Denominador:** Não se aplica

**Unidade:** contagem

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Recepção — `reception`

**Pergunta:** Qual o valor de Recepção neste contexto?

**Definição:** Recepção

**Classe:** OBSERVADO

**Fórmula:** Contagens publicadas de recepções

**Numerador:** Contagens publicadas de recepções

**Denominador:** Não se aplica

**Unidade:** contagem

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Ataque — `attack`

**Pergunta:** Qual o valor de Ataque neste contexto?

**Definição:** Ataque

**Classe:** OBSERVADO

**Fórmula:** Kills, erros, bloqueados e tentativas

**Numerador:** Kills, erros, bloqueados e tentativas

**Denominador:** Não se aplica

**Unidade:** contagem

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Bloqueio — `block`

**Pergunta:** Qual o valor de Bloqueio neste contexto?

**Definição:** Bloqueio

**Classe:** OBSERVADO

**Fórmula:** Pontos de bloqueio publicados

**Numerador:** Pontos de bloqueio publicados

**Denominador:** Não se aplica

**Unidade:** contagem

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Bloqueado% — `blocked`

**Pergunta:** Qual o valor de Bloqueado% neste contexto?

**Definição:** Bloqueado%

**Classe:** DERIVADO

**Fórmula:** Ataques bloqueados / tentativas

**Numerador:** Ataques bloqueados

**Denominador:** tentativas

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Saldo P1–P6 — `rotation_balance`

**Pergunta:** Qual o valor de Saldo P1–P6 neste contexto?

**Definição:** Saldo P1–P6

**Classe:** OBSERVADO

**Fórmula:** Pontos ganhos − pontos perdidos na passagem publicada

**Numerador:** Pontos ganhos − pontos perdidos na passagem publicada

**Denominador:** Não se aplica

**Unidade:** contagem

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Cobertura parcial; associação descritiva sujeita a adversário e escalação.

**Exemplo numérico ou caso limite:** 10 pontos ganhos e 8 perdidos na passagem: saldo +2.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Side-Out do placar — `rally_so`

**Pergunta:** Qual o valor de Side-Out do placar neste contexto?

**Definição:** Side-Out do placar

**Classe:** DERIVADO

**Fórmula:** Pontos ganhos recebendo / pontos disputados recebendo

**Numerador:** Pontos ganhos recebendo

**Denominador:** pontos disputados recebendo

**Unidade:** %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Break Point do placar — `rally_bp`

**Pergunta:** Qual o valor de Break Point do placar neste contexto?

**Definição:** Break Point do placar

**Classe:** DERIVADO

**Fórmula:** Pontos ganhos sacando / pontos disputados sacando

**Numerador:** Pontos ganhos sacando

**Denominador:** pontos disputados sacando

**Unidade:** %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## SO por rotação — `rotation_so`

**Pergunta:** Qual o valor de SO por rotação neste contexto?

**Definição:** SO por rotação

**Classe:** DERIVADO

**Fórmula:** Pontos ganhos recebendo em P / pontos recebendo em P

**Numerador:** Pontos ganhos recebendo em P

**Denominador:** pontos recebendo em P

**Unidade:** %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## BP por rotação — `rotation_bp`

**Pergunta:** Qual o valor de BP por rotação neste contexto?

**Definição:** BP por rotação

**Classe:** DERIVADO

**Fórmula:** Pontos ganhos sacando em P / pontos sacando em P

**Numerador:** Pontos ganhos sacando em P

**Denominador:** pontos sacando em P

**Unidade:** %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Matchup 6×6 — `rotation_matchup`

**Pergunta:** Qual o valor de Matchup 6×6 neste contexto?

**Definição:** Matchup 6×6

**Classe:** DERIVADO

**Fórmula:** Pontos ganhos em P própria × P adversária / pontos nesse par

**Numerador:** Pontos ganhos em P própria × P adversária

**Denominador:** pontos nesse par

**Unidade:** %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Passagem de saque — `serve_run`

**Pergunta:** Qual o valor de Passagem de saque neste contexto?

**Definição:** Passagem de saque

**Classe:** DERIVADO

**Fórmula:** Pontos consecutivos ganhos sacando antes do side-out ou fim do set

**Numerador:** Pontos consecutivos ganhos sacando antes do side-out ou fim do set

**Denominador:** Não se aplica

**Unidade:** pontos ganhos por passagem

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** Após recuperar o saque, equipe ganha 3 BP e perde o próximo: passagem de 3 pontos; 4 saques.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Sobrevivência da passagem — `run_survival`

**Pergunta:** Qual o valor de Sobrevivência da passagem neste contexto?

**Definição:** Sobrevivência da passagem

**Classe:** DERIVADO

**Fórmula:** Passagens completas com pelo menos k pontos / passagens completas

**Numerador:** Passagens completas com pelo menos k pontos

**Denominador:** passagens completas

**Unidade:** probabilidade 0–1; interface em %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Sequência de pontos — `streak`

**Pergunta:** Qual o valor de Sequência de pontos neste contexto?

**Definição:** Sequência de pontos

**Classe:** DERIVADO

**Fórmula:** Comprimento de pontos consecutivos ganhos

**Numerador:** Comprimento de pontos consecutivos ganhos

**Denominador:** Não se aplica

**Unidade:** pontos consecutivos

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Eficiência da formação — `lineup_efficiency`

**Pergunta:** Qual o valor de Eficiência da formação neste contexto?

**Definição:** Eficiência da formação

**Classe:** DERIVADO

**Fórmula:** Pontos ganhos com seis atletas reconciliados / rallies com essa formação

**Numerador:** Pontos ganhos com seis atletas reconciliados

**Denominador:** rallies com essa formação

**Unidade:** %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## On/off bruto — `on_off`

**Pergunta:** Qual o valor de On/off bruto neste contexto?

**Definição:** On/off bruto

**Classe:** DERIVADO

**Fórmula:** Taxa com atleta presente − taxa sem atleta; apenas presença confiável

**Numerador:** Taxa com atleta presente − taxa sem atleta; apenas presença confiável

**Denominador:** Não se aplica

**Unidade:** %

**Fontes:** Scoresheet, Match Report, Libero Report quando exigido

**Granularidade:** rally/rotação/lineup/equipe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Wilson 95% para proporções exatas; não para diferença on/off.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Rotações absolutas exigem marcador de levantadora observado; lineup e on/off exigem presença de líbero reconciliada. Passagens finais são censuradas.

**Exemplo numérico ou caso limite:** Com atleta 6/10=60%; sem atleta 5/10=50%: diferença bruta +10 pp; sem causalidade.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sequência RECONSTRUÍDA a partir das passagens de saque; não é feed observado. Pontos administrativos podem não representar rally físico.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Intervalo de Wilson — `wilson`

**Pergunta:** Qual o valor de Intervalo de Wilson neste contexto?

**Definição:** Intervalo de Wilson

**Classe:** DERIVADO

**Fórmula:** Centro=(p+z²/2n)/(1+z²/n); meia largura=z√(p(1-p)/n+z²/4n²)/(1+z²/n), z=1,95996

**Numerador:** Centro=(p+z²

**Denominador:** 2n)/(1+z²/n); meia largura=z√(p(1-p)/n+z²/4n²)/(1+z²/n), z=1,95996

**Unidade:** intervalo em %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Prior descritivo da coorte completa; não usar em previsão temporal retrospectiva. Aproximações de percentuais não são contagens binomiais exatas.

**Exemplo numérico ou caso limite:** 6 sucessos em 10: 60%; Wilson 95% aproximadamente 31,3%–83,2%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Wilson (1927), https://doi.org/10.1080/01621459.1927.10502953

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Percentil — `percentile`

**Pergunta:** Qual o valor de Percentil neste contexto?

**Definição:** Percentil

**Classe:** DERIVADO

**Fórmula:** 100 × (quantidade de valores inferiores + 0,5 × quantidade de empates) / equipes cobertas

**Numerador:** 100 × (quantidade de valores inferiores + 0,5 × quantidade de empates)

**Denominador:** equipes cobertas

**Unidade:** percentil 0–100

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Prior descritivo da coorte completa; não usar em previsão temporal retrospectiva. Aproximações de percentuais não são contagens binomiais exatas.

**Exemplo numérico ou caso limite:** Taxas 40, 50, 50, 60: valor 50 tem (1+0,5×2)/4=50º percentil.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Delta — `delta`

**Pergunta:** Qual o valor de Delta neste contexto?

**Definição:** Delta

**Classe:** DERIVADO

**Fórmula:** Valor da equipe − referência da coorte

**Numerador:** Valor da equipe − referência da coorte

**Denominador:** Não se aplica

**Unidade:** pp

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Prior descritivo da coorte completa; não usar em previsão temporal retrospectiva. Aproximações de percentuais não são contagens binomiais exatas.

**Exemplo numérico ou caso limite:** Equipe=60%; referência=55%: +5 pontos percentuais.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Empirical Bayes — `shrinkage`

**Pergunta:** Qual o valor de Empirical Bayes neste contexto?

**Definição:** Empirical Bayes

**Classe:** MODELADO

**Fórmula:** 100 × (k+α)/(n+α+β); prior beta por momentos da coorte

**Numerador:** 100 × (k+α)

**Denominador:** (n+α+β); prior beta por momentos da coorte

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** beta-binomial empirical Bayes

**Versão do modelo:** eb-moments-v1

**Validação:** Prior por momentos, mínimo 3 equipes com contagens binomiais exatas; ajuste descritivo da coorte completa, não feature temporal.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Prior descritivo da coorte completa; não usar em previsão temporal retrospectiva. Aproximações de percentuais não são contagens binomiais exatas.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Tendência — `trend`

**Pergunta:** Qual o valor de Tendência neste contexto?

**Definição:** Tendência

**Classe:** DERIVADO

**Fórmula:** Razão das somas dos últimos cinco jogos com data, incluindo o jogo do ponto da série

**Numerador:** Razão das somas dos últimos cinco jogos com data, incluindo o jogo do ponto da série

**Denominador:** Não se aplica

**Unidade:** %

**Fontes:** Match Report

**Granularidade:** equipe/jogo/coorte

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Prior descritivo da coorte completa; não usar em previsão temporal retrospectiva. Aproximações de percentuais não são contagens binomiais exatas.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## xSO — `xso`

**Pergunta:** Qual o valor de xSO neste contexto?

**Definição:** xSO

**Classe:** EXPERIMENTAL

**Fórmula:** E[P(ganhar recebendo) | histórico anterior à data]

**Numerador:** E[P(ganhar recebendo) | histórico anterior à data]

**Denominador:** Não se aplica

**Unidade:** %

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** xSO

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## xBP — `xbp`

**Pergunta:** Qual o valor de xBP neste contexto?

**Definição:** xBP

**Classe:** EXPERIMENTAL

**Fórmula:** E[P(ganhar sacando) | histórico anterior à data]

**Numerador:** E[P(ganhar sacando) | histórico anterior à data]

**Denominador:** Não se aplica

**Unidade:** %

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** xBP

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## SO acima do esperado — `soae`

**Pergunta:** Qual o valor de SO acima do esperado neste contexto?

**Definição:** SO acima do esperado

**Classe:** EXPERIMENTAL

**Fórmula:** SO observado − xSO

**Numerador:** SO observado − xSO

**Denominador:** Não se aplica

**Unidade:** pp

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** SO acima do esperado

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** SO=64%; xSO=60% na mesma amostra: +4 pp.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## BP acima do esperado — `bpae`

**Pergunta:** Qual o valor de BP acima do esperado neste contexto?

**Definição:** BP acima do esperado

**Classe:** EXPERIMENTAL

**Fórmula:** BP observado − xBP

**Numerador:** BP observado − xBP

**Denominador:** Não se aplica

**Unidade:** pp

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** BP acima do esperado

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** BP=36%; xBP=32% na mesma amostra: +4 pp.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## xPoints/100 — `xpoints`

**Pergunta:** Qual o valor de xPoints/100 neste contexto?

**Definição:** xPoints/100

**Classe:** EXPERIMENTAL

**Fórmula:** 100 × soma de probabilidades históricas de vitória dos rallies / rallies

**Numerador:** 100 × soma de probabilidades históricas de vitória dos rallies

**Denominador:** rallies

**Unidade:** pontos por 100 rallies

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** xPoints/100

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** Probabilidades 0,6 e 0,4 em dois rallies: xPoints/100=50.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Rotation Above Expected — `rotation_ae`

**Pergunta:** Qual o valor de Rotation Above Expected neste contexto?

**Definição:** Rotation Above Expected

**Classe:** EXPERIMENTAL

**Fórmula:** Pontos por 100 − xPoints/100

**Numerador:** Pontos por 100 − xPoints

**Denominador:** 100

**Unidade:** pp

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Rotation Above Expected

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## xAttack — `xattack`

**Pergunta:** Qual o valor de xAttack neste contexto?

**Definição:** xAttack

**Classe:** EXPERIMENTAL

**Fórmula:** Tentativas atuais × kill% histórico anterior na mesma fase K1+/K1−/K2

**Numerador:** Tentativas atuais × kill% histórico anterior na mesma fase K1+

**Denominador:** K1−/K2

**Unidade:** kills esperados; kill% esperado em %

**Fontes:** Match Report validado, Identidade e data da partida

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** xAttack

**Versão do modelo:** phase-prior-v1

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 10 ataques × expectativa histórica de 40%: 4 kills esperados.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Attack Above Expected — `attack_ae`

**Pergunta:** Qual o valor de Attack Above Expected neste contexto?

**Definição:** Attack Above Expected

**Classe:** EXPERIMENTAL

**Fórmula:** Kills publicados/reconstruídos − kills esperados

**Numerador:** Kills publicados

**Denominador:** reconstruídos − kills esperados

**Unidade:** kills

**Fontes:** Match Report validado, Identidade e data da partida

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Attack Above Expected

**Versão do modelo:** phase-prior-v1

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 6 kills e 4 esperados: +2 kills, sujeitos a arredondamento da fonte.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Probabilidade de vitória durante o jogo — `wp`

**Pergunta:** Qual o valor de Probabilidade de vitória durante o jogo neste contexto?

**Definição:** Probabilidade de vitória durante o jogo

**Classe:** EXPERIMENTAL

**Fórmula:** Recorrência de placar e saque com probabilidade de rally fixada antes do jogo

**Numerador:** Recorrência de placar e saque com probabilidade de rally fixada antes do jogo

**Denominador:** Não se aplica

**Unidade:** probabilidade 0–1

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Probabilidade de vitória durante o jogo

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Win Probability Added — `wpa`

**Pergunta:** Qual o valor de Win Probability Added neste contexto?

**Definição:** Win Probability Added

**Classe:** EXPERIMENTAL

**Fórmula:** WP_after − WP_before

**Numerador:** WP_after − WP_before

**Denominador:** Não se aplica

**Unidade:** diferença de probabilidade; interface ×100 em pp

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Win Probability Added

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** WP antes=0,45; depois=0,52: WPA=+0,07 (+7 pp).

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Sensibilidade do rally — `leverage`

**Pergunta:** Qual o valor de Sensibilidade do rally neste contexto?

**Definição:** Sensibilidade do rally

**Classe:** EXPERIMENTAL

**Fórmula:** WP(se ganhar o próximo ponto) − WP(se perder o próximo ponto)

**Numerador:** WP(se ganhar o próximo ponto) − WP(se perder o próximo ponto)

**Denominador:** Não se aplica

**Unidade:** sensibilidade 0–1; interface ×100 em pp

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Sensibilidade do rally

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** WP se ganhar=0,60; se perder=0,42: sensibilidade=0,18 (18 pp).

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Mapa de pressão — `pressure_map`

**Pergunta:** Qual o valor de Mapa de pressão neste contexto?

**Definição:** Mapa de pressão

**Classe:** EXPERIMENTAL

**Fórmula:** Taxas por rotação; faixas LOW/MEDIUM/HIGH/VERY_HIGH nos P50/P75/P90 do leverage de dias anteriores; alta pressão = acima de P75

**Numerador:** Taxas por rotação; faixas LOW

**Denominador:** MEDIUM/HIGH/VERY_HIGH nos P50/P75/P90 do leverage de dias anteriores; alta pressão = acima de P75

**Unidade:** % e pp por faixa de leverage

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Mapa de pressão

**Versão do modelo:** atlas-rally-beta-v2

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Efeito contextual estimado — `contextual_effect`

**Pergunta:** Qual o valor de Efeito contextual estimado neste contexto?

**Definição:** Efeito contextual estimado

**Classe:** EXPERIMENTAL

**Fórmula:** Coeficiente de presença em regressão logística L2=100, com adversário, rotação, saque, placar/set e seis companheiras; unidade log-odds

**Numerador:** Contraste regularizado com

**Denominador:** sem atleta condicionado a adversário, rotação e companheiras

**Unidade:** log-odds

**Fontes:** Histórico de fontes reconciliadas

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Presença HIGH com seis nomes; ≥3 jogos anteriores; ≥5 jogos de avaliação; ≥20 pontos com/sem atleta.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Efeito contextual estimado

**Versão do modelo:** lineup-context-l2-v1

**Validação:** Blocos de dia; Brier e log loss médios por jogo menores e ECE não maior na mesma amostra contra contexto sem atletas; manter NULL sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Associação, não causalidade; colinearidade de seis atletas identificada pela convenção L2; sem intervalo validado.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Força ajustada por adversário — `opponent_rating`

**Pergunta:** Qual o valor de Força ajustada por adversário neste contexto?

**Definição:** Força ajustada por adversário

**Classe:** EXPERIMENTAL

**Fórmula:** Efeito regularizado de equipe e oponente sobre resultado da fase

**Numerador:** Efeito regularizado de equipe e oponente sobre resultado da fase

**Denominador:** Não se aplica

**Unidade:** força em %; coeficientes em log-odds

**Fontes:** Match Report validado, Identidade e data da partida

**Granularidade:** rally/rotação/equipe/modelo

**Dados mínimos:** Histórico estritamente anterior no mesmo recorte; indisponível sem dados elegíveis.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Força ajustada por adversário

**Versão do modelo:** opponent-logistic-l2-v1

**Validação:** Walk-forward em blocos de dia; comparar Brier e log loss na mesma amostra; não substituir baseline sem ganho.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Só recebe classe MODELADO após validação registrada. Não atribuir WPA individual sem contato observado.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Crunch — `crunch`

**Pergunta:** Qual o valor de Crunch neste contexto?

**Definição:** Crunch

**Classe:** DERIVADO

**Fórmula:** Placar de ambos ≥ alvo−5 e diferença ≤2

**Numerador:** Placar de ambos ≥ alvo−5 e diferença ≤2

**Denominador:** Não se aplica

**Unidade:** booleano

**Fontes:** Sequência de placar reconciliada

**Granularidade:** rally

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Convenção descritiva local, explícita; não mede leverage nem psicologia.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Super Crunch — `super_crunch`

**Pergunta:** Qual o valor de Super Crunch neste contexto?

**Definição:** Super Crunch

**Classe:** DERIVADO

**Fórmula:** Placar de ambos ≥ alvo−2 e diferença ≤1

**Numerador:** Placar de ambos ≥ alvo−2 e diferença ≤1

**Denominador:** Não se aplica

**Unidade:** booleano

**Fontes:** Sequência de placar reconciliada

**Granularidade:** rally

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** Não se aplica

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Convenção descritiva local, explícita; não mede leverage nem psicologia.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Previsão pré-jogo — `prematch`

**Pergunta:** Qual o valor de Previsão pré-jogo neste contexto?

**Definição:** Previsão pré-jogo

**Classe:** MODELADO

**Fórmula:** sigmoid(w · diferenças de SO/BP/eff/K1+/K1−/K2 e forma recente)

**Numerador:** sigmoid(w · diferenças de SO

**Denominador:** BP/eff/K1+/K1−/K2 e forma recente)

**Unidade:** probabilidade ou escore

**Fontes:** Match Report legado, Resultados

**Granularidade:** jogo/coorte/modelo

**Dados mínimos:** Mínimo 20 exemplos de treino com features históricas completas.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** logistic-l2

**Versão do modelo:** logistic-l2-v1

**Validação:** Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Regressão logística L2 baseline — `logistic`

**Pergunta:** Qual o valor de Regressão logística L2 baseline neste contexto?

**Definição:** Regressão logística L2 baseline

**Classe:** MODELADO

**Fórmula:** Argmin log loss + penalidade L2; escala fixa diferenças/20; sem intercepto

**Numerador:** Argmin log loss + penalidade L2; escala fixa diferenças

**Denominador:** 20; sem intercepto

**Unidade:** probabilidade ou escore

**Fontes:** Match Report legado, Resultados

**Granularidade:** jogo/coorte/modelo

**Dados mínimos:** Mínimo 20 exemplos de treino com features históricas completas.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** logistic-l2

**Versão do modelo:** logistic-l2-v1

**Validação:** Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Brier Score — `brier`

**Pergunta:** Qual o valor de Brier Score neste contexto?

**Definição:** Brier Score

**Classe:** DERIVADO

**Fórmula:** Média de (p−y)²

**Numerador:** Média de (p−y)²

**Denominador:** Não se aplica

**Unidade:** probabilidade ou escore

**Fontes:** Match Report legado, Resultados

**Granularidade:** jogo/coorte/modelo

**Dados mínimos:** Mínimo 20 exemplos de treino com features históricas completas.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** logistic-l2-v1

**Validação:** Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.

**Exemplo numérico ou caso limite:** p=0,7, y=1: (0,7−1)²=0,09.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Brier (1950), https://doi.org/10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Log Loss — `log_loss`

**Pergunta:** Qual o valor de Log Loss neste contexto?

**Definição:** Log Loss

**Classe:** DERIVADO

**Fórmula:** −média[y log(p)+(1−y) log(1−p)]

**Numerador:** −média[y log(p)+(1−y) log(1−p)]

**Denominador:** Não se aplica

**Unidade:** probabilidade ou escore

**Fontes:** Match Report legado, Resultados

**Granularidade:** jogo/coorte/modelo

**Dados mínimos:** Mínimo 20 exemplos de treino com features históricas completas.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** logistic-l2-v1

**Validação:** Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.

**Exemplo numérico ou caso limite:** p=0,7, y=1: −ln(0,7)≈0,357.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Curva de calibração — `calibration`

**Pergunta:** Qual o valor de Curva de calibração neste contexto?

**Definição:** Curva de calibração

**Classe:** DERIVADO

**Fórmula:** Frequência observada × probabilidade média por faixa do favorito

**Numerador:** Frequência observada × probabilidade média por faixa do favorito

**Denominador:** Não se aplica

**Unidade:** probabilidade ou escore

**Fontes:** Match Report legado, Resultados

**Granularidade:** jogo/coorte/modelo

**Dados mínimos:** Mínimo 20 exemplos de treino com features históricas completas.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** logistic-l2-v1

**Validação:** Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Calibration Error — `calibration_error`

**Pergunta:** Qual o valor de Calibration Error neste contexto?

**Definição:** Calibration Error

**Classe:** DERIVADO

**Fórmula:** Soma de n_faixa × |frequência−p médio| / n

**Numerador:** Soma de n_faixa × |frequência−p médio|

**Denominador:** n

**Unidade:** probabilidade ou escore

**Fontes:** Match Report legado, Resultados

**Granularidade:** jogo/coorte/modelo

**Dados mínimos:** Mínimo 20 exemplos de treino com features históricas completas.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** logistic-l2-v1

**Validação:** Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Acurácia — `accuracy`

**Pergunta:** Qual o valor de Acurácia neste contexto?

**Definição:** Acurácia

**Classe:** DERIVADO

**Fórmula:** Previsões com favorito correto / previsões

**Numerador:** Previsões com favorito correto

**Denominador:** previsões

**Unidade:** probabilidade ou escore

**Fontes:** Match Report legado, Resultados

**Granularidade:** jogo/coorte/modelo

**Dados mínimos:** Mínimo 20 exemplos de treino com features históricas completas.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** Não se aplica

**Versão do modelo:** logistic-l2-v1

**Validação:** Walk-forward por dia; treinar e construir features apenas com datas anteriores. Mesmo dia não contamina mesmo dia.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Definições SO/BP legadas preservadas; sem inferência causal. Acurácia é secundária à calibração.

**Exemplo numérico ou caso limite:** Ausência de denominador → NULL, nunca 0%.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** IMPLEMENTED

## Distribuição estimada — experimental — `setter_distribution`

**Pergunta:** Qual o valor de Distribuição estimada — experimental neste contexto?

**Definição:** Distribuição estimada — experimental

**Classe:** EXPERIMENTAL

**Fórmula:** Pesos heurísticos normalizados sobre atacantes elegíveis

**Numerador:** Pesos heurísticos normalizados sobre atacantes elegíveis

**Denominador:** Não se aplica

**Unidade:** %

**Fontes:** Volume ofensivo agregado, Funções estimadas

**Granularidade:** equipe/rotação/condição de passe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** setter-heuristic

**Versão do modelo:** setter-heuristic-legacy-v1

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Sem encadeamento recepção→levantamento→ataque observado. Pesos heurísticos não validados; entropia alta não significa melhor.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** LEGACY_EXPERIMENTAL

## Entropia do modelo — `entropy`

**Pergunta:** Qual o valor de Entropia do modelo neste contexto?

**Definição:** Entropia do modelo

**Classe:** EXPERIMENTAL

**Fórmula:** −Σ p_i log₂(p_i) da distribuição estimada

**Numerador:** −Σ p_i log₂(p_i) da distribuição estimada

**Denominador:** Não se aplica

**Unidade:** bits; versão normalizada 0–1

**Fontes:** Volume ofensivo agregado, Funções estimadas

**Granularidade:** equipe/rotação/condição de passe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** setter-heuristic

**Versão do modelo:** setter-heuristic-legacy-v1

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Sem encadeamento recepção→levantamento→ataque observado. Pesos heurísticos não validados; entropia alta não significa melhor.

**Exemplo numérico ou caso limite:** Duas opções equiprováveis: −2×0,5×log₂(0,5)=1 bit.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Shannon (1948), https://doi.org/10.1002/j.1538-7305.1948.tb01338.x

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** LEGACY_EXPERIMENTAL

## Diversidade × eficiência — `predictability_efficiency`

**Pergunta:** Qual o valor de Diversidade × eficiência neste contexto?

**Definição:** Diversidade × eficiência

**Classe:** EXPERIMENTAL

**Fórmula:** Associação entre entropia do modelo e eficiência ofensiva agregada

**Numerador:** Associação entre entropia do modelo e eficiência ofensiva agregada

**Denominador:** Não se aplica

**Unidade:** bits × eficiência em %

**Fontes:** Volume ofensivo agregado, Funções estimadas

**Granularidade:** equipe/rotação/condição de passe

**Dados mínimos:** Fonte presente e denominador positivo; elegibilidade explícita.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** setter-heuristic

**Versão do modelo:** setter-heuristic-legacy-v1

**Validação:** Fixtures e invariantes; modelos exigem avaliação temporal em datas anteriores.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Sem encadeamento recepção→levantamento→ataque observado. Pesos heurísticos não validados; entropia alta não significa melhor.

**Exemplo numérico ou caso limite:** 6 eventos favoráveis em 10 oportunidades elegíveis: 100×6/10=60%. Fórmula com termos negativos subtrai esses termos antes da divisão.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** LEGACY_EXPERIMENTAL

## Distribuição estimada por volume — `lineup_volume_distribution`

**Pergunta:** Qual o valor de Distribuição estimada por volume neste contexto?

**Definição:** Distribuição estimada por volume

**Classe:** EXPERIMENTAL

**Fórmula:** Ataques da atleta na coorte / soma de ataques das atletas não líbero na formação modal reconciliada de P

**Numerador:** Ataques da atleta na coorte

**Denominador:** soma de ataques das atletas não líbero na formação modal reconciliada de P

**Unidade:** peso 0–1; interface em %

**Fontes:** Volume de ataque do Match Report na coorte, Formação reconciliada da súmula e líbero

**Granularidade:** equipe/rotação/coorte

**Dados mínimos:** Seis nomes reconciliados, rotação conhecida e volume positivo entre atacantes da formação modal.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** lineup volume prior

**Versão do modelo:** lineup-volume-prior-v1

**Validação:** Normalização e escopo por fixtures; modelo descritivo não validado preditivamente. Não usar como feature temporal.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Sem sequência recepção→levantamento→ataque. Passe filtra eficiência, mas NÃO altera pesos de distribuição. Amostras de disponibilidade e eficiência podem diferir. Entropia alta não implica qualidade; não há causalidade.

**Exemplo numérico ou caso limite:** Dois atacantes com pesos 0,5: entropia do modelo=1 bit; isso não informa quantos levantamentos receberam.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Entropia do prior de volume — `lineup_volume_entropy`

**Pergunta:** Qual o valor de Entropia do prior de volume neste contexto?

**Definição:** Entropia do prior de volume

**Classe:** EXPERIMENTAL

**Fórmula:** −Σ peso_i log₂(peso_i), sobre a distribuição estimada por volume

**Numerador:** −Σ peso_i log₂(peso_i), sobre a distribuição estimada por volume

**Denominador:** Não se aplica

**Unidade:** bits

**Fontes:** Volume de ataque do Match Report na coorte, Formação reconciliada da súmula e líbero

**Granularidade:** equipe/rotação/coorte

**Dados mínimos:** Seis nomes reconciliados, rotação conhecida e volume positivo entre atacantes da formação modal.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** lineup volume prior

**Versão do modelo:** lineup-volume-prior-v1

**Validação:** Normalização e escopo por fixtures; modelo descritivo não validado preditivamente. Não usar como feature temporal.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Sem sequência recepção→levantamento→ataque. Passe filtra eficiência, mas NÃO altera pesos de distribuição. Amostras de disponibilidade e eficiência podem diferir. Entropia alta não implica qualidade; não há causalidade.

**Exemplo numérico ou caso limite:** Dois atacantes com pesos 0,5: entropia do modelo=1 bit; isso não informa quantos levantamentos receberam.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL

## Diversidade do modelo × eficiência — `volume_diversity_efficiency`

**Pergunta:** Qual o valor de Diversidade do modelo × eficiência neste contexto?

**Definição:** Diversidade do modelo × eficiência

**Classe:** EXPERIMENTAL

**Fórmula:** Entropia do prior de volume em P × eficiência agregada da equipe em K1+/K1−/K2

**Numerador:** Entropia do prior de volume em P × eficiência agregada da equipe em K1+

**Denominador:** K1−/K2

**Unidade:** bits × eficiência em %

**Fontes:** Volume de ataque do Match Report na coorte, Formação reconciliada da súmula e líbero

**Granularidade:** equipe/rotação/coorte

**Dados mínimos:** Seis nomes reconciliados, rotação conhecida e volume positivo entre atacantes da formação modal.

**Amostra:** Somente registros cobertos pelas fontes, na mesma competição, categoria, gênero e temporada.

**Amostra pequena:** Exibir n; amostra pequena não sustenta ranking conclusivo.

**Intervalo:** Não aplicável sem hipótese probabilística válida.

**Ajuste de amostra:** Nenhum na medida bruta.

**Modelo:** lineup volume prior

**Versão do modelo:** lineup-volume-prior-v1

**Validação:** Normalização e escopo por fixtures; modelo descritivo não validado preditivamente. Não usar como feature temporal.

**Interpretação:** Comparar somente definições e fontes equivalentes.

**Limitações:** Sem sequência recepção→levantamento→ataque. Passe filtra eficiência, mas NÃO altera pesos de distribuição. Amostras de disponibilidade e eficiência podem diferir. Entropia alta não implica qualidade; não há causalidade.

**Exemplo numérico ou caso limite:** Dois atacantes com pesos 0,5: entropia do modelo=1 bit; isso não informa quantos levantamentos receberam.

**Interface:** Detalhe contextual e Dados → caderno.

**Como não interpretar:** Não demonstra causalidade ou qualidade individual.

**Referência:** Definição operacional do projeto; não reivindica padronização externa.

**Notas da fonte:** Sem eventos individuais, não atribuir ponto a atacante ou levantadora.

**Introduzida em:** atlas-metrics-1.0

**Disponibilidade:** CONDITIONAL
