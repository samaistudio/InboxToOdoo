"""End-to-end check of the invoice workflow against the expected verdicts.

  python3 test/run_invoices.py               mails each test invoice to the invoice mailbox, waits for its approval mail,
                                             compares the verdict in the subject with the expected one
  python3 test/run_invoices.py inv-02 inv-05 only these cases
  python3 test/run_invoices.py --check-only  sends nothing: checks the newest approval mail per case already in Mailpit

Prints PASS/FAIL per case and exits with 1 if any case fails. Needs the running demo (./install.sh) and, for a
repeatable result, an Odoo state without earlier test bills (test/reset_odoo.py). Cases are sent one at a time,
because the expected verdicts assume that order (inv-04 is a copy of inv-01, inv-06 has no order number).
"""
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "http://localhost:8025/api/v1"
SETTINGS = json.loads((ROOT / "data" / "settings.json").read_text(encoding="utf-8"))
APPROVER = SETTINGS["inv_approval_email"]

# case: (invoice number in the subject, file name in the mail, expected verdict)
EXPECTED = {
    "inv-01": ("RE-2026-1187", "Rechnung_RE-2026-1187.pdf", "Buchbar"),
    "inv-02": ("LW-50231", "Rechnung_LW-50231.pdf", "Abweichung"),
    "inv-03": ("2026/4471", "Rechnung_2026-4471.pdf", "Abweichung"),
    "inv-04": ("RE-2026-1187", "Rechnungskopie_RE-2026-1187.pdf", "Gestoppt"),
    "inv-05": ("RE-2026-1203", "Rechnung_RE-2026-1203.pdf", "Gestoppt"),
    "inv-06": ("LW-50288", "Rechnung_LW-50288.pdf", "Buchbar"),
    "inv-07": ("2026/4502", "Rechnung_2026-4502.pdf", "Abweichung"),
    "inv-08": ("8812", "Ihre_Rechnung_8812.pdf", "Gestoppt"),
    "inv-09": ("RE-2026-1219", "XRechnung_RE-2026-1219.xml", "Buchbar"),
    "inv-10": ("LW-50340", "Rechnung_LW-50340.pdf", "Abweichung"),
    "inv-11": ("2026/4519", "Rechnung_2026-4519.pdf", "Buchbar"),
    "inv-09b": ("RE-2026-1219", "XRechnung_RE-2026-1219.xml", "Gestoppt"),  # the same e-invoice again: duplicate
}
SEND_AS = {"inv-09b": "inv-09"}


def get(path):
    return json.load(urllib.request.urlopen(f"{API}/{path}"))


def approval_mails():
    q = urllib.parse.quote(f"to:{APPROVER} !tag:Vorversion")
    return get(f"search?query={q}&limit=500")["messages"]  # newest first


def verdict(subject):
    m = re.match(r"\[Eingangsrechnung\] (\w+) ·", subject)
    return m.group(1) if m else None


def matches(case, msgs):
    """Approval mails for this case, oldest first."""
    number, filename, _ = EXPECTED[case]
    out = []
    for m in msgs:
        if f"· {number} ·" in m["Subject"]:
            full = get(f"message/{m['ID']}")
            if filename in full["HTML"] + full["Text"]:
                out.append(m)
    return sorted(out, key=lambda m: m["Created"])


def find(case, msgs, check_only):
    found = matches(case, msgs)
    if not check_only:
        return found[-1] if found else None
    # cases that share a document (inv-09 and inv-09b) take the mails in the order they arrived
    nth = [c for c in EXPECTED if EXPECTED[c][:2] == EXPECTED[case][:2]].index(case)
    return found[nth] if len(found) > nth else None


def main(args):
    check_only = "--check-only" in args
    cases = [a for a in args if a in EXPECTED] or list(EXPECTED)
    failed = 0
    for case in cases:
        if not check_only:
            before = {m["ID"] for m in approval_mails()}
            subprocess.run([sys.executable, str(ROOT / "test" / "invoices_send.py"), SEND_AS.get(case, case)], check=True, capture_output=True)
            new = []
            for _ in range(90):
                time.sleep(2)
                new = [m for m in approval_mails() if m["ID"] not in before]
                if new:
                    break
            msg = find(case, new, False)
        else:
            msg = find(case, approval_mails(), True)
        want = EXPECTED[case][2]
        got = verdict(msg["Subject"]) if msg else None
        ok = got == want
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {case:<7} expected {want:<10} got {got or 'no mail'}")
    print(f"\n{len(cases) - failed}/{len(cases)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
