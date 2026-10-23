# Registro metodológico interno

Versão: scouting-1.0 / logistic-l2-v1. Revisão em 22/10/2026.
Este documento não integra a navegação pública. As fontes abaixo foram consultadas;
não se preservaram as alegações quantitativas nem as citações bibliográficas sem
verificação da interface antiga.

## Fonte primária dos dados

CBV, página do jogo 2590834: https://cbv.com.br/jogo/2590834
Relatório consultado: https://fra1.digitaloceanspaces.com/pls-api/matches/2590834-c29c468eeeaaa1725a85cce989fddafd/2026-10-16-RJ-MG.pdf

O PDF diferencia `Pontos SO`, recepções, `Pontos BP`, saques, erros de ataque e
bloqueados. `Cada ... recepções/serviço` é frequência por ponto, não percentual.
SO e BP são recalculados das contagens, sem tratar esses campos como taxas.
A tabela por rotação contém saldo, sem denominadores separados por fase.
Os kills de fase no parser são reconstruídos por arredondamento de n × percentual.
Não classificar essa reconstrução como contagem diretamente observada.

| Métrica | Fórmula / dados necessários | Classe da taxa | Limitações |
| --- | --- | --- | --- |
| SO | pontos SO / recepções | Derivado | Denominador da fase do relatório; não confundir com FBSO |
| BP | pontos BP / saques | Derivado | Não substituir por aces ou pontos de bloqueio |
| Kill% | pontos de ataque / tentativas | Derivado | Distinta de eficiência |
| Eficiência | (kills − erros − bloqueados) / tentativas | Derivado | Campos de erro e bloqueado separados; não tratar ausentes como zero |
| K1+, K1−, K2 | kills reconstruídos / tentativas; eficiência usa erros e bloqueados | Derivado | Percentual de origem arredondado; sem IC binomial |
| Passe positivo/excelente | soma(n × percentual publicado) / soma(n) | Derivado | Numerador aproximado; sem Wilson ou beta-binomial sobre contagem inventada |
| Erro de saque/recepção/ataque | erros / tentativas da respectiva ação | Derivado | Não equivale a erro por rally; não somar ações com denominadores diferentes |
| Δ | taxa da equipe − razão das somas da coorte | Derivado | Pontos percentuais; apenas mesma competição/categoria/gênero/temporada |
| Percentil | 100 × (equipes abaixo + metade dos empates) / equipes válidas | Derivado | Percentil de taxa bruta, inclusive em ranking ajustado |
| Tendência | razão das somas das últimas 5 partidas válidas | Derivado | Janela menor no início; mesma coorte; datas ausentes ficam fora |

As definições executáveis e versões estão em `cbv/metric_definitions.py`,
materializadas na tabela `metric_definitions` do DuckDB.

## Definições esportivas de apoio

- FIVB, **Technical and Data Report — VNL 2024**, documento consultado em:
  https://www.fivb.com/wp-content/uploads/2025/04/FIVB-Technical-and-Data-Report-07.05.2025.pdf
  Distingue eficiência in/out-of-system e situações crunch. Não se transpõem
  correlações ou rankings VNL para a base CBV. O nome/ano da competição é VNL 2024;
  a data do caminho do arquivo não é o ano da competição.
- Pro Volleyball Federation, **Statistics Explained**:
  https://provolleyball.com/statistics-explained
  A página indexada define eficiência como kills menos erros e bloqueados sobre
  tentativas. Na consulta direta houve redirecionamento indisponível; a fórmula
  implementada é explicitamente a convenção de campos separados do relatório CBV.
  Não se afirma que convenções NCAA com bloqueado incorporado ao erro sejam idênticas.

## Wilson 95%

NIST/SEMATECH e-Handbook, **7.2.4.1. Confidence intervals**:
https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm

Implementação `wilson(k,n)`, z=1,959963984540054. Só k e n de contagem direta,
0 ≤ k ≤ n, n > 0. Eficiência líquida e contagens reconstruídas não recebem
intervalo binomial. Dependência entre rallies e heterogeneidade entre adversários
limitam interpretação inferencial. Não são intervalos para previsão de partidas.

## Ranking beta-binomial empírico

Modelo de desenvolvimento explicitamente documentado, não uma conclusão da
literatura esportiva: prior Beta(α,β) por momentos das taxas das equipes. Média
ponderada por ações; variância entre equipes menos média da variância binomial.
Intensidade α+β limitada a [2, 10000]; mínimo de 3 equipes e média estritamente
entre 0 e 1. Posterior média = (k+α)/(n+α+β).

As escolhas de limites são regularizações de implementação. Com coorte insuficiente,
contagens aproximadas ou eficiência líquida, ajuste fica indisponível. Taxa bruta,
n, IC e classe Modelo permanecem distintos. Para erro, menor taxa é preferível.

## Previsão e validação temporal

Hyndman e Athanasopoulos, **Forecasting: Principles and Practice**, seção
**Time series cross-validation**:
https://otexts.com/fpp3/toolbox.html#time-series-cross-validation

A fonte sustenta a separação temporal, não uma garantia de desempenho no voleibol.
Implementação: regressão logística L2, penalidade 2, escala fixa de diferenças /20
para SO, BP, eficiência e kill de K1+/K1−/K2, mais diferença de vitórias nas últimas
5 partidas. Sem intercepto e sem efeito de mando não validado: previsão simétrica
à troca de equipes. Features são taxas históricas brutas; os rankings beta-binomial
são uma camada separada, não se atribui ajuste Bayesiano ao modelo logístico.

Amostra: partidas VALID, datadas, com resultado não empatado, na mesma coorte.
Cada feature usa apenas dias anteriores. Todos os jogos do dia são previstos antes
de atualizar histórico/treino. Mínimo de 20 exemplos temporais anteriores para fit;
sem dados de ambas equipes ou fases, não há previsão. Treino final usa todo histórico
conhecido da coorte para confronto hipotético; isso não é retrospectivamente aplicado
ao backtest. Não há imputação entre temporadas.

Brier = média((p−y)²); log loss = −média(y log p + (1−y) log(1−p)). ECE usa faixas
do favorito [50,60), [60,70), [70,80), [80,100], ponderadas por n. A curva mostra
probabilidade média versus frequência de vitória do favorito. Acurácia é secundária.
Sem amostra, métricas retornam null, não desempenho fictício. Não há intervalo
preditivo validado, placar projetado ou confiança alta/média/baixa.

## Proveniência

Novas ingestões registram URL da página pública, parser_version e data_version.
A camada repository não conhece instante real da consulta à fonte nem ID/URL exata
do PDF: fetched_at e source_document_id ficam nulos. created_at é inserção no banco,
não comprovação de nova coleta. Não retroatribuir versão de parser a registros legados.

## Eventos: estudo da fonte e requisitos

A página CBV consultada incorpora um widget público ponto-a-ponto:
https://widgets.volleystation.com/play-by-play-old/2590834

O widget é uma aplicação JavaScript. Uma tentativa de consulta direta com o cliente HTTP local retornou 403; não foi contornada a restrição de acesso. A presença do link não comprova disponibilidade
de contatos, avaliações de passe, atleta levantador, tempo de ataque ou rotações.
Não há ingestão validada desse feed neste projeto. `rallies` e `contacts` foram
criadas vazias. Antes de habilitar métricas, verificar contrato, cobertura,
identificadores, ordenação, placar e reconciliação com resultado/súmula.

Planejados, condicionais aos eventos:
- xSO/xBP: recepção/saque vinculado ao resultado e contexto de cada rally;
- FBSO/primeira transição: sequência de contatos e fase;
- Set Assist: denominador completo de levantamentos e ataque seguinte;
- levantadora/entropia/rede: destinos e categorias efetivamente observados;
- Markov: transições empíricas e estados absorventes;
- crunch: placar anterior, set e ações vinculadas. Não inferir do placar final.

A heurística antiga permanece apenas em `/experimental` e CLI, com classe Modelo,
aviso de que não representa frequências reais e sem ICs artificiais. Entropia dos
pesos heurísticos não equivale à diversidade observada da levantadora.
