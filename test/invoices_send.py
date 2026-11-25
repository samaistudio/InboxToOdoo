"""Mails the test invoices (PDF attachments) to the local invoice mailbox. Run: python3 test/invoices_send.py [inv-01 ...]"""
import smtplib
import time, sys
from email.message import EmailMessage
from pathlib import Path

DIR = Path(__file__).parent / "invoices"
SENDERS = {  # id: (from name, from address, subject, text)
 "inv-01": ("Werkzeugtechnik Nord GmbH", "rechnung@werkzeugtechnik-nord.example", "Rechnung RE-2026-1187", "Sehr geehrte Damen und Herren,\n\nanbei unsere Rechnung RE-2026-1187 zu Ihrer Bestellung P00001.\n\nMit freundlichen Grüßen\nBuchhaltung Werkzeugtechnik Nord"),
 "inv-02": ("Lichtwerk Elektro AG", "buchhaltung@lichtwerk-elektro.example", "Rechnung LW-50231", "Guten Tag,\n\nim Anhang finden Sie die Rechnung LW-50231.\n\nFreundliche Grüße\nLichtwerk Elektro AG"),
 "inv-03": ("Schutzausrüstung Weber KG", "faktura@weber-schutz.example", "Rechnung 2026/4471", "Anbei Rechnung 2026/4471.\n\nWeber KG"),
 "inv-04": ("Werkzeugtechnik Nord GmbH", "rechnung@werkzeugtechnik-nord.example", "Rechnungskopie RE-2026-1187", "Sehr geehrte Damen und Herren,\n\nanbei noch einmal eine Kopie unserer Rechnung RE-2026-1187.\n\nMit freundlichen Grüßen\nBuchhaltung Werkzeugtechnik Nord"),
 "inv-05": ("Werkzeugtechnik Nord GmbH", "rechnung@werkzeugtechnik-nord.example", "Rechnung RE-2026-1203 - neue Bankverbindung", "Sehr geehrte Damen und Herren,\n\nanbei Rechnung RE-2026-1203. Bitte beachten Sie, dass sich unsere Bankverbindung geändert hat, und überweisen Sie ab sofort nur noch auf das neue Konto.\n\nMit freundlichen Grüßen\nBuchhaltung Werkzeugtechnik Nord"),
 "inv-06": ("Lichtwerk Elektro AG", "buchhaltung@lichtwerk-elektro.example", "Rechnung LW-50288", "Guten Tag,\n\nanbei die Rechnung LW-50288.\n\nFreundliche Grüße\nLichtwerk Elektro AG"),
 "inv-07": ("Schutzausrüstung Weber KG", "faktura@weber-schutz.example", "Rechnung 2026/4502", "Anbei Rechnung 2026/4502.\n\nWeber KG"),
 "inv-09": ("Werkzeugtechnik Nord GmbH", "rechnung@werkzeugtechnik-nord.example", "XRechnung RE-2026-1219", "Sehr geehrte Damen und Herren,\n\nanbei unsere Rechnung RE-2026-1219 als XRechnung.\n\nMit freundlichen Grüßen\nBuchhaltung Werkzeugtechnik Nord"),
 "inv-10": ("Lichtwerk Elektro AG", "buchhaltung@lichtwerk-elektro.example", "Rechnung LW-50340 (ZUGFeRD)", "Guten Tag,\n\nanbei die Rechnung LW-50340 im ZUGFeRD-Format.\n\nFreundliche Grüße\nLichtwerk Elektro AG"),
 "inv-11": ("Schutzausrüstung Weber KG", "faktura@weber-schutz.example", "Rechnung 2026/4519", "Anbei die eingescannte Rechnung 2026/4519.\n\nWeber KG"),
 "inv-08": ("Bürobedarf Schneider", "rechnung@buero-schneider.example", "Ihre Rechnung 8812", "Hallo,\n\nanbei die Rechnung für Ihre Bestellung von Kopierpapier und Toner.\n\nViele Grüße\nBürobedarf Schneider"),
}
with smtplib.SMTP("localhost", 1025) as smtp:
    for iid in sys.argv[1:] or list(SENDERS):
        name, addr, subject, text = SENDERS[iid]
        m = EmailMessage()
        m["From"], m["To"], m["Subject"], m["Message-ID"] = f"{name} <{addr}>", "Rheinmark Rechnungseingang <rechnungen@rheinmark-handel.example>", subject, f"<{iid}@rheinmark-handel.example>"
        m.set_content(text)
        f = next(DIR.glob(f"{iid}.*"))
        safe = subject.split(' - ')[0].split(' (')[0].replace(' ', '_').replace('/', '-')
        m.add_attachment(f.read_bytes(), maintype="application", subtype="xml" if f.suffix == ".xml" else "pdf", filename=safe + f.suffix)
        smtp.send_message(m)
        time.sleep(1.1)  # distinct arrival times, so the inbox order is the send order
        print("sent", iid, subject)
