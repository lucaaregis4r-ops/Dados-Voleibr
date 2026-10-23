# Central de scout — revisão da interface

## Escopo

A revisão substitui a apresentação editorial por uma aplicação de scouting familiar:
sidebar de 232px, header com filtros e busca, Inter/Roboto Mono, fundo #F7F7F5,
superfícies brancas e azul como cor principal. Os cálculos e o schema do DuckDB
permanecem preservados.

## Seis commits

1. `refactor(ui): simplify app shell and navigation`
2. `refactor(ui): simplify overview dashboard`
3. `refactor(ui): rebuild team scouting page`
4. `refactor(ui): rebuild matchup comparison`
5. `refactor(ui): simplify match and data pages`
6. `chore(ui): remove legacy AI-dashboard styling`

## Telas

- Home: 3 KPIs, scatter SO/BP, top 5 de cada taxa, partidas recentes.
- Equipes: seleção antes do perfil, 4 KPIs, barras de comparação, resumo por regras,
  rotações 3×2 e tabela de atletas com busca e ordenação.
- Confrontos: tabelas de resumo/fases/rotações; “Ver projeção” recolhido no final.
- Partidas: Próximas/Encerradas/Súmulas e página individual sem previsão.
- Dados: cobertura, definição/tipo das métricas, atualização e Experimental recolhido.

## Dados e limites preservados

A exportação acrescenta apenas a exposição de registros existentes para a tela
individual de partida e contagens de jogos/recepções dos atletas. Não há nova
estatística, modelo, coleta, migração de banco ou mudança das fórmulas corrigidas.
Partidas com ressalvas ficam fora dos agregados; sua consulta individual é sinalizada.

SO/BP por rotação continuam ausentes: a fonte contém apenas saldo e não informa os
denominadores separados. Não se inferem taxas nem amostras a partir desse saldo.
Kills por fase e passe positivo mantêm o aviso de arredondamento em detalhe.
Intervalo preditivo permanece explicitamente indisponível.

O resumo usa maior/menor eficiência para fases e maior/menor saldo bruto para
rotações. Empates exibem a primeira posição, sem concluir superioridade. Jogos
na tabela de atletas são partidas com registro do atleta na fonte.

Wilson, shrinkage, percentis, deltas, validação temporal, Brier e calibração
permanecem nos cálculos. Tipos de métrica e explicações ficam nos detalhes e em
Dados. Fontes e auditoria metodológica permanecem em `METRIC_SOURCES.md`.

## Verificação

O script `scripts/check_dashboard_ui.py` verifica as telas em 1440, 1024, 768 e
390px: overflow, busca, ordenação, seleção, filtros, projeção recolhida, teclado e
funcionamento com fontes incorporadas. Capturas ficam em `temp_inspect/ui/`.
A suíte Python existente verifica a preservação das métricas e da validação.

Resultado da verificação desta revisão: 46 testes Python aprovados. Sete telas e
a projeção expandida foram verificadas nas quatro larguras, sem overflow da
página ou erros JavaScript. A verificação inclui busca/ordenação de atletas,
seleção pelo teclado, todos os filtros e uso sem requisições externas.
