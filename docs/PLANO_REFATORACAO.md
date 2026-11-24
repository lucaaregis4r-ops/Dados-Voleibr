# Plano de refatoração — Atlas do Vôlei

## Objetivo

Dar acesso direto às análises do Atlas, organizar a comparação por edição e
melhorar a experiência em telas pequenas, preservando os dados, fórmulas,
modelos, coortes e caminhos publicados. Implementação sobre o GitHub `main`
(`8f75425a92fa6c4d11bb41d0f79aa1eca4292b34`), na branch isolada
`codex/atlas-refactor`.

## Etapas verificáveis

- [x] **1. Auditar o estado atual.** Mapear arquitetura, navegação, dados,
  pipeline, métodos, modelos, exports e testes; registrar em
  `INVENTARIO_FUNCIONALIDADES.md`.
- [x] **2. Registrar o contexto do produto.** Documentar usuários, tarefas,
  fontes, limites estatísticos e linguagem visual existente em `PRODUCT.md`.
- [x] **3. Estabelecer baseline executável.** Registrar os 115 testes da
  primeira execução; instalar Playwright e Chromium no ambiente local; executar
  a suíte completa após preparar as dependências.
- [x] **4. Corrigir instalação do projeto.** Configurar descoberta explícita de
  pacotes `cbv*` no `pyproject.toml` e validar instalação editável.
- [x] **5. Preservar e reutilizar a renderização existente.** A nova rota usa
  `renderTeamSubSection` e as definições atuais do registry; não remove
  caminhos ou renderizadores sem evidência de que sejam descartáveis.
- [x] **6. Abrir caminho direto para análises.** Adicionar “Análises” ao menu
  principal e móvel; disponibilizar equipe, rotações, ataque, recepção, atletas,
  avançado e comparação entre edições.
- [x] **7. Refinar navegação e responsividade.** Tornar a busca utilizável em
  celular, incluir ícones SVG, organizar as abas em duas linhas e validar a
  interface em larguras de 320 a 1440 px.
- [x] **8. Gerar as saídas publicáveis.** Regenerar `index.html`,
  `docs/index.html` e `exports/dashboard.html` a partir do bootstrap exportado
  atual; confirmar conteúdo e hashes idênticos.
- [x] **9. Validar regressões.** Executar suíte integral, verificações de UI,
  navegação JavaScript, lint de Python, checagem de sintaxe, smoke em navegador
  e revisão visual das telas em celular e desktop.
- [x] **10. Registrar conclusão e retomada.** Atualizar inventário e plano com
  entregas, resultados finais e o limite da ferramenta de render do Hallmark.

## Resultado e validação

- `pytest -q`: **126 passaram**, uma advertência de descontinuação da API do
  PyMuPDF, em 246 s. A cópia versionada de `data/cbv.duckdb` foi restaurada
  depois da execução.
- Testes focados finais de UI: **11 passaram**; navegação JavaScript: **9
  passaram**. `node --check`, Ruff e `git diff --check` passaram.
- `python scripts/check_atlas_ui.py` passou em 1440, 1024, 768 e 390 px.
- Chromium via Playwright passou em 320, 390, 768, 1024, 1440 e 1920 px, sem
  overflow, erro de navegador ou falha na comparação. O destino ativo móvel tem
  contraste de 13,92:1; a comparação apresenta seis métricas.
- Capturas finais revisadas em `/tmp/atlas-final-mobile-viewport.png` e
  `/tmp/atlas-final-comparison-viewport.png`.
- `sloplint index.html --scope app`: **0 FAIL, 0 REFLEX e 0 WARN**.
- Os três HTMLs estáticos foram regenerados com o payload existente: 640
  partidas, 9 coortes e 74 métricas. Os três têm SHA-256 idêntico
  (`88bb6f86eb529a0c360ab8f68f1d808e642fd7f6bb38067e13825628c1dd094e`).
- A descoberta de pacotes setuptools foi restringida a `cbv*`; a instalação
  editável passou. Nenhuma fórmula, coorte ou dado de publicação foi recalculado
  para produzir os HTMLs.
- A sincronização automática agora também exige push em `main`, para não alterar
  dados enquanto a refatoração estiver em uma branch de PR.

## Limite da ferramenta de render

O comando Hallmark com `--render` informa que `puppeteer-core` não está
disponível e o runtime não alcança o npm registry. Por isso, os checks próprios
de render do Hallmark não rodaram. A validação visual equivalente foi feita
manualmente com Playwright e Chromium nas seis larguras acima; as capturas foram
inspecionadas.

## Ponto de retomada

A rota “Análises”, a comparação por edição, a migração de tokens e estados
visuais, o empacotamento, os exports e as validações estão concluídos. Não há
pendências de código identificadas. Para executar também o render automatizado
do Hallmark, disponibilize `puppeteer-core` no ambiente e repita o comando; a
revisão visual em Chromium já foi feita manualmente.
