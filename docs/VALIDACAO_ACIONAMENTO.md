# Acionamento presumido: validação e suporte

O vínculo real entre passe, levantadora e atacante não está disponível. A análise por rotação e fase reparte os ataques individuais de cada jogo segundo a exposição individual por rotação e a fração de ataques da equipe por fase. São premissas proporcionais explícitas, não efeitos estimados de passe. Nenhuma diferença entre fases deve ser interpretada como comportamento observado da levantadora ou previsão validada.

O **índice de suporte da formação** é uma heurística, não uma probabilidade de acerto nem intervalo estatístico: 100 × (rallies da formação modal / rallies com formação elegível) × min(rallies elegíveis / 100, 1) × min(jogos com formação elegível / 5, 1). Os cortes de 100 rallies e 5 jogos são escolhas descritivas, não limiares validados. Não mede a precisão da alocação de ataques. O aplicativo exibe separadamente o número de jogos efetivamente usados pelo cenário.

A sensibilidade por retirada de um jogo depende apenas dos jogos selecionados. É omitida com menos de três jogos com alocação na fase. Não capta incerteza das suposições nem oferece cobertura estatística formal.

`python scripts/backtest_attack_volume.py` audita a distribuição geral usando jogos de datas anteriores e comparando histórico com uniforme, com o conjunto de atacantes do jogo avaliado conhecido para a normalização. É um diagnóstico condicional que não valida a próxima bola, a alocação por rotação, a associação por fase ou a calibração de probabilidades. Um teste real por célula exige dados independentes que registrem o atleta acionado junto à fase e rotação.
