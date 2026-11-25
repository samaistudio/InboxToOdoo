# Instructions for AI coding agents

You are setting up InboxToOdoo for a user. Keep it local and ask before anything leaves the machine.

1. Check that Docker is installed and running, and that Python 3 exists. If not, tell the user what to install; do not install system software without asking.
2. Run `./install.sh --demo` from the repository root. It creates `.env.local` with fresh local passwords, starts all containers, creates the Odoo database `inboxtoodoo` with a fictional company, loads the n8n workflows and mails the demo documents into the local mailbox. It is safe to run again.
3. Open http://localhost:8025 (the local test mailbox). Approval mails arrive within one to two minutes. Walk the user through one invoice mail (the comparison table and the three buttons) and one complaint mail.
4. Odoo is at http://localhost:8069, user `admin`, password in `.env.local`. Vendor bills: Accounting > Vendors > Bills.
5. Settings are two forms: http://localhost:5678/form/einstellungen (complaints, AI provider) and http://localhost:5678/form/rechnungen-einstellungen (invoices).

Ask the user first before:
- putting any cloud AI key into `.env.local` or choosing a cloud provider in the settings (customer and supplier data would go to that provider),
- connecting a real mailbox or a real Odoo database,
- clicking approval buttons on their behalf.

Useful commands: `./reload.sh` rebuilds and reloads the workflows after editing `workflows/src/` or `build_*.py`; `node --test test/rules.test.mjs` runs the unit tests of the fixed rules; `python3 test/run_invoices.py` sends the test invoices one at a time and compares each verdict with the expected one (`--check-only` sends nothing); `docker compose down` stops everything (data stays in Docker volumes).

If the install fails, read `install.log`. The n8n editor (http://localhost:5678) asks for an owner account the first time it is opened; let the user create it.
