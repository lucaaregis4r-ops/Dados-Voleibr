# Limitações e operação do Atlas

- O widget play-by-play foi consultado por HTTP e navegador e retornou 403. Não
  houve contorno do bloqueio. Não existe cobertura observada do feed na coleta
  histórica atual. O adaptador `cbv-normalized-pbp-v1` é uma fronteira de importação
  explícita, não uma alegação de que o provedor publica esse formato.
- As sequências disponíveis são reconstruções das passagens de saque da súmula.
  Elas identificam pontos de placar, não contato, autoria, duração ou timestamp.
  Pontos administrativos podem estar incluídos. Sanções não foram extraídas.
- PDFs com layout não reconhecido, equipes ambíguas ou grade incompleta falham
  fechados. Uma tentativa ruim não apaga a última reconstrução válida.
- O marcador gráfico de levantadora inicial no Match Report ancora P1–P6.
  Ausência ou divergência deixa rotação absoluta NULL. Não há ajuste de posição
  para forçar concordância com os saldos ou resultados da partida.
- Formação registrada não equivale a seis atletas realmente em quadra. Somente
  controle de líbero e substituições reconciliados habilitam on/off. O ajuste
  contextual L2 permanece experimental: controla adversário, rotação, saque,
  placar/set e companheiras, e só mostra coeficiente com ganho temporal na mesma
  amostra (Brier/log loss menores, ECE não maior, cinco jogos avaliados e pelo
  menos 20 pontos com/sem). Não há interpretação causal de diferenças brutas
  ou ajustadas.
- SO/BP creditados no Match Report excluem pontos por erro adversário. A sequência
  completa usa outros denominadores. As duas séries permanecem separadas.
- WP, WPA, leverage, xSO/xBP/xPoints e xAttack iniciais são experimentais. O
  comparativo de probabilidades por ponto não valida automaticamente WP por jogo.
  Sem histórico anterior não há previsão; mesmo dia nunca alimenta mesmo dia.
- O modelo de estado considera placar, sets e saque. Ainda não usa efeito de
  rotação, escalação ou adversário validado. Assume CBS melhor de três e Superliga
  melhor de cinco; extensões de competição precisam validar o regulamento.
- As futuras primeiras equipes sacadoras dos sets são marginalizadas 50/50. Isso
  é hipótese explícita, não observação. Crunch é convenção de placar; leverage é
  sensibilidade probabilística. Faixas de pressão ainda não foram validadas.
- O baseline pré-jogo logístico L2 permanece ativo. Nenhum novo modelo o substitui
  por possuir mais features. Ratings por adversário, efeito contextual ajustado e
  previsão v2 só devem ser publicados após comparação temporal na mesma amostra.
- Distribuição de levantadora e Shannon continuam experimentais no módulo legado.
  O Atlas também oferece um prior de volume ofensivo sobre formação modal
  observada, sem multiplicadores de passe: a fase filtra a eficiência comparada,
  mas não altera os pesos quando os contatos não existem. Entropia é do modelo.
  Não há sequência observada recepção→levantamento→ataque nas fontes coletadas.
  Diversidade não significa eficiência e associação não implica causalidade.

## Reprocessamento

```bash
python -m cbv backfill --competition superliga --season 2025-2026
python -m cbv backfill --cached-only
python -m cbv.metrics.methodology
python scripts/daily_update.py
```

O backfill usa manifests/hashes, limite de requisições compartilhado, cache,
retentativas e staging. Uma única instância deve atualizar o banco. Feche um
servidor local que mantenha conexão de escrita antes da promoção; DuckDB rejeita
concorrência incompatível. A rotina diária usa trava de publicação e staging.
A cópia `data/cbv.last-valid.duckdb` permite recuperação local e não entra no Git.

Snapshots permanecem em `data/raw/matches/`, ignorados no Git por volume. O
workflow preserva cache e um artefato de fontes/logs por 30 dias. Isso exige
arquivamento externo para retenção permanente; não confundir cache com backup
indefinido. Os manifests no banco e na interface expõem URLs e hashes para auditoria.

Cron preservado em 06:00 UTC / 03:00 BRT. CI testa código em push/PR; rotina diária
só versiona banco e artefatos gerados, sem `git add cbv/`.

Temporada, categoria e gênero legados permanecem identificadores da coorte. Datas
fora de uma janela esportiva esperada não são reclassificadas automaticamente
como outra temporada sem identidade oficial da competição. O HTML original
preserva essa evidência para auditoria; não inferir regulamento pelo placar.

## Correção de edições — 23/10/2026

A auditoria da página oficial “Temporada 26/27”, cruzada por identificador de
partida, corrigiu seis jogos femininos (2584995 a 2585000) e o calendário que
estavam rotulados como 2025–2026. Os jogos pertencem a 2026–2027. O erro era causado
pela inferência fixa no repositório e pelo rótulo fixo do calendário; a ingestão
agora recebe a edição da fonte. A rotina diária acompanha as páginas atuais dos
dois gêneros e confirma o título de temporada antes de atribuir seus jogos.

Os modelos e agregados das edições afetadas foram recalculados. Treinos anteriores
sobre o recorte incorreto ficam em `superseded_model_runs`, com motivo explícito;
não são os treinos ativos. `season_assignments` registra edição anterior, edição
corrigida, URL e hash da evidência. A página oficial e seu hash ficam em
`competition_editions` e nos exports de auditoria. Não houve alteração dos pontos
ou resultados originais. O dossiê legado deixou de combinar temporadas ou trocar
silenciosamente a edição solicitada por outra com mais dados.

Fontes: [Superliga feminina](https://cbv.com.br/volei-de-quadra/superliga-a-feminina)
e [Superliga masculina](https://cbv.com.br/volei-de-quadra/superliga-a-masculina).

Os rankings e resumos táticos legados em CSV/JSON também são agrupados por
competição, categoria, gênero e temporada, com essas colunas explícitas. O total
da equipe usado no cálculo de participação ofensiva pertence à mesma coorte.
