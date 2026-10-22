#!/usr/bin/env bash
# Configura o agendamento no crontab do Linux para rodar todos os dias às 03:00

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
PYTHON_BIN="$DIR/.venv/bin/python"
SCRIPT_PATH="$DIR/scripts/daily_update.py"
LOG_PATH="$DIR/data/cron_sync.log"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Erro: Ambiente virtual não encontrado em $PYTHON_BIN"
    exit 1
fi

CRON_JOB="0 3 * * * cd '$DIR' && '$PYTHON_BIN' '$SCRIPT_PATH' >> '$LOG_PATH' 2>&1"

# Verifica se já está configurado no crontab
crontab -l 2>/dev/null | grep -F "$SCRIPT_PATH" >/dev/null && {
    echo "✓ O pipeline diário já está agendado no crontab local para rodar às 03:00."
    exit 0
}

# Adiciona ao crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "✓ Agendamento criado com sucesso no crontab local: Todos os dias às 03:00 da manhã."
echo "  Comando: $CRON_JOB"
