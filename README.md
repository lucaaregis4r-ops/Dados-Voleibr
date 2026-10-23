# Vôlei BR — Dados & scouting

[Consultar a publicação](https://lucaaregis4r-ops.github.io/Dados-Voleibr/)

Projeto independente • dados públicos disponibilizados pela CBV.

Pipeline Python de coleta, parser, validação, DuckDB e publicação de scouting.
A interface editorial usa Archivo, base clara, gráficos SVG e tabelas sem dependência
de bibliotecas gráficas externas. O HTML contém os dados e funciona no GitHub Pages;
as fontes são incorporadas no HTML, com licenças SIL OFL preservadas no código.

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

- **Visão geral:** SO/BP, eficiência, recepção, erro de saque, dispersão e ranking.
- **Equipes:** perfil, dot plot, tendência dos últimos cinco jogos, fases, rotações e atletas.
- **Confronto:** comparação observada, rotações e modelo com validação temporal.
- **Partidas:** calendário, resultados e links públicos das súmulas.
- **Dados:** cobertura, qualidade, definições, proveniência e atualização local.

Todos os recortes separam competição, categoria, gênero e temporada. Somente
partidas VALID entram nos indicadores; ressalvas ficam visíveis em Dados/Partidas.
Cada taxa oferece denominador e definição. Percentuais arredondados da fonte
não são convertidos em contagens exatas para inventar intervalos.

SO/BP usam contagens, Kill% é distinto de eficiência, Wilson é aplicado somente
às proporções compatíveis. Rankings oferecem taxa bruta e média posterior
beta-binomial empírica. Previsões usam regressão logística L2 com backtest
walk-forward estrito, Brier, log loss e calibração calculados; não há garantia de
acurácia nem IC preditivo artificial. Com histórico insuficiente, ficam indisponíveis.

A fonte atual não permite SO/BP separados por rotação, xSO/xBP, distribuição real
da levantadora, FBSO, Set Assist ou crunch. O schema de eventos está preparado,
sem preencher dados sintéticos. A heurística de disponibilidade ofensiva fica
em `/experimental` no servidor local, identificada como Modelo.

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
# QA opcional das quatro larguras; requer Google Chrome instalado
pip install playwright
python scripts/check_dashboard_ui.py
```

- `cbv/export/templates/scouting.html`: interface compartilhada por local e Pages.
- `cbv/analysis/scouting.py`: taxas, cobertura, Wilson, percentil, shrinkage e tendência.
- `cbv/analysis/temporal.py`: treinamento e validação cronológica.
- `cbv/metric_definitions.py`: catálogo versionado, materializado no DuckDB.
- `docs/METRIC_SOURCES.md`: fontes verificadas e limites metodológicos internos.
- `docs/REFORMULATION.md`: escopo implementado e dependências de eventos.

A API `/api/data` agora oferece `cohorts`, com estatísticas e validação por recorte;
consumidores do payload antigo devem migrar para essa estrutura. Campos preditivos
sem evidência retornam null. `/api/setter-distribution` permanece experimental.
