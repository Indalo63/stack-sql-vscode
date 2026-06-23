#!/usr/bin/env bash
# Wrapper para cron: carga variables de entorno y ejecuta sync_boe.py
# Crontab: 0 4 * * 0  /home/indalo/dev/stack-sql-vscode/scripts/cron_sync_boe.sh

set -a
source /home/indalo/dev/stack-sql-vscode/.env
set +a

cd /home/indalo/dev/stack-sql-vscode
python3 scripts/sync_boe.py >> logs/sync_boe.log 2>&1
