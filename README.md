# Vôlei BR — Atlas Tático

[Consultar a publicação](https://lucaaregis4r-ops.github.io/Dados-Voleibr/)

Scouting de voleibol com Python, DuckDB, FastAPI e HTML estático. Quadras, matrizes
de rotação e replay usam fontes reconciliadas; cada medida expõe amostra e origem.

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

- **Visão geral:** mapa SO × BP do Match Report, rankings, cobertura e leituras por regra.
- **Equipes:** quadra compartilhada, ciclo P1→P6→P5→P4→P3→P2, SO/BP por rotação,
  matriz 6×6 com jogos de origem, fases, passagens de saque, formações e on/off.
- **Confrontos:** quadras comparativas, contexto histórico de rotações, fases e
  projeção pré-jogo recolhida ao final.
- **Partidas:** timeline experimental de WP, ponto a ponto reconstruído, navegação
  de rally e atualização de placar, saque, rotações e formação na quadra.
- **Atletas:** tabela pesquisável e ordenável, perfil e amostra.
- **Dados:** fontes, hashes, tentativas, estados de validação, modelos e avaliações.

O HTML incorpora dados, fontes Inter/Roboto Mono e os componentes de visualização;
não depende de scripts, fontes ou endpoints externos para navegar. As licenças SIL
OFL estão preservadas. Layout verificado em 1440, 1024, 768 e 390 px.

## Definições e limites

SO/BP creditados no Match Report não equivalem a todos os pontos de placar. A
sequência completa é reconstruída das passagens de saque da súmula e mantém uma
série separada. Não há autoria de ação ou timestamp inventado. A rotação absoluta
exige marcador independente da levantadora inicial; presença real exige controle
de líbero e substituições reconciliados.

O widget play-by-play retornou HTTP 403. O coletor registra esse estado e preserva
fontes acessíveis; não há cobertura observada desse feed. Um adaptador estrito de
importação está disponível para schema explicitamente confirmado.

WP, WPA, leverage, expected metrics e ajustes novos são experimentais. O baseline
pré-jogo logístico L2 permanece ativo, com validação temporal em blocos de dia e
comparação comum com challenger de intercepto. Modelos mais complexos não são
promovidos automaticamente. Não confundir associação, on/off e efeito causal.

- [Caderno metodológico gerado do registry](docs/CADERNO_METODOLOGICO.md)
- [Limitações, cobertura e operação](docs/LIMITACOES_ATLAS.md)
- [Auditoria das fontes e definições](docs/AUDITORIA_ATLAS.md)

```bash
python -m cbv backfill --competition superliga --season 2025-2026
python -m cbv backfill --cached-only
python -m cbv.metrics.methodology
python scripts/daily_update.py
```

O backfill é resumível, limitado em requisições e idempotente por hash. A rotina
diária às 03:00 BRT constrói banco e artefatos em staging, executa quality gates e
preserva o último resultado válido em caso de falha. CI de código e sincronização
de dados são workflows separados. Raw snapshots ficam fora do Git, com cache e
artefatos temporários no Actions; retenção permanente exige arquivo externo.

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
