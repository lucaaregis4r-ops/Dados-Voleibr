#!/usr/bin/env bash
# ============================================================
# CBV Volley Data — Aplicação Web da Comissão Técnica (CT)
# Clique duas vezes neste arquivo na pasta para abrir a aplicação
# ============================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Ativa o ambiente virtual se existir
if [ -f "$DIR/.venv/bin/activate" ]; then
    source "$DIR/.venv/bin/activate"
fi

# Executa a aplicação web unificada
python3 -m cbv app
