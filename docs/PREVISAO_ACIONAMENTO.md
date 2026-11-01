# Distribuição presumida experimental

## Primeira versão com a base agregada

Na aba Ataque de cada equipe, a estimativa usa os ataques registrados por atleta na combinação exata de competição, categoria, gênero e temporada. Os dados de equipes ou naipes diferentes nunca são somados. Só são elegíveis atacantes com ao menos um ataque observado; as opções possíveis e a disponibilidade em quadra não são conhecidas. Sem pelo menos duas atacantes, não é apresentada previsão.

Para k atacantes e n_i ataques, o prior simétrico tem massa total s e a estimativa é `(n_i+s/k)/(N+s)`. A força s é selecionada numa grade por log loss em partidas posteriores, para equipes do mesmo recorte de competição, categoria, gênero e temporada, usando apenas partidas de datas anteriores. Não se somam contagens de atletas entre equipes: outras equipes contribuem somente à escolha da força. Atacantes não vistas no histórico não são previstas e são contadas separadamente na avaliação. Selecionar a força nessa amostra não equivale a avaliá-la em um conjunto independente.

Com menos de 100 ataques avaliáveis ou três partidas avaliáveis, o valor fraco provisório s=1 é usado e a interface informa que não foi calibrado. A entropia usa apenas atletas observadas, portanto não representa todas as opções em quadra. A análise não usa multiplicadores de passe nem afirma estimar passe, rotação ou levantadora. A incerteza sobre composição da equipe, passagem de tempo, disponibilidade e qualidade da fonte não está incluída em um intervalo de credibilidade; por isso nenhum intervalo validado é apresentado.

Os dados agregados calibram a distribuição geral de volume ofensivo, não a distribuição condicional por passe/rotação. A observação de contatos permanece necessária para atualizar as previsões por situação e validar seus efeitos.

# Previsão de acionamento: diagnóstico e núcleo experimental

## Diagnóstico da cópia do banco em 01/11/2026

Há 601 partidas, 9.041 registros de atletas por partida, 532 registros táticos por equipe-partida, 71.034 rallies reconstruídos e zero contatos. O número de rallies não representa ataques ou levantamentos. `matches` registra data, competição, categoria, gênero, temporada e equipes; `player_match_stats` possui número, nome e totais de ataque por jogo; `team_tactical_stats` agrega ataque após recepção positiva/negativa por equipe-jogo, sem individualizar atacante. `rallies` contém rotação e posição da levantadora quando reconstruídas e validadas; isso não identifica quem levantou ou quem atacou. `contacts` prevê sequência, equipe, atleta, fundamento, avaliação e zonas, mas está vazia e não há contrato comprovado que associe, sem ambiguidades, cada levantamento ao ataque.

A inferência de funções do módulo legado é heurística, não identifica uma levantadora observada. O volume individual não permite deduzir a distribuição condicional por recepção ou rotação. A base atual não autoriza valores de previsão, calibração empírica, intervalos validados ou retrospectiva de acionamentos. Não são preenchidas observações artificiais.

## Núcleo de contatos preparado, ainda não integrado ao produto

`cbv.analysis.activation_model` recebe registros sequenciais já auditados, um por distribuição observada, com `team`, `category`, `gender`, `season`, `match_id`, `date`, `target` e, quando conhecidos, `setter`, `rotation`, `pass_quality`. Esses nomes são um contrato interno em memória, não novas colunas no banco. Falta criar e validar um adaptador a partir de uma fonte real de contatos; não basta a tabela existir. O código não decide que um contato de levantamento tenha resultado no ataque seguinte, não reconstrói autoria, nem garante opções presentes em quadra. A integração desse núcleo de contatos e do jogo ao vivo depende dessa etapa; a interface geral de volume acima usa outro módulo. Nenhuma migração de schema é proposta sem a análise da fonte de eventos.

A identidade usa a tupla normalizada clube, categoria, gênero e temporada; campos ausentes invalidam a identidade e impedem a previsão. Outros anos, categorias e gêneros nunca entram no histórico direto. A competição ainda não compõe a identidade, pois a mesma equipe pode disputar mais de uma competição na mesma temporada; nomes ambíguos exigem identificador confiável da fonte.

## Modelo provisório

As categorias são atacantes observadas no histórico daquela equipe-temporada, não necessariamente todas as opções disponíveis naquele instante. Sem pelo menos duas opções históricas, retorna indisponível. Não é possível compartilhar nomes entre equipes como se fossem categorias equivalentes: para incorporar um prior geral seriam necessárias funções ofensivas observadas e comparáveis ou outra representação validada. O núcleo atual **não usa a base geral** como prior e **não está calibrado com ela**.

O prior inicial simétrico tem massa total configurável, provisoriamente 1. Essa escolha fraca não é uma estimativa empírica. Em cada nível, as contagens fora do subconjunto mais específico definem uma distribuição mais geral; ela é convertida em massa inicial de força configurável e atualizada com as contagens do nível seguinte. Usam-se subconjuntos disjuntos para evitar contar a mesma observação repetidamente. A ordem é equipe, passe, rotação e levantadora, omitindo condições desconhecidas. A posterior soma o prior e as contagens e a média divide cada parâmetro pela soma. A sequência ao vivo adiciona apenas observações da equipe e do contexto selecionado. Se surgir uma atacante não contemplada no histórico, a previsão fica indisponível até existir um contrato confiável de opções possíveis, evitando omiti-la silenciosamente.

A entropia normalizada resume concentração entre as opções conhecidas; não é certeza sobre a bola seguinte. O desvio-padrão marginal vem da Dirichlet: `sqrt(p * (1-p) / (sum(alpha)+1))`. Não equivale a um intervalo de credibilidade validado nem inclui incerteza de estimação da força do prior ou da disponibilidade; nenhuma classificação de confiança é atribuída.

## Validação e calibração

`evaluate` ordena por data e treina apenas em datas anteriores, atualizando com jogadas anteriores do mesmo jogo conforme a ordem de entrada; partidas do mesmo dia não alimentam umas às outras. Informar registros em ordem cronológica dentro de cada jogo. Relata log loss, Brier multiclasse, top-1/top-2 e tabelas de calibração (previsão média e frequência para cada faixa), além da quantidade de observações não avaliadas, inclusive atletas novas. A exclusão afeta a representatividade: deve ser divulgada e resolvida com escalações auditadas.

`calibrate_strength` compara uma grade de forças usando log loss cronológico; requer dados reais. O resultado da seleção não é avaliação independente: separe um período posterior para testar a força escolhida. Uma avaliação final deve também comparar baselines, medir cobertura, agrupar incerteza por jogo e verificar deriva e calibração por gênero, categoria e temporada. Com a base atual ambas as rotinas retornam ausência de amostra, não um desempenho fictício.

## Cenários por fase com margens por partida

O painel cruza `player_match_stats.attack_attempts` com `team_tactical_stats` por partida/equipe-temporada. Só entra partida cujo total das contagens individuais conhecidas seja exatamente igual à soma dos ataques em K1 positivo, K1 negativo e K2; números incompatíveis são excluídos. Uma contagem individual ausente não é convertida em zero como dado observado; quando o total conhecido fecha integralmente com o total da equipe, não resta volume agregado a alocar, sob a hipótese de que ambos os relatórios são completos e comparáveis. Dados inconsistentes de origem podem invalidar essa hipótese.

Para cada partida e fase, o cenário proporcional aloca `ataques_atleta × ataques_fase / ataques_equipe`. Assim incorpora composição diferente de fases entre jogos e alterações no volume individual, mas supõe independência da escolha da atleta e da fase *dentro de cada jogo*. A hipótese não é aprendida nem validada pelos totais. O cenário é uma distribuição hipotética, não uma previsão calibrada ou posterior Dirichlet; o ajuste Dirichlet exibido no quadro geral é separado.

Como alternativa à precisão ilusória, a faixa de possibilidades usa, para cada partida, `max(0, ataques_atleta - (ataques_equipe - ataques_fase))` como mínimo e `min(ataques_atleta, ataques_fase)` como máximo. Somam-se limites e divide-se pelo total da fase. São limites de identificação dos dados agregados, não intervalos de credibilidade ou confiança; para diferentes atletas os extremos não têm necessariamente ocorrência simultânea. As faixas valem apenas sob o pressuposto de que as fases formam uma partição dos ataques registrados e são completos. Não usar como indicação de risco da próxima bola.

O painel por rotação reutiliza a formação modal de `lineup-volume-prior-v1`, exclusivamente em rallies com presença reconciliada `RECONSTRUCTED_HIGH`; pondera atletas presentes pelo volume geral da temporada e informa amostras de formação. Trata-se de hipótese para a formação histórica modal, não escalação atual nem frequência de levantamento por rotação. As duas formas de cenário não são combinadas, pois a base não associa fase, rotação e atacante por contato. Não há inferência por levantadora. A atualização durante um jogo e a validação de probabilidades condicionais dependem de eventos de fonte verificável; avaliações sobre margens não comprovam calibração por fase.
