# CBV Volley Data

Sistema em Python para coleta automatizada, estruturação, validação e análise de dados públicos dos relatórios de jogos da Confederação Brasileira de Voleibol (CBV).

## Ordem de Prioridade
`CORREÇÃO DOS DADOS > VALIDAÇÃO > ROBUSTEZ > MANUTENIBILIDADE > VELOCIDADE > INTERFACE`

## Instalação e Ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Execução Rápida com 1 Clique (Aplicação da CT)

Você pode simplesmente **clicar duas vezes no arquivo `executar.sh`** na pasta do projeto para iniciar a aplicação web completa diretamente no seu navegador padrão (ou clicar no atalho `Abrir_Menu_CBV.desktop`).

Pelo terminal:
```bash
./executar.sh
# ou
python -m cbv app
```

A aplicação web conta com:
- **Design Moderno (21st.dev):** HUD profissional em dark mode, Bento grid, glassmorphism, tipografia técnica e ícones vetoriais SVG (sem emojis ou visual genérico de IA).
- **Quadra Tática Interativa:** Visualização em tempo real das 6 zonas com mapeamento espacial de atacantes, rede e fundo.
- **Sincronização por URL:** Cole o link do CBS Feminino da CBV e o sistema baixa novos jogos, atualiza o DuckDB e recalcula tudo automaticamente.
- **Boletim Diário WhatsApp:** Pré-visualize e copie com 1 clique a mensagem pronta para a Comissão Técnica com classificação, destaques e alertas.
- **Simulador Preditivo:** Previsões probabilísticas com intervalos de confiança de 90%, margens de erro e Brier score calibrado.
- **Acionamento da Levantadora (P1-P6):** Previsão condicional do destino dos levantamentos com base na qualidade do primeiro passe (A, C ou contra-ataque K2) e índice de previsibilidade (entropia de Shannon).

## Comandos do Sistema

```bash
# 1. Aplicação Web Unificada (FastAPI + Dashboard Tático)
python -m cbv app

# 2. Menu Interativo via Terminal (Modo alternativo CLI)
python -m cbv menu

# 3. Raspagem e Sincronização Diária via URL da Competição (Rotina da CT)
python -m cbv sync --url "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-18-especial"
python -m cbv scrape-url "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-18-especial"

# 3. Boletim da Comissão Técnica (CT) gerado automaticamente no sync
# Disponível em:
# - exports/boletim_ct_diario.txt (formatado para WhatsApp/Telegram)
# - exports/boletim_ct_diario.md (relatório em Markdown)

# 4. Previsão de Vitórias com Nível de Precisão e Calibração
python -m cbv predict "SÃO PAULO" "MINAS GERAIS"
python -m cbv model-accuracy

# 5. Previsão de Acionamento de Atletas por Qualidade de Passe e Rotação P1-P6
python -m cbv setter-distribution "SÃO PAULO"
python -m cbv setter-distribution "SÃO PAULO" --rotation P1 --pass negative
python -m cbv setter-distribution "SÃO PAULO" --rotation P5 --pass positive

# 6. Coleta de partida individual
python -m cbv scrape-game 2590834

# 7. Rankings consolidados e exportação
python -m cbv rankings --min-attack 15 --min-serve 10
python -m cbv export csv
python -m cbv export json

# 8. Reprocessar partidas com erro
python -m cbv retry-failed
```

## Estrutura do Match Report (VolleyStation / CBV)

A análise estrutural do relatório (Fase 2) utilizando PyMuPDF e pdfplumber revelou os seguintes padrões:
- **Páginas:** O relatório da partida possui 1 única página.
- **Identificação das Equipes:** 
  - Placar geral no topo: `[Equipe Casa] [Sets Casa] [Sets Fora] [Equipe Fora]` (ex: `RIO DE JANEIRO 1 2 MINAS GERAIS`).
  - Normalização automática de codificação de caracteres dos estados (ex: `MARANH?O` -> `MARANHÃO`, `S?O PAULO` -> `SÃO PAULO`).
  - Cada equipe possui sua própria seção de estatísticas precedida pelo nome em caixa alta.
- **Jogadores:**
  - Identificados por número de 2 dígitos (ex: `01`, `03`), indicador opcional de líbero `L`, e nome.
  - Normalização de tokens compactados sem espaço na recepção (ex: `100%(100%)`).
  - Jogadores que não atuaram possuem marcadores `.` em todas as colunas de sets e estatísticas.
- **Estrutura das Colunas:**
  - `Set (1 a 5)`: Posição de rotação inicial ou substituição no set.
  - `Votar`: Nota de avaliação do jogador (ex: `5.8`, `6.4`, ou `.` quando ausente).
  - `Pontos`: `Tot` (Total), `BP` (Break Points), `W-L` (Vencidos - Perdidos).
  - `Saque`: `Tot` (Total), `Err` (Erros), `Pts` (Aces).
  - `Recepção`: `Tot` (Total), `Err` (Erros), `Pos%` (% Positiva), `Exc%` (% Excelente entre parênteses).
  - `Ataque`: `Tot` (Tentativas), `Err` (Erros), `Blo` (Bloqueados), `Pts` (Pontos convertidos), `Pts%` (% de aproveitamento).
  - `BK`: `Pts` (Pontos de bloqueio).
- **Totais da Equipe:**
  - Linha `Total de jogadores` (frequentemente `otal de jogadores` no OCR de texto devido à capitular estilizada).
  - Linhas de resumo por set com pontos vencidos (`Ser`, `Atk`, `Blo`, `Op.Er`).
- **Validação Cruzada:**
  - Confirmação matemática exata de todos os pontos da partida: `Ataque + Bloqueio + Aces + Erros do Adversário = Pontos Totais`.

## Automação Diária e Integração GitHub (03:00 BRT)

O projeto conta com esteira CI/CD via GitHub Actions e rotina local automatizada:
- **Agendamento:** Executa diariamente às 03:00 BRT (`06:00 UTC`), buscando novos jogos e súmulas na CBV, extraindo o calendário de próximas partidas, atualizando o DuckDB, recompilando os modelos Monte Carlo e exportando o dashboard e datasets.
- **Git Auto-Push:** As atualizações são comitadas e enviadas automaticamente para o repositório oficial: [https://github.com/lucaaregis4r-ops/Dados-Voleibr](https://github.com/lucaaregis4r-ops/Dados-Voleibr).
- **Agendador Local (Opcional):** `./scripts/setup_cron.sh` para ativar o agendamento crontab nativo no Linux.

## Módulos do Dashboard Tático

O dashboard editorial (`exports/dashboard.html`) conta com 10 módulos técnicos:
1. **01 CONFRONTOS:** Simulador estocástico Monte Carlo (2.500 iterações por confronto), probabilidades calibradas, distribuição de placar e linhas de mercado.
2. **02 CALENDÁRIO:** Próximas 132 partidas da Superliga Masculina e Feminina com probabilidades calculadas e botão de simulação direta em 1-clique.
3. **03 LEVANTADORA:** Prancheta espacial 2D das 6 zonas, acionamento por qualidade do passe (A, C, K2), Entropia de Shannon $H(X)$, entropia normalizada $H_{norm}$ e diretrizes da CT.
4. **04 MATRIZ TÁTICA:** Dispersão bidimensional em 4 quadrantes (Elite, Defensivas, Viradoras, Vulneráveis) baseada em Side-Out % × Break Point %.
5. **05 ATAQUE & FASES:** Aproveitamento em K1+ (passe na mão), K1- (passe quebrado) e K2 (contra-ataque/transição).
6. **06 RODÍZIOS:** Saldo e diferencial líquido de pontos rotação por rotação (P1 a P6).
7. **07 DOSSIÊ & SCOUTING:** Relatório individual por equipe com principais pontuadores, alvos vulneráveis de saque e taxa de erro.
8. **08 H2H DIRETO:** Comparativo técnico e tático direto entre duas equipes selecionadas.
9. **09 SÚMULAS AUDITADAS:** Histórico de 583 partidas oficiais validadas pelo DuckDB.
10. **10 REFERÊNCIAS CIENTÍFICAS:** Fundamentação acadêmica baseada nas publicações internacionais mais citadas (Palao et al., 2004; Marcelino et al., 2010; Paulo et al., 2016; Castro & Mesquita, 2011; Afonso et al., 2012; Moras et al., 2008).

## Estrutura de Diretórios
- `cbv/`: Código-fonte da aplicação (scraper, parser, models, database, analysis, validation, export).
- `.github/workflows/daily_sync.yml`: Workflow diário do GitHub Actions (03:00 BRT).
- `scripts/`: Scripts utilitários de atualização diária (`daily_update.py`) e crontab (`setup_cron.sh`).
- `data/cbv.duckdb`: Banco de dados relacional colunar DuckDB auditado (583 jogos, 132 fixtures, 40 clubes).
- `exports/`: Arquivos gerados (dashboard HTML autônomo, CSV, JSON e boletim WhatsApp).
- `logs/`: Arquivos de log de auditoria (`cbv.log`).
- `tests/`: Bateria de testes unitários e de integração (39 testes aprovados).



