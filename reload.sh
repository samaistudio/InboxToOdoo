#!/usr/bin/env bash
# Rebuild the workflow files and re-import them into the running n8n.
# Run after changing anything in workflows/src/ or a build_*.py. Details go to reload.log.
set -euo pipefail
cd "$(dirname "$0")"
LOG=reload.log
: > "$LOG"
fail() { echo "Failed: $*. Details are in $LOG."; exit 1; }
# same helper as in install.sh, but the output is kept in the log
retry() { for n in 1 2 3 4 5; do "$@" >>"$LOG" 2>&1 && return 0; sleep 3; done; fail "$*"; }

python3 build_workflows.py >>"$LOG" 2>&1 || fail "building the complaint workflows"
python3 build_eingangsrechnung.py >>"$LOG" 2>&1 || fail "building the invoice workflows"
curl -s -o /dev/null http://localhost:5678/healthz || fail "n8n is not running (start it with docker compose up -d)"
for f in workflows/*.json; do retry docker compose exec -T n8n n8n import:workflow --input=/files/$f; done
for id in rwReklamation001 rwPosteingang002 rwEinstellung003 rwRechnung004 rwRechnEing005 rwRechnEinst006; do
  retry docker compose exec -T n8n n8n publish:workflow --id=$id
done
docker compose restart n8n >>"$LOG" 2>&1 || fail "restarting n8n"
for n in $(seq 1 60); do curl -s -o /dev/null http://localhost:5678/healthz && break; sleep 1; done
curl -s -o /dev/null http://localhost:5678/healthz || fail "n8n did not come back after the restart"
sleep 3
echo "reloaded"
