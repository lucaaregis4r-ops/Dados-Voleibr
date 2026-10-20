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

## Comandos do Sistema

```bash
# 1. Ajuda geral
python -m cbv --help

# 2. Coleta e processamento de partida individual
python -m cbv scrape-game 2590834

# 3. Raspagem de campeonato completo (descoberta automática de jogos públicos)
python -m cbv scrape-competition --competition cbs --category sub18 --gender masculino --division especial --season 2026

# 4. Rankings e estatísticas consolidadas por fundamento
python -m cbv rankings
python -m cbv rankings --min-attack 15 --min-serve 10

# 5. Exportação de dados e rankings
python -m cbv export csv
python -m cbv export json

# 6. Reprocessar partidas com erro registradas no data/failed_games.json
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

## Estrutura de Diretórios
- `cbv/`: Código-fonte da aplicação (scraper, parser, models, database, analysis, validation, export).
- `data/raw/`: Arquivos brutos baixados (páginas HTML e relatórios PDF).
- `data/processed/`: Dados extraídos normalizados em JSON.
- `data/cbv.duckdb`: Banco de dados relacional colunar DuckDB.
- `exports/`: Arquivos gerados para consumo analítico externo (CSV e JSON).
- `logs/`: Arquivos de log de auditoria (`cbv.log`).
- `tests/`: Bateria de testes unitários e de integração com fixtures reais.


