"""Builds eight fictional supplier invoices as PDFs (three different layouts) in test/invoices/.
Run: python3 test/make_invoices.py   (needs Google Chrome for HTML -> PDF; set CHROME to its path if it is not the macOS default)"""
import os
import subprocess
from pathlib import Path

OUT = Path(__file__).parent / "invoices"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def iban_de(blz, account):
    bban = f"{blz}{account:010d}"
    num = int("".join(str(int(c, 36)) for c in bban + "DE00"))
    return f"DE{98 - num % 97:02d}{bban}"


def fmt_iban(i):
    return " ".join(i[k:k + 4] for k in range(0, len(i), 4))


def eur(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


SUP = {
    "nord": dict(name="Werkzeugtechnik Nord GmbH", street="Hafenstraße 12", city="20457 Hamburg", vat="DE298765435",
                 iban=iban_de("99020050", 1234567), bank="Fiktivbank Hamburg", mail="rechnung@werkzeugtechnik-nord.example", style="a"),
    "licht": dict(name="Lichtwerk Elektro AG", street="Leopoldstraße 88", city="80802 München", vat="DE314159262",
                  iban=iban_de("99070150", 7654321), bank="Fiktivbank München", mail="buchhaltung@lichtwerk-elektro.example", style="b"),
    "weber": dict(name="Schutzausrüstung Weber KG", street="Industrieweg 5", city="44147 Dortmund", vat="DE271828180",
                  iban=iban_de("99044050", 5550123), bank="Fiktivbank Dortmund", mail="faktura@weber-schutz.example", style="c"),
    "schneider": dict(name="Bürobedarf Schneider e.K.", street="Ehrenstraße 40", city="50672 Köln", vat="DE123456788",
                      iban=iban_de("99037050", 3141592), bank="Fiktivbank Köln", mail="rechnung@buero-schneider.example", style="b"),
}

INVOICES = [  # id, supplier, number, date, due, our PO, [(code, text, qty, price)], overrides
    ("inv-01", "nord", "RE-2026-1187", "20.11.2026", "04.12.2026", "P00001",
     [("BS-18", "Akku-Bohrschrauber BS-18", 20, 92.00), ("WS-125", "Winkelschleifer WS-125", 10, 54.00)], {}),
    ("inv-02", "licht", "LW-50231", "21.11.2026", "21.12.2026", "P00002",
     [("LED-30", "LED-Arbeitsleuchte LED-30", 40, 20.90), ("LM-50", "Laser-Entfernungsmesser LM-50", 10, 71.00)], {}),
    ("inv-03", "weber", "2026/4471", "22.11.2026", "06.12.2026", "P00003",
     [("SB-1", "Schutzbrille SB-1 klar", 200, 3.20), ("WK-PRO", "Werkzeugkoffer Pro", 30, 31.00)], {}),
    ("inv-04", "nord", "RE-2026-1187", "20.11.2026", "04.12.2026", "P00001",
     [("BS-18", "Akku-Bohrschrauber BS-18", 20, 92.00), ("WS-125", "Winkelschleifer WS-125", 10, 54.00)], {"copy": True}),
    ("inv-05", "nord", "RE-2026-1203", "23.11.2026", "07.12.2026", "P00004",
     [("BS-18", "Akku-Bohrschrauber BS-18", 10, 92.00)], {"iban": iban_de("99550010", 8812345), "bank": "Fiktivbank Frankfurt",
                                                           "note": "Bitte beachten Sie unsere neue Bankverbindung."}),
    ("inv-06", "licht", "LW-50288", "23.11.2026", "23.12.2026", None,
     [("LED-30", "LED-Arbeitsleuchte LED-30", 15, 19.50)], {}),
    ("inv-07", "weber", "2026/4502", "23.11.2026", "07.12.2026", "P00006",
     [("SB-1", "Schutzbrille SB-1 klar", 100, 3.20)], {"gross_override": 390.80}),
    ("inv-08", "schneider", "8812", "24.11.2026", "08.12.2026", None,
     [("", "Kopierpapier A4, 500 Blatt", 10, 4.99), ("", "Toner schwarz TN-2420", 1, 89.00)], {}),
]

CSS = {
 "a": "body{font-family:Arial,sans-serif;font-size:10pt;color:#222;margin:22mm 20mm}h1{font-size:20pt;color:#0b3d6e;margin:0 0 4mm}"
      ".top{display:flex;justify-content:space-between}.logo{font-size:15pt;font-weight:700;color:#0b3d6e}table{width:100%;border-collapse:collapse;margin-top:8mm}"
      "th{background:#0b3d6e;color:#fff;text-align:left;padding:5px}td{padding:5px;border-bottom:1px solid #ddd}.r{text-align:right}.sum td{border:none}",
 "b": "body{font-family:Georgia,serif;font-size:10.5pt;color:#111;margin:20mm 22mm}h1{font-size:16pt;letter-spacing:.2em;text-transform:uppercase;margin:10mm 0 4mm}"
      ".top{display:flex;justify-content:space-between;border-bottom:2px solid #111;padding-bottom:4mm}.logo{font-size:18pt;font-style:italic}"
      "table{width:100%;border-collapse:collapse;margin-top:6mm}th{border-bottom:1px solid #111;text-align:left;padding:4px}td{padding:4px}.r{text-align:right}.sum td{padding:2px 4px}",
 "c": "body{font-family:Helvetica,Arial,sans-serif;font-size:9.5pt;color:#333;margin:18mm 18mm}h1{font-size:13pt;margin:6mm 0 2mm;color:#b35400}"
      ".top{display:flex;justify-content:space-between;background:#f4f1ec;padding:5mm}.logo{font-size:14pt;font-weight:700}"
      "table{width:100%;border-collapse:collapse;margin-top:5mm;font-size:9pt}th,td{border:1px solid #ccc;padding:4px}.r{text-align:right}.sum td{border:none}",
}

OUT.mkdir(exist_ok=True)
for iid, skey, num, date, due, po, lines, ov in INVOICES:
    s = SUP[skey]
    iban, bank = ov.get("iban", s["iban"]), ov.get("bank", s["bank"])
    net = round(sum(q * p for _, _, q, p in lines), 2)
    vat = round(net * 0.19 + 1e-9, 2)
    gross = ov.get("gross_override", round(net + vat, 2))
    rows = "".join(f"<tr><td>{i + 1}</td><td>{c}</td><td>{t}</td><td class=r>{q}</td><td class=r>{eur(p)} €</td><td class=r>{eur(q * p)} €</td></tr>"
                   for i, (c, t, q, p) in enumerate(lines))
    po_line = f"Ihre Bestellung: {po}<br>" if po else ""
    html = f"""<!doctype html><html lang=de><head><meta charset=utf-8><style>{CSS[s['style']]}</style></head><body>
<div class=top><div><div class=logo>{s['name']}</div>{s['street']} · {s['city']}</div>
<div style="text-align:right">Rechnungsnr.: <b>{num}</b><br>Rechnungsdatum: {date}<br>{po_line}Kundennr.: RW-4410</div></div>
<p style="margin-top:10mm">Rheinmark Handels GmbH<br>Einkauf / Kreditorenbuchhaltung<br>Industriestraße 7<br>50735 Köln</p>
<h1>Rechnung{' (Kopie)' if ov.get('copy') else ''}</h1>
<p>Für die Lieferung berechnen wir Ihnen:</p>
<table><tr><th>Pos.</th><th>Art.-Nr.</th><th>Bezeichnung</th><th class=r>Menge</th><th class=r>Einzelpreis</th><th class=r>Gesamt</th></tr>{rows}</table>
<table class=sum style="width:45%;margin-left:55%;margin-top:4mm">
<tr><td>Nettobetrag</td><td class=r>{eur(net)} €</td></tr><tr><td>zzgl. 19 % USt.</td><td class=r>{eur(vat)} €</td></tr>
<tr><td><b>Rechnungsbetrag</b></td><td class=r><b>{eur(gross)} €</b></td></tr></table>
<p style="margin-top:8mm">Zahlbar ohne Abzug bis {due}.{(' ' + ov['note']) if ov.get('note') else ''}</p>
<p style="font-size:8.5pt;color:#555;margin-top:12mm">{s['name']} · USt-IdNr. {s['vat']} · {bank} · IBAN {fmt_iban(iban)}<br>
Alle Angaben fiktiv, Testdokument.</p></body></html>"""
    h = OUT / f"{iid}.html"
    h.write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT / (iid + '.pdf')}", h.as_uri()],
                   stderr=subprocess.DEVNULL, check=True)
    h.unlink()
    print(iid, s["name"], num, eur(gross), "€")
