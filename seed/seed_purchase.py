# odoo shell: fictional suppliers with VAT IDs and bank accounts, confirmed purchase orders and
# goods receipts for the invoice automation. Idempotent (looks records up by reference first).
from datetime import datetime, timedelta

env = env  # noqa: F821
now = datetime(2026, 11, 24, 9, 0)


def iban_de(blz, account):
    """Valid German IBAN (checksum) for a made-up bank code and account number."""
    bban = f"{blz}{account:010d}"
    num = int("".join(str(int(c, 36)) for c in bban + "DE00"))
    return f"DE{98 - num % 97:02d}{bban}"


SUPPLIERS = [  # ref, name, vat, city, street, email, iban
    ("L-2001", "Werkzeugtechnik Nord GmbH", "DE298765435", "Hamburg", "Hafenstraße 12", "rechnung@werkzeugtechnik-nord.example", iban_de("99020050", 1234567)),
    ("L-2002", "Lichtwerk Elektro AG", "DE314159262", "München", "Leopoldstraße 88", "buchhaltung@lichtwerk-elektro.example", iban_de("99070150", 7654321)),
    ("L-2003", "Schutzausrüstung Weber KG", "DE271828180", "Dortmund", "Industrieweg 5", "faktura@weber-schutz.example", iban_de("99044050", 5550123)),
]
R, B = env["res.partner"], env["res.partner.bank"]
sup = {}
for ref, name, vat, city, street, email, iban in SUPPLIERS:
    p = R.search([("ref", "=", ref)], limit=1) or R.create({"ref": ref, "name": name, "is_company": True, "vat": vat, "city": city,
                                                            "street": street, "email": email, "country_id": env.ref("base.de").id, "supplier_rank": 1})
    if not B.search([("partner_id", "=", p.id)]):
        B.create({"partner_id": p.id, "acc_number": iban})
    sup[ref] = p
    print("supplier", ref, name, vat, iban)

P = {p.default_code: p for p in env["product.product"].search([("default_code", "!=", False)])}
ORDERS = [  # our ref, supplier, [(code, qty ordered, price, qty received)], days ago
    ("EK-1001", "L-2001", [("BS-18", 20, 92.00, 20), ("WS-125", 10, 54.00, 10)], 12),
    ("EK-1002", "L-2002", [("LED-30", 40, 19.50, 40), ("LM-50", 10, 71.00, 10)], 10),
    ("EK-1003", "L-2003", [("SB-1", 200, 3.20, 200), ("WK-PRO", 30, 31.00, 20)], 9),
    ("EK-1004", "L-2001", [("BS-18", 10, 92.00, 10)], 6),
    ("EK-1005", "L-2002", [("LED-30", 15, 19.50, 15)], 5),
    ("EK-1006", "L-2003", [("SB-1", 100, 3.20, 100)], 4),
    ("EK-1007", "L-2001", [("WS-125", 6, 54.00, 6)], 3),        # paid by XRechnung (XML)
    ("EK-1008", "L-2002", [("LM-50", 4, 71.00, 4)], 3),         # ZUGFeRD PDF, price above order
    ("EK-1009", "L-2003", [("WK-PRO", 12, 31.00, 12)], 2),      # scanned paper invoice
]
PO = env["purchase.order"]
for ref, sref, lines, days in ORDERS:
    if PO.search([("origin", "=", ref)]):
        continue
    when = now - timedelta(days=days)
    po = PO.create({"partner_id": sup[sref].id, "origin": ref, "date_order": when,
                    "order_line": [(0, 0, {"product_id": P[c].id, "product_qty": q, "price_unit": pr}) for c, q, pr, _ in lines]})
    po.button_confirm()
    rec = {P[c].id: r for c, _, _, r in lines}
    for pick in po.picking_ids:
        for m in pick.move_ids:
            m.quantity = rec[m.product_id.id]
        pick.with_context(skip_backorder=True, picking_ids_not_to_backorder=pick.ids).button_validate()
        pick.write({"date_done": when + timedelta(days=2)})
    print("PO", po.name, ref, sup[sref].name, [(l.product_id.default_code, l.product_qty, l.qty_received) for l in po.order_line])
env.cr.commit()
