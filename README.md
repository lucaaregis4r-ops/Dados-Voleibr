# Vôlei BR — Central de scout

[Consultar a publicação](https://lucaaregis4r-ops.github.io/Dados-Voleibr/)

Projeto independente • dados públicos disponibilizados pela CBV.

Pipeline Python de coleta, parser, validação, DuckDB e publicação de scouting.
A interface usa Inter e Roboto Mono, sidebar, filtros e tabelas sem dependência
de bibliotecas gráficas externas. O HTML contém os dados e funciona no GitHub Pages;
as fontes WOFF2 são incorporadas no HTML, com licenças SIL OFL preservadas no código.

## Executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m cbv app
# Alternativa: ./executar.sh
```

## Navegação

- **Visão geral:** três KPIs (SO, BP e eficiência), scatter de equipes, dois rankings
  simples e partidas recentes.
- **Equipes:** seletor, quatro KPIs, perfil por barras, resumo, rotações e tabela
  pesquisável/ordenável de atletas.
- **Confrontos:** comparação geral, ataque por fase, rotações e projeção inicialmente
  recolhida no final da página.
- **Partidas:** Próximas, Encerradas e Súmulas. “Ver” abre a partida com comparação,
  sets, fases, atletas e rotações, sem previsão.
- **Dados:** cobertura, definições, tipos de métrica e atualização. A análise
  experimental de distribuição fica em um detalhe, fora da navegação principal.

A sidebar fixa de 232px vira menu em telas menores. Tabelas têm rolagem interna;
a home mostra apenas três KPIs. Fórmulas, amostras, intervalos, percentis e ajustes
ficam em tooltip ou detalhe. As fontes são incorporadas no HTML para uso offline.

Os recortes continuam separando competição, categoria, gênero e temporada. Somente
partidas VALID entram nos indicadores consolidados. Partidas com ressalvas podem
ser consultadas individualmente e são sinalizadas. Nenhum modelo estatístico,
parser, scraper ou schema foi substituído durante este redesenho.

SO/BP usam contagens, Kill% é distinto de eficiência. Wilson, deltas, percentis,
shrinkage beta-binomial e validação temporal permanecem implementados. A previsão
é o modelo existente, com Brier, log loss e calibração em detalhe. Sem intervalo
preditivo validado ou denominador de rotação, a interface informa a ausência.

A distribuição estimada é experimental: não representa frequência observada de
levantamentos. A literatura permanece apenas na documentação interna.

## Coleta e exportação

```bash
python -m cbv sync --url "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-18-especial"
python -m cbv scrape-game 2590834
python -m cbv rankings --min-attack 15 --min-serve 10
python -m cbv export csv
python -m cbv export json
python -m cbv predict "SADA CRUZEIRO VÔLEI" "ITAMBÉ MINAS"
python -m cbv model-accuracy
python -m cbv retry-failed
```

O workflow `.github/workflows/daily_sync.yml` roda às 03h BRT, executa a coleta
existente e atualiza banco/exportações/páginas. A exportação HTML escreve
`exports/dashboard.html`, `index.html` e `docs/index.html` a partir da mesma fonte.
Caches de dossiês e papéis táticos são invalidados após ingestão bem-sucedida.
A data de geração do HTML é diferente da data de inserção/consulta à fonte.

## Desenvolvimento

```bash
pytest -q
python -c "from cbv.export.html_dashboard import export_dashboard_html; export_dashboard_html()"
# QA opcional das quatro larguras; usa o Chromium de teste do Playwright
pip install playwright
python -m playwright install chromium
python scripts/check_dashboard_ui.py
```

- `cbv/export/templates/scouting.html`: interface compartilhada por local e Pages.
- `cbv/analysis/scouting.py`: taxas, cobertura, Wilson, percentil, shrinkage e tendência (cálculos preservados).
- `cbv/analysis/temporal.py`: treinamento e validação cronológica.
- `cbv/metric_definitions.py`: catálogo versionado, materializado no DuckDB.
- `docs/METRIC_SOURCES.md`: fontes verificadas e limites metodológicos internos.
- `docs/REFORMULATION.md`: escopo implementado e dependências de eventos.

A API `/api/data` agora oferece `cohorts`, com estatísticas e validação por recorte;
consumidores do payload antigo devem migrar para essa estrutura. Campos preditivos
sem evidência retornam null. `/api/setter-distribution` permanece experimental.
