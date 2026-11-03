# Acionamento ofensivo presumido — experimental

O Atlas usa ataques por atleta em cada partida e formação reconstruída para montar uma referência de participação ofensiva para a formação histórica mais frequente em cada rotação. Ela é uma hipótese baseada em dados agregados: não é frequência observada de levantamentos, nem uma previsão validada da próxima bola ou uma escalação atual.

O modelo corrige o volume de ataques pela exposição estimada em rallies com formação `RECONSTRUCTED_HIGH`. A formação define as atletas elegíveis, e a líbero recebe peso zero. Onde a exposição não é confiável, o cálculo conserva o volume de ataques da partida em vez de inventar presença.

Os relatórios também fornecem os totais por fase (K1+, K1− e K2), mas não vinculam cada passe e levantamento à atacante. Variação entre jogos não identifica com segurança 18 efeitos por atleta. Portanto, o modelo **não estima efeito de passe**: `pass_condition_effect` é nulo, os três cenários retornam à mesma referência, com `identified = false`, e a interface informa essa limitação.

Cada análise é restrita à mesma competição, categoria, gênero, temporada e equipe. O índice de suporte descreve a quantidade e concentração de dados da formação, sem representar uma chance de acerto. A fórmula, os limites e a auditoria temporal da distribuição geral estão em [VALIDACAO_ACIONAMENTO.md](VALIDACAO_ACIONAMENTO.md).

Dados independentes que liguem passe, levantadora, atacante e rotação são necessários para validar probabilidades por fase, avaliar calibração e produzir um índice de confiança preditiva.
