# Cenários proporcionais de acionamento — experimental

A base dispõe dos ataques individuais por jogo, dos ataques por fase da equipe e de parte das formações reconstruídas em cada rotação. Não dispõe do vínculo de cada passe e levantamento ao atleta que atacou. Consequentemente as saídas são **cenários condicionais a hipóteses**, não percentuais observados, probabilidades preditivas validadas ou prova de escolha da levantadora.

## Cálculo, por competição, categoria, naipe, temporada e equipe

1. Para cada jogo, incluir apenas partidas com ao menos 80% dos rallies com rotação e seis nomes de formação reconstruídos com alta confiança; todos os atletas que atacaram precisam aparecer nesses rallies. Exigir também que a soma dos ataques individuais coincida com a soma K1+, K1− e K2.
2. Para cada atleta, distribuir seu total de ataques no jogo entre as rotações na proporção dos rallies em que esteve presente em cada uma. Exemplo: 20 ataques e 25% de sua exposição em P1 produzem 5 ataques **alocados**, não cinco ataques observados em P1. Supõe-se o mesmo ritmo de ataque por rally entre rotações dentro daquele jogo.
3. Para os cenários por fase, multiplicar cada alocação pela fração de ataques da equipe que veio daquela fase no jogo. Supõe-se a mesma composição de fases para cada atleta e rotação naquele jogo. Diferenças por fase podem surgir da combinação de jogos com exposições e proporções de fase diferentes; elas não identificam o efeito do passe sobre o destino do levantamento.
4. Somar as alocações dos jogos elegíveis e normalizar apenas entre os atletas da formação histórica mais frequente da rotação. Assim, a distribuição é condicional à formação selecionada e **não estima** quem está em quadra hoje. Atletas com o mesmo nome e números distintos são separados por camisa dentro do recorte; se o número mudar, a identidade deverá ser revisada.

Uma equipe pode não ter dados suficientes para uma rotação ou fase. O gráfico marca a lacuna e apresenta uma referência geral quando disponível, sem chamá-la de estimativa específica. Um valor zero no cenário é zero alocado nos dados utilizados, não comprovação de impossibilidade. A líbero identificada é tratada como zero estrutural.

## Sensibilidade e suporte

Com pelo menos três jogos elegíveis para uma fase, recalcular o percentual omitindo um jogo por vez. A faixa exibida é a menor e a maior estimativa obtida nesses recálculos. Ela mostra dependência dos jogos incluídos; **não é intervalo de confiança nem limite de todos os valores possíveis** e não mede erro por falta dos contatos.

O índice de suporte continua a resumir quantidade e concentração das formações reconstruídas. É uma heurística de cobertura e não chance de acerto. Fórmula e limitações em [VALIDACAO_ACIONAMENTO.md](VALIDACAO_ACIONAMENTO.md).

Para validar probabilidades por atleta, fase e rotação seriam necessários contatos independentes ligando recepção, levantamento e atacante. A avaliação cronológica descrita no outro documento verifica apenas distribuição geral sob condições restritas; não valida as células do cenário.
