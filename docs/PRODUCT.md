# Produto: Atlas do Vôlei

## Propósito

O Atlas do Vôlei é uma plataforma de inteligência esportiva para treinadores,
analistas de desempenho, comissões técnicas e profissionais do voleibol. Ajuda a
explorar partidas, equipes, atletas, padrões táticos e estimativas estatísticas
a partir dos registros oficiais disponíveis.

## Fluxos de trabalho

- Selecionar competição, categoria, gênero e temporada.
- Explorar equipes, partidas e atletas dentro desse recorte.
- Comparar duas equipes ou atletas.
- Examinar rotações P1–P6, ataque, recepção, distribuição e análises avançadas.
- Consultar método, amostra, origem e limitações de cada indicador.
- Conferir o estado da coleta e a cobertura das fontes.

## Verdade do produto e dados

A edição ativa determina o escopo de agregados e modelos. Elencos e resultados de
temporadas diferentes não são combinados como uma só equipe. A plataforma
preserva as definições publicadas no catálogo de métricas.

Os rótulos Observado, Reconstruído, Derivado, Modelado e Experimental distinguem
a natureza das informações. Pontos reconstruídos de súmulas não são feed
observado de contatos. Relações entre passe, levantadora e atacante só aparecem
como inferência ou cenário quando os dados não identificam a sequência real.
Estimativas experimentais e indicadores de suporte não são apresentados como
probabilidades validadas.

## Contexto técnico observado

- Interface web estática com payload principal compacto e JSON sob demanda.
- Python, FastAPI e DuckDB atendem aplicação local, coleta e exportação.
- O HTML publicado é gerado a partir de `cbv/export/templates/scouting.html`,
  `atlas.css` e `atlas.js`; os arquivos `index.html`, `docs/index.html` e
  `exports/dashboard.html` são saídas publicadas.
- O fluxo automatizado atualiza e publica dados em GitHub Actions.
- A identidade existente usa azul-marinho, vermelho, Inter e Roboto Mono. A
  refatoração deve evoluir essa linguagem e manter a leitura esportiva do Atlas.

## Critérios de experiência

O caminho principal precisa tornar competição e temporada visíveis e permitir
abrir equipes, atletas, partidas e análises táticas sem descobrir controles
escondidos. Em telas pequenas, controles, tabelas, comparações e gráficos devem
continuar utilizáveis com teclado e toque. A interface não altera cálculos,
fontes, coortes ou contratos de publicação.
