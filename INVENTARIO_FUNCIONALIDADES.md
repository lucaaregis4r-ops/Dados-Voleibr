# Inventário funcional — Atlas do Vôlei

## Base auditada

- Repositório e branch: `main`, atualizado no worktree para `8f75425`
  (14/11/2026; atualização automática CBV).
- Aplicação: Python 3.11+, FastAPI, DuckDB e interface HTML/CSS/JavaScript
  estática. O exportador monta o site a partir de `cbv/export/templates/`.
- Snapshot do diretório `exports/`: 640 partidas; 1.280 registros de equipe;
  9.964 registros de atletas por partida; 4 edições cadastradas; 938 registros
  de execução de modelos. São contagens do snapshot de publicação e podem mudar
  na próxima sincronização.
- Coortes presentes em `matches.json`: Superliga A feminina e masculina em
  2024–2025, 2025–2026 e 2026–2027; CBI sub-16 feminino e masculino em 2026;
  CBS sub-18 masculino em 2026. O escopo de gênero/categoria/temporada é
  preservado por coorte.

## Arquitetura e fluxo de dados

1. `cbv/scraper/` consulta páginas oficiais, coleta relatórios e artefatos
   associados, mantém cache bruto e sincroniza competições.
2. `cbv/parser/` extrai metadados, Match Report, estatísticas de atletas e
   equipe, súmulas, ponto a ponto estruturado quando disponível e dados táticos.
3. `cbv/validation/` valida registros. `cbv/reconstruction/` reconstrói rallies,
   escalações e presença a partir das fontes aprovadas, mantendo tentativas,
   avisos e proveniência.
4. `cbv/database/schema.sql` e `cbv/database/repository.py` mantêm o DuckDB,
   histórico, fontes, relatórios, definições de métricas e execuções de modelos.
5. `cbv/analysis/` agrega indicadores, tática, séries temporais, rankings e
   modelos. `cbv/metrics/registry.py` concentra definição, unidade, fórmula,
   fontes, classificação e limitações.
6. `cbv/export/html_dashboard.py` gera payload compacto e fatias JSON. O HTML
   carrega atletas, rallies, dados táticos e partidas detalhadas sob demanda.
7. `cbv/pipeline.py` promove atualizações em staging; scripts de sincronização
   e `.github/workflows/daily_sync.yml` publicam o site e os dados. CI em
   `.github/workflows/ci.yml` executa verificações de código, método e UI.

## Interface e navegação existente

- **Início:** resumo da edição, jogos recentes e agendados, atletas em destaque,
  equipes, comparadores rápidos e atalhos de exploração.
- **Jogos:** filtros de agenda, partidas encerradas e súmulas; página de partida
  com placar por sets, comparação das equipes, fases de ataque, atletas e saldo
  por rotação, quando disponível.
- **Times:** seletor dentro da coorte; Visão geral, Rotações, Ataque, Passe,
  Atletas e Avançado.
- **Atletas:** busca e perfil por equipe/coorte, filtros e métricas; elenco
  completo pode ser carregado sob demanda.
- **Confrontos:** comparação acionada pelo dock, limitado a duas equipes ou dois
  atletas conforme o tipo de item.
- **Filtros de contexto:** chips de Superliga, CBS e CBI por gênero; seletor
  completo para categoria, gênero e temporada.
- **Busca global:** atletas, equipes e partidas no recorte selecionado.
- **Estado das fontes:** selo no cabeçalho abre a cobertura e a saúde da coleta.
- **Legenda metodológica:** classificações e detalhes de métricas são apresentados
  nos detalhes de indicadores; o caderno metodológico, limitações e registro de
  fontes ficam em documentação versionada.

### Navegação inicial e alteração

No snapshot inicial, a navegação principal tinha Início, Jogos, Times e Atletas.
Rotações, Ataque, Passe e Avançado ficavam dentro do perfil da equipe. A nova
rota “Análises” reaproveita esses renderizadores e adiciona um comparador de
edições. O cabeçalho mobile recebeu uma busca em largura integral; os caminhos
anteriores continuam disponíveis. O HTML gerado ainda contém scripts legados
do template, preservados para não romper consumidores sem um inventário de uso.

## Estatísticas, visualizações e métodos a preservar

- Indicadores do Match Report: Side-Out, Break Point, ataque/Kill%, eficiência,
  erros, bloqueios, aces e métricas por fase de recepção/ataque, com denominador,
  amostra e classificação segundo o registry.
- Rankings, indicadores de campanha, perfil ofensivo, resumo tático e tendência
  por equipe; comparações de campanha e confronto.
- Rotações P1–P6, quadra esquemática e posição da levantadora quando sustentadas
  pelos dados. Saldo de rotação não fornece por si só denominadores de SO/BP.
- Distribuições de ataque por fase, gráficos de volume/eficiência, recepção e
  participação das atletas. A atribuição individual não é inventada quando o
  Match Report só contém agregados.
- Modelos existentes em `cbv/analysis/`: previsões logísticas e avaliação
  temporal, ratings de adversárias, efeitos contextuais, ataque esperado,
  distribuição de levantadora, distribuição presumida, alocação de exposição,
  ativação presumida e análises de rallies. Cada saída mantém seu status
  Observado/Reconstruído/Derivado/Modelado/Experimental e limitações.
- Suavização, hierarquia, calibração, intervalos, avaliação walk-forward e
  diagnósticos são métodos existentes; nenhum deve ser recalibrado ou
  reclassificado como efeito de design.
- Tabelas, matriz/quadra, gráficos de dispersão, mapas de participação presumida,
  cenários e estimativas devem manter amostra, recorte, legenda e consulta aos
  valores sempre que a tela atual os oferece.

## Estado final da validação

- Baseline inicial: 115 passaram; 9 testes de navegador não iniciaram porque
  Playwright ainda não estava instalado. Playwright e Chromium foram preparados
  localmente; a suíte final executou todos os casos.
- `pytest -q`: 126 passaram; uma advertência de descontinuação da API do PyMuPDF.
  Testes finais focados de UI: 11 passaram; navegação JavaScript: 9 passaram.
- `python scripts/check_atlas_ui.py` passou em 1440, 1024, 768 e 390 px.
  Playwright no Chromium passou em 320, 390, 768, 1024, 1440 e 1920 px, sem
  overflow ou erro de página. Contraste medido do item ativo móvel: 13,92:1.
- A comparação entre temporadas mostrou seis indicadores com amostras e
  denominadores; nenhum valor ausente foi inventado.
- `node --check`, Ruff e `git diff --check` passaram. Hallmark estático:
  0 FAIL, 0 REFLEX e 0 WARN.
- Capturas finais revisadas: `/tmp/atlas-final-mobile-viewport.png` e
  `/tmp/atlas-final-comparison-viewport.png`. Capturas de referência:
  `/tmp/atlas-current-before-1440.png` e `/tmp/atlas-current-before-390.png`.
- Os exports usam o bootstrap real: 640 partidas, 9 coortes e 74 métricas.
  `index.html`, `docs/index.html` e `exports/dashboard.html` têm SHA-256 idêntico
  (`88bb6f86eb529a0c360ab8f68f1d808e642fd7f6bb38067e13825628c1dd094e`).
- A configuração setuptools inclui somente `cbv*`; a instalação editável passou.
  O teste modificou temporariamente o DuckDB e o banco foi restaurado ao snapshot
  versionado.
- A sincronização automática do GitHub Actions agora só inicia em push para
  `main`; branches de trabalho não atualizam os dados publicados.
- O `sloplint --render` não encontrou `puppeteer-core` e não conseguiu baixar o
  pacote porque o npm registry está inacessível. A validação visual foi feita
  manualmente com Playwright/Chromium nas seis larguras listadas.

## Como verificar alterações futuras

- Executar `node --test tests/test_match_navigation.cjs tests/test_mobile_navigation.cjs`.
- Executar `pytest -q` com dependências de desenvolvimento e Chromium instalados.
- Executar `python scripts/check_atlas_ui.py`: quatro larguras (1440, 1024,
  768 e 390px), overflow, navegação, jogos e rotação P1/P4.
- Executar `ruff check cbv scripts --select E9,F63,F7,F82` e
  `node --check` para o JavaScript do Atlas.
- Comparar contagens antes/depois dos exports e os identificadores e definições
  das métricas. Testes de método e de reconstrução permanecem intactos.
- Abrir as saídas estáticas em navegador e conferir busca, filtros, análise,
  equipe, atletas, partidas, comparação, estados vazios e console.
- Confirmar que os dados sob demanda continuam locais, que a saúde da coleta
  abre, e que geração/publicação preservam os contratos atuais.

## Contrato de preservação

Nenhuma fórmula, denominador, coorte, rota de coleta, schema, modelo, fonte,
classificação epistemológica, registro histórico ou arquivo publicado será
removido. Mudanças de tela devem reutilizar renderizadores e dados existentes.
