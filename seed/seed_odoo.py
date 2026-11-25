# Run inside `odoo shell` against the local test database. Creates a small, fictional
# tool wholesaler: products in stock, B2B and B2C customers, confirmed orders that were
# delivered and invoiced on different dates (some inside, one outside warranty).
# Safe to run again: records are found by a reference before anything is created.
# The dates are fixed (November 2026), so the warranty cases give the documented results until about October 2027.
from datetime import datetime, timedelta

env = env  # noqa: F821  (provided by odoo shell)
now = datetime(2026, 11, 24, 10, 0)
company = env.company
company.write({"name": "Rheinmark Handels GmbH", "email": "service@rheinmark-handel.example", "phone": "+49 221 4710 123"})

PRODUCTS = [  # code, name, price
    ("BS-18", "Akku-Bohrschrauber BS-18", 149.90),
    ("WS-125", "Winkelschleifer WS-125", 89.90),
    ("WK-PRO", "Werkzeugkoffer Pro", 59.90),
    ("LM-50", "Laser-Entfernungsmesser LM-50", 119.00),
    ("LED-30", "Arbeitsleuchte LED-30", 34.90),
    ("SB-1", "Schutzbrille SB-1", 9.90),
]
P = env["product.product"]
prod = {}
for code, name, price in PRODUCTS:
    p = P.search([("default_code", "=", code)], limit=1)
    if not p:  # stock is added only when the product is created, so a second run does not add 50 more
        p = P.create({"name": name, "default_code": code, "list_price": price, "is_storable": True,
                      "type": "consu", "invoice_policy": "delivery"})
        env["stock.quant"]._update_available_quantity(p, env.ref("stock.stock_location_stock"), 50)
    prod[code] = p

CUSTOMERS = [  # ref, name, email, is_company, lang
    ("K-1001", "Becker Haustechnik GmbH", "einkauf@becker-haustechnik.example", True, "de_DE"),
    ("K-1002", "Anna Schulz", "anna.schulz@privat.example", False, "de_DE"),
    ("K-1003", "Elektro Yilmaz KG", "info@elektro-yilmaz.example", True, "de_DE"),
    ("K-1004", "Jonas Weber", "jonas.weber@privat.example", False, "de_DE"),
    ("K-1005", "Sarah Miller", "sarah.miller@privat.example", False, "en_US"),
    ("K-1006", "Malerbetrieb Krüger", "kontakt@maler-krueger.example", True, "de_DE"),
]
for code in ("de_DE",):
    if not env["res.lang"].search([("code", "=", code), ("active", "=", True)]):
        env["res.lang"]._activate_lang(code)
R = env["res.partner"]
cust = {}
for ref, name, email, is_co, lang in CUSTOMERS:
    c = R.search([("ref", "=", ref)], limit=1) or R.create({"ref": ref, "name": name, "email": email, "is_company": is_co, "lang": lang})
    cust[ref] = c

ORDERS = [  # client ref, customer, [(product, qty)], days ago delivered
    ("RW-2026-0412", "K-1001", [("BS-18", 4), ("SB-1", 10)], 21),
    ("RW-2026-0431", "K-1002", [("LM-50", 1)], 9),
    ("RW-2026-0388", "K-1003", [("WS-125", 2), ("WK-PRO", 1)], 40),
    ("RW-2023-0117", "K-1004", [("BS-18", 1)], 3 * 365 + 20),   # outside warranty
    ("RW-2026-0447", "K-1005", [("LED-30", 2)], 6),
    ("RW-2026-0450", "K-1006", [("WK-PRO", 3)], 4),
]
SO = env["sale.order"]
for ref, cref, lines, days in ORDERS:
    if SO.search([("client_order_ref", "=", ref)]):
        continue
    when = now - timedelta(days=days)
    so = SO.create({"partner_id": cust[cref].id, "client_order_ref": ref,
                    "order_line": [(0, 0, {"product_id": prod[c].id, "product_uom_qty": q}) for c, q in lines]})
    so.action_confirm()
    for pick in so.picking_ids:
        for m in pick.move_ids:
            m.quantity = m.product_uom_qty
        pick.button_validate()
        pick.write({"date_done": when})
    so.write({"date_order": when - timedelta(days=2)})
    inv = so._create_invoices()
    inv.write({"invoice_date": when.date()})
    inv.action_post()
    print("order", so.name, ref, cust[cref].name, "delivered", when.date(), "invoice", inv.name)

env.cr.commit()
print("products", len(prod), "customers", len(cust), "orders", SO.search_count([("client_order_ref", "like", "RW-")]))
