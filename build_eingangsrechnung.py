"""Builds the incoming-invoice workflows in workflows/. Run: python3 build_eingangsrechnung.py

  4. Eingangsrechnung: Prüfung       – document from the mailbox, read by Odoo (e-invoice) or the AI (PDF, scan after OCR),
                                       fixed checks (sums, VAT ID, IBAN), 3-way match with Odoo (order, receipt, invoice),
                                       duplicate and bank-account stop, draft vendor bill, approval mail, booking.
  5. Eingangsrechnung: Posteingang   – checks the invoice mailbox every minute.
  6. Eingangsrechnung: Einstellungen – tolerance, addresses and signature as a form.

This file only wires the nodes together. The code of every Code node is in workflows/src/ (see js() in n8nlib.py).
"""
import json

from n8nlib import *  # noqa: F401,F403

# ---------------------------------------------------------------- 4. Eingangsrechnung: Prüfung
BODY = "$('Rechnung eingegangen').first().json.body"           # what workflow 5 handed over
INV = '$("Prüfungen").first().json.inv'                         # the invoice as read and checked
SUP_ID = '(($("Lieferant suchen").first().json.result||[])[0]||{id:0}).id'
BILL = '(($("Beleg lesen").first().json.result||[])[0]||{})'    # the bill Odoo's importer created
DONE = '$("Abschluss vorbereiten").first().json'                # what the click in the approval mail decided
DONE_X = "$('Abschluss vorbereiten').first().json"

W4 = [
    node("Rechnung eingegangen", "webhook", 2, {"httpMethod": "POST", "path": "eingangsrechnung", "responseMode": "responseNode", "options": {}},
         [0, 300], webhookId="eingangsrechnung"),
    read_file("Einstellungen lesen", [200, 300], SETTINGS),
    from_json("Einstellungen", [400, 300]),
    read_file("Stilregeln datei", [600, 300], STYLE_GUIDE),
    from_text("Stilregeln lesen", [800, 300]),
    node("Dokument holen", "httpRequest", 4.2,
         {"method": "GET", "url": f"={MAILPIT}/message/{{{{ {BODY}.mailpit_id }}}}/part/{{{{ {BODY}.part_id }}}}",
          "options": {"response": {"response": {"responseFormat": "file"}}}}, [1000, 300]),
    node("Dokument erkennen", "httpRequest", 4.2,
         {"method": "POST", "url": f"=http://docreader:8098/read?filename={{{{ encodeURIComponent({BODY}.filename || '') }}}}",
          "sendBody": True, "contentType": "binaryData", "inputDataFieldName": "data", "options": {"timeout": 300000}}, [1200, 300]),
    code("Kontext", [1400, 300], js("rechnung/context.js")),
    odoo_login("Odoo Login", [1600, 300]),
    odoo("KI aus Odoo lesen", [1800, 300], "ir.config_parameter", "search_read",
         '[[["key", "in", $("Kontext").first().json.settings.odoo_ai_params || []]]]', '{fields: ["key", "value"]}'),
    if_true("E-Rechnung?", [2000, 300], "={{ $('Kontext').first().json.doc.source === 'einvoice' }}"),

    # e-invoice: Odoo's own importer reads it (top row)
    code("Datei für Odoo", [2240, 80], "return [{ json: { b64: $('Dokument erkennen').first().json.b64 } }];"),
    odoo("Einkaufsjournal", [2440, 80], "account.journal", "search", '[[["type", "=", "purchase"]]]', '{limit: 1}'),
    odoo("In Odoo hochladen", [2640, 80], "ir.attachment", "create",
         '[{name: $("Rechnung eingegangen").first().json.body.filename || "e-rechnung", datas: $("Datei für Odoo").first().json.b64}]'),
    odoo("Odoo liest E-Rechnung", [2840, 80], "account.journal", "create_document_from_attachment",
         '[$("Einkaufsjournal").first().json.result, [$("In Odoo hochladen").first().json.result]]'),
    odoo("Beleg lesen", [3040, 80], "account.move", "read", '[[$("Odoo liest E-Rechnung").first().json.result.res_id]]',
         '{fields: ["partner_id", "ref", "invoice_date", "invoice_date_due", "amount_untaxed", "amount_tax", "amount_total", '
         '"partner_bank_id", "invoice_origin", "invoice_line_ids"]}'),
    odoo("Belegzeilen lesen", [3240, 80], "account.move.line", "read",
         '[(($("Beleg lesen").first().json.result||[])[0]||{invoice_line_ids:[]}).invoice_line_ids]',
         '{fields: ["product_id", "name", "quantity", "price_unit", "price_subtotal", "purchase_line_id", "display_type"]}'),
    odoo("Belegpartner lesen", [3440, 80], "res.partner", "read", f'[[({BILL}.partner_id||[0])[0]]]', '{fields: ["name", "vat", "create_date"]}'),
    odoo("Bankkonto lesen", [3640, 80], "res.partner.bank", "read", f'[[({BILL}.partner_bank_id||[0])[0]]]', '{fields: ["acc_number", "create_date"]}'),
    code("E-Rechnung übernehmen", [3840, 80], js("rechnung/einvoice.js")),

    # PDF or scan: the AI reads the text (bottom row)
    code("Lese-Anfrage", [2240, 520], js("shared/llm-request.js", "rechnung/read-request.js")),
    ai_http("KI liest Rechnung", [2440, 520]),
    code("KI-Antwort prüfen", [2640, 520], js("shared/ai-text.js", "rechnung/read-parse.js")),

    # fixed checks, then everything Odoo knows about this supplier
    code("Prüfungen", [4080, 300], js("rules/invoice-rules.js", "rechnung/checks.js")),
    odoo("Lieferant suchen", [4280, 300], "res.partner", "search_read",
         f'[{INV}.supplier_vat ? [["vat", "=", {INV}.supplier_vat]] : [["name", "ilike", {INV}.supplier_name || "###"], ["supplier_rank", ">", 0]]]',
         '{fields: ["name", "vat", "email", "phone"], limit: 1}'),
    odoo("Bankkonten lesen", [4480, 300], "res.partner.bank", "search_read", f'[[["partner_id", "=", {SUP_ID}]]]', '{fields: ["acc_number"]}'),
    odoo("Bestellungen suchen", [4680, 300], "purchase.order", "search_read",
         f'[[["partner_id", "=", {SUP_ID}], ["state", "in", ["purchase", "done"]]]]',
         '{fields: ["name", "partner_ref", "origin", "order_line", "invoice_status"]}'),
    odoo("Bestellpositionen lesen", [4880, 300], "purchase.order.line", "search_read",
         f'[[["order_id.partner_id", "=", {SUP_ID}], ["order_id.state", "in", ["purchase", "done"]]]]',
         '{fields: ["order_id", "name", "product_id", "product_qty", "qty_received", "qty_invoiced", "price_unit", "taxes_id"]}'),
    odoo("Dubletten prüfen", [5080, 300], "account.move", "search_read",
         f'[[["move_type", "=", "in_invoice"], ["partner_id", "=", {SUP_ID}], ["ref", "=", {INV}.invoice_number || "###"], '
         '["state", "!=", "cancel"], ["id", "!=", $("Prüfungen").first().json.importedBillId || 0]]]',
         '{fields: ["name", "state"]}'),
    code("Abgleich", [5280, 300], js("rules/invoice-rules.js", "rechnung/match.js")),
    if_true("Entwurf anlegen?", [5480, 300], "={{ !!$json.draft }}"),
    odoo_dyn("Rechnungsentwurf anlegen", [5680, 120], "$json.draft.model", "$json.draft.method", "$json.draft.args"),
    code("Rückfrage-Anfrage", [5880, 300], js("shared/llm-request.js", "rechnung/query-request.js")),
    node("Eingang bestätigen", "respondToWebhook", 1.1,
         {"respondWith": "json", "responseBody": "={{ JSON.stringify({ ok: true, decision: $json.decision }) }}", "options": {}}, [6080, 300]),
    if_true("Rückfrage schreiben?", [6280, 300], "={{ $json.wantQuery }}"),
    ai_http("KI schreibt Rückfrage", [6480, 120]),

    # the person decides
    code("Freigabe-Mail bauen", [6680, 300], js("shared/ai-text.js", "shared/mail-layout.js", "rechnung/approval-mail.js")),
    send_mail("Freigabe anfragen", [6880, 300], "={{ $json.settings.inv_mailbox }}", "={{ $json.settings.inv_approval_email }}",
              "={{ $json.approvalSubject }}", "={{ $json.approvalHtml }}", html=True),
    node("Auf Freigabe warten", "wait", 1.1, {"resume": "webhook", "options": {}}, [7080, 300], webhookId="rechnung-freigabe"),
    code("Abschluss vorbereiten", [7280, 300], js("rechnung/finalize.js")),
    if_true("Odoo-Aktion?", [7480, 300], "={{ !!$json.call }}"),
    odoo_dyn("In Odoo ausführen", [7680, 120], "$json.call.model", "$json.call.method", "$json.call.args"),
    if_true("Rückfrage senden?", [7880, 300], f"={{{{ {DONE_X}.sendQuery }}}}"),
    send_mail("Rückfrage an Lieferanten", [8080, 120], f"={{{{ {DONE_X}.settings.inv_mailbox }}}}", f"={{{{ {DONE_X}.supplier.email }}}}",
              f"={{{{ {DONE_X}.query.subject }}}}", f"={{{{ {DONE_X}.query.body }}}}"),
    if_true("Notiz möglich?", [8280, 300], f"={{{{ !!{DONE_X}.target }}}}"),
    odoo_dyn("Notiz in Odoo", [8480, 120], f"{DONE}.target.model", '"message_post"', f"[[{DONE}.target.id]]", f"{{body: {DONE}.note}}"),
    code("Protokollzeile", [8680, 300], js("rechnung/log-line.js")),
    append_log("Protokoll schreiben", [8880, 300]),
]
W4_LINKS = [
    *chain("Rechnung eingegangen", "Einstellungen lesen", "Einstellungen", "Stilregeln datei", "Stilregeln lesen", "Dokument holen",
           "Dokument erkennen", "Kontext", "Odoo Login", "KI aus Odoo lesen", "E-Rechnung?"),
    ("E-Rechnung?", "Datei für Odoo", 0), ("E-Rechnung?", "Lese-Anfrage", 1),
    *chain("Datei für Odoo", "Einkaufsjournal", "In Odoo hochladen", "Odoo liest E-Rechnung", "Beleg lesen", "Belegzeilen lesen",
           "Belegpartner lesen", "Bankkonto lesen", "E-Rechnung übernehmen", "Prüfungen"),
    *chain("Lese-Anfrage", "KI liest Rechnung", "KI-Antwort prüfen", "Prüfungen"),
    *chain("Prüfungen", "Lieferant suchen", "Bankkonten lesen", "Bestellungen suchen", "Bestellpositionen lesen", "Dubletten prüfen",
           "Abgleich", "Entwurf anlegen?"),
    ("Entwurf anlegen?", "Rechnungsentwurf anlegen", 0), ("Entwurf anlegen?", "Rückfrage-Anfrage", 1),
    *chain("Rechnungsentwurf anlegen", "Rückfrage-Anfrage", "Eingang bestätigen", "Rückfrage schreiben?"),
    ("Rückfrage schreiben?", "KI schreibt Rückfrage", 0), ("Rückfrage schreiben?", "Freigabe-Mail bauen", 1),
    *chain("KI schreibt Rückfrage", "Freigabe-Mail bauen", "Freigabe anfragen", "Auf Freigabe warten", "Abschluss vorbereiten", "Odoo-Aktion?"),
    ("Odoo-Aktion?", "In Odoo ausführen", 0), ("Odoo-Aktion?", "Rückfrage senden?", 1), ("In Odoo ausführen", "Rückfrage senden?"),
    ("Rückfrage senden?", "Rückfrage an Lieferanten", 0), ("Rückfrage senden?", "Notiz möglich?", 1), ("Rückfrage an Lieferanten", "Notiz möglich?"),
    ("Notiz möglich?", "Notiz in Odoo", 0), ("Notiz möglich?", "Protokollzeile", 1),
    *chain("Notiz in Odoo", "Protokollzeile", "Protokoll schreiben"),
]

# ---------------------------------------------------------------- 5. Eingangsrechnung: Posteingang
W5 = [
    every_minute("Jede Minute", [0, 300]),
    read_file("Einstellungen lesen", [200, 300], SETTINGS),
    from_json("Einstellungen", [400, 300]),
    http("Postfach abrufen", [600, 300], f"{MAILPIT}/messages?limit=50", method="GET"),
    code("Neue Rechnungen", [800, 300], js("rechnung/inbox-new.js")),
    http("E-Mail lesen", [1000, 300], f"={MAILPIT}/message/{{{{ $json.ID }}}}", method="GET"),
    code("PDF-Anhänge", [1200, 300], js("rechnung/attachments.js")),
    http("An Prüfung übergeben", [1400, 300], "http://localhost:5678/webhook/eingangsrechnung", "={{ JSON.stringify($json) }}"),
    mark_read("Als gelesen markieren", [1600, 300], "$('PDF-Anhänge').item.json.mailpit_id"),
]
W5_LINKS = chain("Jede Minute", "Einstellungen lesen", "Einstellungen", "Postfach abrufen", "Neue Rechnungen", "E-Mail lesen", "PDF-Anhänge",
                 "An Prüfung übergeben", "Als gelesen markieren")

# ---------------------------------------------------------------- 6. Eingangsrechnung: Einstellungen
W6, W6_LINKS = settings_flow(
    "Rechnungs-Einstellungen", "Eingangsrechnungen: Einstellungen",
    "Wie streng geprüft wird und wer freigibt. Jedes Feld zeigt den Wert, der gerade gilt; nur ändern, was sich ändern soll. "
    "Den KI-Anbieter wählen Sie im Einstellungsmenü der Reklamationen; er gilt für beide.",
    [
        heading("Prüfung", "Ab welcher Preisabweichung zur Bestellung die Rechnung gemeldet wird. "
                "Summen, USt-IdNr., IBAN, Dubletten und Bankverbindung werden immer geprüft."),
        now({"fieldLabel": "Preistoleranz (%)", "fieldType": "number"}, "inv_price_tolerance_pct"),
        heading("Postfächer und Freigabe"),
        now({"fieldLabel": "Freigabe an (E-Mail der Buchhaltung)", "fieldType": "email"}, "inv_approval_email"),
        now({"fieldLabel": "Rechnungs-Postfach", "fieldType": "email"}, "inv_mailbox"),
        heading("Rückfragen an Lieferanten"),
        now({"fieldLabel": "Signatur für Rückfragen", "fieldType": "textarea"}, "inv_signature", prefill=False),
    ],
    "rechnungen-einstellungen", "Die nächste Rechnung wird mit den neuen Einstellungen geprüft.",
    js("rechnung/settings-save.js"), ("Neue Einstellungen", "Speichern"))

OUT.mkdir(exist_ok=True)
for fname, f in [("4-eingangsrechnung.json", flow("Eingangsrechnung: Prüfung", W4, W4_LINKS, "rwRechnung004")),
                 ("5-rechnungseingang.json", flow("Eingangsrechnung: Posteingang", W5, W5_LINKS, "rwRechnEing005")),
                 ("6-rechnungen-einstellungen.json", flow("Eingangsrechnung: Einstellungen", W6, W6_LINKS, "rwRechnEinst006"))]:
    (OUT / fname).write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", fname, len(f["nodes"]), "nodes")
