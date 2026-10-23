# Validação da entrega Atlas Tático

Verificação local em 23/10/2026, anterior à publicação.

## Inventário e cobertura

- 583 partidas mantidas no banco.
- 583 páginas oficiais e 583 Match Reports arquivados.
- 571 súmulas e 329 relatórios de líbero disponíveis.
- 429 reconstruções aprovadas: 104 VALID e 325 VALID_WITH_WARNINGS.
- 68.339 pontos de placar elegíveis para a nova análise.
- 97 tentativas FAILED e 57 PARTIAL permanecem explícitas, sem alimentar a análise nova.
- O último snapshot válido de uma tentativa posterior rejeitada permanece armazenado, mas é excluído dos modelos até nova aprovação.

Os pontos são reconstruídos da súmula. Não representam um feed observado de contatos.
O widget original retornou 403; sanções e autoria individual de ações não têm cobertura.
As contagens referem-se a este snapshot e serão atualizadas pela rotina diária.

## Verificação

- Suíte completa: 76 testes passaram em 131,62 s.
- Após o ajuste final de metadados: quatro testes de registry, reconstrução idempotente e preservação de produção passaram em 9,63 s.
- Ruff: verificações de sintaxe e nomes indefinidos aprovadas.
- JavaScript: sintaxe aprovada com Node.
- Navegador Chromium: seis páginas em 1440, 1024, 768 e 390 px; sem erros de JavaScript, NaN ou transbordamento horizontal.
- Interações offline: quadra SO/BP, seleção de rotação, célula da matriz, replay de rally, busca e perfil de atleta, fontes e caderno.
- Os três HTML publicados têm conteúdo idêntico. A promoção usa staging, quality gates e cópia de recuperação.

A avaliação temporal de um modelo de ponto não valida automaticamente a probabilidade de vitória por partida. Modelos novos permanecem experimentais; o baseline pré-jogo logístico L2 permanece ativo. Limitações detalhadas em [LIMITACOES_ATLAS.md](LIMITACOES_ATLAS.md).
