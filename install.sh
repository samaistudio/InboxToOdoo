#!/usr/bin/env bash
# InboxToOdoo installer: starts everything, creates a demo Odoo database with a fictional
# wholesaler, loads the workflows. Run it again any time; it skips what is already done.
#   ./install.sh          install and start
#   ./install.sh --demo   also mail the test complaints and invoices into the inbox
set -euo pipefail
cd "$(dirname "$0")"
say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
LOG=install.log
: > "$LOG"
fail() { echo "Failed: $*. Details are in $LOG."; exit 1; }

command -v docker >/dev/null || { echo "Docker is needed: https://docs.docker.com/get-docker/ (macOS: Docker Desktop, OrbStack or Colima)"; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker is installed but not running. Start it and run ./install.sh again."; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 is needed (only for the demo mails and to build the workflows)."; exit 1; }

if [ ! -f .env.local ]; then
  say "Creating .env.local with fresh local passwords"
  cp config/env.example .env.local
  pw=$(python3 -c 'import secrets; print(secrets.token_urlsafe(15))')
  sed -i.bak "s/^ODOO_DB=.*/ODOO_DB=inboxtoodoo/; s/^ODOO_USER=.*/ODOO_USER=admin/; s/^ODOO_PASSWORD=.*/ODOO_PASSWORD=$pw/" .env.local && rm -f .env.local.bak
fi
set -a; . ./.env.local; set +a
mkdir -p data
[ -f data/settings.json ] || cp config/settings.default.json data/settings.json

say "Starting the containers (first time: a few minutes to download)"
docker compose up -d --build

say "Waiting for the database"
until docker compose exec -T db pg_isready -U odoo >/dev/null 2>&1; do sleep 2; done

if ! docker compose exec -T db psql -U odoo -lqt | cut -d'|' -f1 | grep -qw "$ODOO_DB"; then
  say "Creating the Odoo database \"$ODOO_DB\" (German company, SKR03 chart of accounts)"
  docker compose stop odoo >/dev/null
  docker compose run --rm -T odoo odoo -d "$ODOO_DB" -i base --without-demo=all --stop-after-init >>"$LOG" 2>&1 || fail "creating the database"
  docker compose run --rm -T odoo odoo shell -d "$ODOO_DB" --no-http >>"$LOG" 2>&1 <<PY
env.company.write({"country_id": env.ref("base.de").id, "name": "Rheinmark Handels GmbH"})
env.ref("base.user_admin").write({"password": "$ODOO_PASSWORD", "lang": "en_US"})
env.cr.commit()
PY
  docker compose run --rm -T odoo odoo -d "$ODOO_DB" -i sale_management,stock,sale_stock,account,purchase,purchase_stock,l10n_de --without-demo=all --stop-after-init >>"$LOG" 2>&1 || fail "installing the Odoo apps"
  say "Loading the fictional demo company (products, customers, suppliers, orders)"
  docker compose run --rm -T odoo odoo shell -d "$ODOO_DB" --no-http < seed/seed_odoo.py 2>>"$LOG" | tee -a "$LOG" | { grep -E "^(order|products)" || true; }
  docker compose run --rm -T odoo odoo shell -d "$ODOO_DB" --no-http < seed/seed_purchase.py 2>>"$LOG" | tee -a "$LOG" | { grep -E "^(supplier|PO)" || true; }
  # odoo shell does not fail on a Python error, so check that the demo records exist
  check='so = env["sale.order"].search_count([("client_order_ref", "=like", "RW-%")]); po = env["purchase.order"].search_count([("origin", "=like", "EK-%")]); print("SEEDED", "ok" if so >= 6 and po >= 9 else "missing", so, po)'
  found=$(echo "$check" | docker compose run --rm -T odoo odoo shell -d "$ODOO_DB" --no-http 2>>"$LOG" | grep '^SEEDED' || true)
  case "$found" in "SEEDED ok"*) ;; *) fail "loading the demo data (expected 6 sales and 9 purchase orders: ${found:-no answer})";; esac
  docker compose up -d odoo
fi

say "Loading the workflows into n8n"
until curl -s -o /dev/null http://localhost:5678/healthz; do sleep 2; done
retry() { for n in 1 2 3 4 5 6 7 8 9 10; do "$@" >/dev/null 2>&1 && return 0; sleep 5; done; echo "Failed: $*"; return 1; }
docker compose cp config/smtp-credential.json n8n:/tmp/cred.json >/dev/null
retry docker compose exec -T n8n n8n import:credentials --input=/tmp/cred.json
python3 build_workflows.py >/dev/null && python3 build_eingangsrechnung.py >/dev/null
for f in workflows/*.json; do retry docker compose exec -T n8n n8n import:workflow --input=/files/$f; done
for id in rwReklamation001 rwPosteingang002 rwEinstellung003 rwRechnung004 rwRechnEing005 rwRechnEinst006; do
  retry docker compose exec -T n8n n8n publish:workflow --id=$id
done
docker compose restart n8n >/dev/null
until curl -s -o /dev/null http://localhost:5678/healthz; do sleep 2; done

if [ "${1:-}" = "--demo" ]; then
  say "Sending the demo complaints and invoices to the inbox"
  sleep 5
  python3 test/complaints.py >/dev/null && python3 test/invoices_send.py >/dev/null
  echo "Approval mails arrive at http://localhost:8025 within one to two minutes."
fi

say "Ready"
cat <<TXT
  Mailbox (approval mails)  http://localhost:8025
  Odoo                      http://localhost:8069   login: admin / password in .env.local
  Settings: complaints      http://localhost:5678/form/einstellungen
  Settings: invoices        http://localhost:5678/form/rechnungen-einstellungen
  Try it:                   ./install.sh --demo   (or python3 test/complaints.py)
  The AI is a stand-in until you pick a real one in the settings (local Ollama or a cloud key in .env.local).
TXT
