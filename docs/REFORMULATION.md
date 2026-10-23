# Reformulação editorial e estatística

## Entregue

- Cinco destinos com subnavegação por pergunta de scouting.
- Design em papel, Archivo/IBM Plex Mono, linhas estruturais, KPIs contínuos,
  tabelas, dispersão, dot plots, tendência e calibração SVG acessíveis por texto.
- Recorte integral por competição/categoria/gênero/temporada em todas as telas.
- Taxas por contagens válidas, denominadores, cobertura, definições e classes visíveis.
- Kill% separado da eficiência; K1+/K1−/K2 com arredondamento da fonte declarado.
- Wilson 95%, deltas, percentis, beta-binomial empírico onde há contagens diretas,
  ranking alternável e tendência por janela de cinco jogos.
- Modelo logístico regularizado com backtest temporal e registro de cada previsão.
- Remoção de acurácia/Brier fixos, ICs artificiais e preenchimento preditivo 50/50.
- Heurística de levantadora fora da navegação principal, em /experimental local.
- Tabelas de definições, proveniência e schema de rallies/contacts.
- Invalidação de caches após gravação; exportações local/Pages da mesma implementação.
- Documentação metodológica interna sem bibliografia na interface pública.

## Condicional aos dados de eventos

A fase de sequência não pode ser declarada implementada a partir dos relatórios
agregados. A fonte CBV aponta para um widget ponto-a-ponto, mas não foi validado
um contrato de eventos com os campos necessários. Permanecem explicitamente
planejados: SO/BP por rotação, xSO/xBP, FBSO, primeira transição, Set Assist,
distribuição observada da levantadora, entropia de eventos, rede, Markov e crunch.
Ver `METRIC_SOURCES.md` para dados faltantes e critérios de habilitação.

Não há intervalo de probabilidade de vitória validado; a interface informa a ausência.
A proveniência histórica permanece desconhecida onde não foi registrada. Nenhum
horário de coleta ou identificador de PDF foi retroativamente inventado.

## Verificação desta entrega

- 46 testes Python aprovados, incluindo invariância a resultados futuros,
  datas estritamente anteriores, Wilson, campos ausentes e invalidação de cache.
- Chrome sem interface: 1440, 1024, 768 e 390 px, sem overflow da página;
  gráficos/tabelas usam rolagem interna quando necessária.
- Todos os destinos e subdestinos, filtros, modelo ajustado e seleção de equipe
  pelo teclado verificados sem erros JavaScript.
- APIs de dados, previsão, avaliação, calendário modelado e rota experimental
  verificadas localmente. A verificação de UI é reproduzível por
  `python scripts/check_dashboard_ui.py` (dependência opcional: playwright).
