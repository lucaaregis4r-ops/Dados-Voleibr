# Acionamento ofensivo presumido — modelo experimental

## Objetivo

O Atlas tenta responder uma pergunta tática útil mesmo sem possuir contatos observados de levantamento:

> **Dada a rotação, a formação disponível e o perfil de passe, qual é a participação ofensiva presumida de cada atleta?**

O resultado **não é frequência observada da levantadora**. É uma inferência ecológica construída a partir de margens agregadas e exposição reconstruída.

## O que a base realmente possui

A base combina três fontes úteis:

1. `player_match_stats`: ataques por atleta em cada partida;
2. `team_tactical_stats`: ataques da equipe após recepção positiva (K1+), recepção negativa (K1−) e transição (K2);
3. rallies reconstruídos: rotação e, quando `RECONSTRUCTED_HIGH`, formação/presença em quadra.

A tabela de contatos continua sem uma fonte auditada que ligue passe → levantamento → atacante. Portanto o Atlas não preenche contatos artificiais.

## 1. Disponibilidade estrutural

A formação reconstruída entra antes do modelo probabilístico.

- atleta ausente da formação: não é candidata naquela rotação;
- líbero presente: peso ofensivo estrutural igual a zero;
- uma central substituída pelo líbero fica fora da distribuição porque não está na formação, não porque exista uma regra fixa "central no fundo = zero";
- se a central permanecer em quadra, o modelo não inventa sua substituição.

Somente formações `RECONSTRUCTED_HIGH` participam desta etapa.

## 2. Exposição por rotação

O número bruto de ataques de uma atleta é corrigido pela exposição reconstruída.

Para cada partida, o Atlas conta quantos rallies confiáveis ocorreram em P1–P6 e em quantos deles cada atleta estava presente. Isso evita interpretar como preferência da levantadora uma diferença causada apenas por tempo desigual em quadra ou por uma rotação aparecer mais vezes.

O prior de uso ofensivo parte, portanto, de uma intensidade aproximada:

`ataques da atleta / oportunidades equivalentes com presença reconstruída`

Quando não existe cobertura confiável de formação em uma partida, o modelo conserva o volume bruto em vez de inventar exposição.

## 3. Efeito do passe como mistura ecológica

O Atlas não usa multiplicadores manuais do tipo "central ×2,3 no passe positivo".

Para cada equipe e partida reconciliada, o modelo conhece:

- a participação de cada atleta nos ataques totais;
- a composição dos ataques da equipe em K1+, K1− e K2;
- a exposição da atleta em cada rotação.

A matriz latente tem 18 células por atleta:

`P1..P6 × {K1+, K1−, K2}`

Como as células não são observadas diretamente, cada partida fornece uma mistura. A feature de uma célula é:

`exposição da atleta na rotação × proporção daquela fase ofensiva no jogo`

O alvo é a participação ofensiva da atleta na partida.

O ajuste usa **Bayesian ridge**: uma regressão regularizada cuja média a priori é o uso ofensivo histórico corrigido por exposição. Assim, células pouco identificadas são puxadas para o comportamento geral da atleta em vez de gerar probabilidades extremas.

Esta é uma associação ecológica regularizada. Ela não recupera qual passe específico terminou em qual atacante.

## 4. Gate de identificação

O efeito de passe só é ativado quando existe variação suficiente entre partidas.

Na versão `lineup-ecological-bayes-v2`:

- mínimo de 6 partidas reconciliadas;
- desvio-padrão mínimo de 0,05 na proporção de K1+ entre partidas;
- totais individuais de ataque devem fechar exatamente com K1+ + K1− + K2 naquela partida;
- deve existir exposição de formação confiável.

Se essas condições não forem atendidas, `pass_condition_effect = null` e K1+/K1−/K2 usam o prior de rotação/formação. O Atlas prefere dizer **"efeito não identificado"** a fabricar uma diferença.

## 5. Saída do modelo

Cada rotação passa a expor:

- `distribution`: prior de uso ofensivo corrigido por exposição entre as atletas da formação modal;
- `pass_scenarios.positive`: cenário K1+;
- `pass_scenarios.negative`: cenário K1−;
- `pass_scenarios.transition`: cenário K2;
- `structural_zero`: marca atleta sem possibilidade ofensiva naquela formação (por exemplo, líbero);
- `pass_condition_effect`: diagnóstico do modelo apenas quando o efeito é identificável;
- amostra de rallies, partidas e versão do modelo.

Exemplo conceitual:

| P3 | K1+ | K1− |
|---|---:|---:|
| Atleta A | 42% | 25% |
| Atleta B | 31% | 46% |
| Atleta C | 27% | 29% |
| Central substituída | 0% | 0% |

Esses percentuais devem ser lidos como **acionamento ofensivo presumido**, não como contagem observada de levantamentos.

## 6. O que não fazer

Não interpretar a matriz como causalidade da qualidade do passe sobre a escolha da levantadora. Jogos com mais K1+ podem diferir também em adversário, escalação, tempo de quadra e estratégia.

Não usar correlação de Pearson bruta como probabilidade. Ataques e fases são composições que somam 100%, portanto correlações simples podem surgir mecanicamente.

Não reutilizar a mesma evidência duas vezes como prior e como atualização. O ridge aplica a regularização dentro do mesmo ajuste e deixa explícita a força do prior.

Não misturar temporadas, categorias ou naipes. O pipeline já calcula o modelo dentro do cohort corrente.

## 7. Validação necessária

A próxima etapa metodológica é comparar, cronologicamente, três níveis:

1. prior de volume puro;
2. volume + formação/rotação;
3. volume + formação/rotação + composição de passe.

O terceiro modelo só deve ser considerado uma melhoria se reduzir erro fora da amostra. Com contatos reais no futuro, a validação passa a usar log loss, Brier multiclasse, top-1/top-2 e calibração das probabilidades por faixa.

Até existir essa fonte, o Atlas deve continuar rotulando o modelo como **EXPERIMENTAL** e exibindo a limitação de inferência ecológica.
