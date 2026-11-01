# Previsão de acionamento: diagnóstico e núcleo experimental

## Diagnóstico da cópia do banco em 01/11/2026

Há 601 partidas, 9.041 registros de atletas por partida, 532 registros táticos por equipe-partida, 71.034 rallies reconstruídos e zero contatos. O número de rallies não representa ataques ou levantamentos. `matches` registra data, competição, categoria, gênero, temporada e equipes; `player_match_stats` possui número, nome e totais de ataque por jogo; `team_tactical_stats` agrega ataque após recepção positiva/negativa por equipe-jogo, sem individualizar atacante. `rallies` contém rotação e posição da levantadora quando reconstruídas e validadas; isso não identifica quem levantou ou quem atacou. `contacts` prevê sequência, equipe, atleta, fundamento, avaliação e zonas, mas está vazia e não há contrato comprovado que associe, sem ambiguidades, cada levantamento ao ataque.

A inferência de funções do módulo legado é heurística, não identifica uma levantadora observada. O volume individual não permite deduzir a distribuição condicional por recepção ou rotação. A base atual não autoriza valores de previsão, calibração empírica, intervalos validados ou retrospectiva de acionamentos. Não são preenchidas observações artificiais.

## Núcleo preparado, ainda não integrado ao produto

`cbv.analysis.activation_model` recebe registros sequenciais já auditados, um por distribuição observada, com `team`, `category`, `gender`, `season`, `match_id`, `date`, `target` e, quando conhecidos, `setter`, `rotation`, `pass_quality`. Esses nomes são um contrato interno em memória, não novas colunas no banco. Falta criar e validar um adaptador a partir de uma fonte real de contatos; não basta a tabela existir. O código não decide que um contato de levantamento tenha resultado no ataque seguinte, não reconstrói autoria, nem garante opções presentes em quadra. A integração da interface e do jogo ao vivo depende dessa etapa. Nenhuma migração de schema é proposta sem a análise da fonte de eventos.

A identidade usa a tupla normalizada clube, categoria, gênero e temporada; campos ausentes invalidam a identidade e impedem a previsão. Outros anos, categorias e gêneros nunca entram no histórico direto. A competição ainda não compõe a identidade, pois a mesma equipe pode disputar mais de uma competição na mesma temporada; nomes ambíguos exigem identificador confiável da fonte.

## Modelo provisório

As categorias são atacantes observadas no histórico daquela equipe-temporada, não necessariamente todas as opções disponíveis naquele instante. Sem pelo menos duas opções históricas, retorna indisponível. Não é possível compartilhar nomes entre equipes como se fossem categorias equivalentes: para incorporar um prior geral seriam necessárias funções ofensivas observadas e comparáveis ou outra representação validada. O núcleo atual **não usa a base geral** como prior e **não está calibrado com ela**.

O prior inicial simétrico tem massa total configurável, provisoriamente 1. Essa escolha fraca não é uma estimativa empírica. Em cada nível, as contagens fora do subconjunto mais específico definem uma distribuição mais geral; ela é convertida em massa inicial de força configurável e atualizada com as contagens do nível seguinte. Usam-se subconjuntos disjuntos para evitar contar a mesma observação repetidamente. A ordem é equipe, passe, rotação e levantadora, omitindo condições desconhecidas. A posterior soma o prior e as contagens e a média divide cada parâmetro pela soma. A sequência ao vivo adiciona apenas observações da equipe e do contexto selecionado. Se surgir uma atacante não contemplada no histórico, a previsão fica indisponível até existir um contrato confiável de opções possíveis, evitando omiti-la silenciosamente.

A entropia normalizada resume concentração entre as opções conhecidas; não é certeza sobre a bola seguinte. O desvio-padrão marginal vem da Dirichlet: `sqrt(p * (1-p) / (sum(alpha)+1))`. Não equivale a um intervalo de credibilidade validado nem inclui incerteza de estimação da força do prior ou da disponibilidade; nenhuma classificação de confiança é atribuída.

## Validação e calibração

`evaluate` ordena por data e treina apenas em datas anteriores, atualizando com jogadas anteriores do mesmo jogo conforme a ordem de entrada; partidas do mesmo dia não alimentam umas às outras. Informar registros em ordem cronológica dentro de cada jogo. Relata log loss, Brier multiclasse, top-1/top-2 e tabelas de calibração (previsão média e frequência para cada faixa), além da quantidade de observações não avaliadas, inclusive atletas novas. A exclusão afeta a representatividade: deve ser divulgada e resolvida com escalações auditadas.

`calibrate_strength` compara uma grade de forças usando log loss cronológico; requer dados reais. O resultado da seleção não é avaliação independente: separe um período posterior para testar a força escolhida. Uma avaliação final deve também comparar baselines, medir cobertura, agrupar incerteza por jogo e verificar deriva e calibração por gênero, categoria e temporada. Com a base atual ambas as rotinas retornam ausência de amostra, não um desempenho fictício.
