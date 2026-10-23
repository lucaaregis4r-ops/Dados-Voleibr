# Auditoria inicial — Atlas Tático

Base de partida: commit `7320f1c`. Em 23/10/2026, os 46 testes existentes passaram.
A aplicação continua Python/FastAPI/DuckDB com exportação HTML autônoma.

## Fontes verificadas

Partida de referência: https://cbv.com.br/jogo/2590834
A página conecta Match Report, Scoresheet e widget pelo mesmo match_id.

- Match Report: PDF já coletado; preserva totais, fases e saldo de rotações.
- Scoresheet: PDF digital acessível, com escalações, ordem de saque, pontuação ao
  fim das passagens de saque, substituições, timeouts e resultado dos sets.
- Ponto a ponto: o widget público retornou HTTP 403/Cloudflare tanto em HTTP
  quanto em navegação normal. Não houve tentativa de contornar o bloqueio.
  Nenhum endpoint estruturado foi confirmado nesta etapa.
- Documento adicional encontrado no HTML público: relatório de controle de líbero.
  Seu PDF registra atleta substituído e pares de placar de entrada/saída. Pode
  completar a presença em quadra quando reconciliado com a súmula.

A súmula usa a área impressa “Set 5” também no terceiro set de partidas em melhor
  de três. A ordem dos painéis ativos deve ser conciliada com o resultado; não
  se pode interpretar a impressão como número lógico do set sem essa validação.

## Regras de preservação

Não alterar retrospectivamente a fonte dos registros legados. Timestamps de cache
não são timestamps de download. Missing não vira zero. A sequência reconstruída
pela súmula não pode ser rotulada como ponto a ponto observado no widget.

O modelo logístico temporal atual será mantido como baseline. Métricas novas
precisam de amostra, rastreabilidade, validação e classificação explícita. Nenhum
modelo novo substitui o baseline automaticamente.

## Riscos e verificações necessárias

- Ler passagens de saque em ordem de linha e coluna, excluindo números da grade
  de pontuação, cabeçalhos e continuação duplicada do tie-break.
- Não identificar levantador pela camisa, volume de ataque ou heurística sem
  declarar inferência. P1–P6 absoluto exige evidência; ciclo relativo é distinto.
- Validar placares, SO/BP, troca de saque, avanço da rotação e presença de atletas.
- Preservar a última base publicada quando qualquer nova fonte falhar.

## Diferença de definição confirmada

Na partida 2590834, o relatório informa para RJ SO=23, BP=18 e 16 erros do
adversário; 23+18+16=57 pontos de placar. Para MG: 19+18+22=59. Portanto as
contagens de SO/BP do relatório não equivalem a todos os pontos de placar ganhos
em recepção/saque. A reconstrução por serviço dá RJ 34/58 e 23/58 e MG 35/58 e
24/58. As séries não podem ser sobrescritas ou misturadas silenciosamente.
O baseline legado permanece reproduzível; o Atlas deve identificar a definição
por fonte e utilizar taxas de todos os pontos apenas quando houver sequência
reconciliada. A diferença de recepções para rallies recebendo inclui saques
errados que não geram uma recepção registrada.

O Match Report também distingue visualmente a levantadora inicial: seu número
na coluna do set tem caixa vazia, enquanto os demais titulares têm fundo cinza.
Essa marcação será testada como fonte independente da posição inicial, sem
inferir a levantadora dos resultados dos rallies.
