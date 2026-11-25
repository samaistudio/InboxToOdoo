"""Builds the complaint workflows in workflows/. Run: python3 build_workflows.py

  1. Reklamation: Assistent      – webhook in, AI reads the mail, Odoo lookup, fixed rules, draft in Odoo,
                                   AI writes the reply, style check, approval mail, wait, book + send.
  2. Reklamation: Posteingang    – checks the service mailbox (Mailpit) every minute and hands new complaints to workflow 1.
  3. Reklamation: Einstellungen  – a form (the settings menu) that writes data/settings.json.

This file only wires the nodes together. The code of every Code node is in workflows/src/ (see js() in n8nlib.py).
"""
import json

from n8nlib import *  # noqa: F401,F403

# ---------------------------------------------------------------- 1. Reklamation: Assistent
DONE = '$("Abschluss vorbereiten").first().json'                # what the click in the approval mail decided
DONE_X = "$('Abschluss vorbereiten').first().json"

W1 = [
    node("Reklamation eingegangen", "webhook", 2, {"httpMethod": "POST", "path": "reklamation", "responseMode": "onReceived", "options": {}},
         [0, 300], webhookId="reklamation"),
    read_file("Einstellungen lesen", [220, 300], SETTINGS),
    from_json("Einstellungen", [440, 300]),
    read_file("Stilregeln datei", [660, 300], STYLE_GUIDE),
    from_text("Stilregeln lesen", [880, 300]),
    code("Kontext", [1100, 300], js("reklamation/context.js")),
    odoo_login("Odoo Login", [1320, 300]),
    odoo("KI aus Odoo lesen", [1430, 480], "ir.config_parameter", "search_read",
         '[[["key", "in", $("Kontext").first().json.settings.odoo_ai_params || []]]]', '{fields: ["key", "value"]}'),

    # the AI reads the complaint; everything else comes from Odoo
    code("Lese-Anfrage", [1540, 300], js("shared/llm-request.js", "reklamation/read-request.js")),
    ai_http("KI liest E-Mail", [1650, 480]),
    code("KI-Antwort prüfen", [1760, 300], js("shared/ai-text.js", "reklamation/read-parse.js")),
    odoo("Auftrag suchen", [1980, 300], "sale.order", "search_read", '[$("KI-Antwort prüfen").first().json.orderDomain]',
         '{fields: ["name","client_order_ref","partner_id","date_order","order_line","picking_ids","invoice_ids","amount_total"], '
         'limit: 1, order: "date_order desc"}'),
    odoo("Positionen lesen", [2200, 300], "sale.order.line", "read",
         '[(($("Auftrag suchen").first().json.result||[])[0]||{order_line:[]}).order_line]',
         '{fields: ["name","product_id","product_uom_qty","price_unit","price_total","tax_id"]}'),
    odoo("Lieferung lesen", [2420, 300], "stock.picking", "read",
         '[(($("Auftrag suchen").first().json.result||[])[0]||{picking_ids:[]}).picking_ids]', '{fields: ["name","date_done","state"]}'),
    odoo("Kunde lesen", [2640, 300], "res.partner", "read",
         '[[(($("Auftrag suchen").first().json.result||[])[0]||{partner_id:[0]}).partner_id[0]]]', '{fields: ["name","email","is_company","lang"]}'),

    # fixed rules decide, the draft goes into Odoo, the AI writes the reply, code checks its style
    code("Entscheidung", [2860, 300], js("rules/complaint-rules.js", "reklamation/decide.js")),
    if_true("Entwurf nötig?", [3080, 300], "={{ !!$json.draft }}", cid="d1"),
    odoo_dyn("Entwurf in Odoo anlegen", [3300, 200], "$json.draft.model", '"create"', "[$json.draft.values]", kwargs=None),
    code("Antwort-Anfrage", [3520, 300], js("shared/llm-request.js", "reklamation/reply-request.js")),
    ai_http("KI schreibt Antwort", [3740, 300]),
    code("Stilprüfung", [3960, 300], js("shared/ai-text.js", "rules/reply-style.js", "reklamation/style-check.js")),
    node("Stil ok?", "if", 2.2, {"conditions": {"options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
         "conditions": [{"id": "s1", "leftValue": "={{ $json.problems.length }}", "rightValue": 0, "operator": {"type": "number", "operation": "equals"}}],
         "combinator": "and"}, "options": {}}, [4180, 300]),
    code("Korrektur-Anfrage", [4400, 420], js("shared/llm-request.js", "reklamation/fix-request.js")),
    ai_http("Stil korrigieren", [4620, 420]),

    # the person decides
    code("Freigabe-Mail bauen", [4840, 300], js("shared/ai-text.js", "shared/mail-layout.js", "reklamation/approval-mail.js")),
    send_mail("Freigabe anfragen", [5060, 300], "={{ $json.settings.service_email }}", "={{ $json.settings.approval_email }}",
              "={{ $json.approvalSubject }}", "={{ $json.approvalHtml }}", html=True),
    node("Auf Freigabe warten", "wait", 1.1, {"resume": "webhook", "options": {}}, [5280, 300], webhookId="freigabe"),
    code("Abschluss vorbereiten", [5500, 300], js("reklamation/finalize.js")),
    if_true("Odoo-Aktion?", [5720, 300], "={{ !!$json.call }}", cid="o1"),
    odoo_dyn("In Odoo buchen", [5940, 200], "$json.call.model", "$json.call.method", "$json.call.args", kwargs=None),
    if_true("Freigegeben?", [6160, 300], f"={{{{ {DONE_X}.approved }}}}", cid="a1"),
    send_mail("Antwort an Kunden", [6380, 200], f"={{{{ {DONE_X}.settings.service_email }}}}", f"={{{{ {DONE_X}.facts.customer_email }}}}",
              f"={{{{ {DONE_X}.subject }}}}", f"={{{{ {DONE_X}.body }}}}"),
    odoo("Notiz im Auftrag", [6600, 300], "sale.order", "message_post", f"[[({DONE}.order||{{id:0}}).id]]", f"{{body: {DONE}.note}}"),
    code("Protokollzeile", [6820, 300], js("reklamation/log-line.js")),
    append_log("Protokoll schreiben", [7040, 300]),
]
W1_LINKS = [
    *chain("Reklamation eingegangen", "Einstellungen lesen", "Einstellungen", "Stilregeln datei", "Stilregeln lesen", "Kontext", "Odoo Login",
           "KI aus Odoo lesen", "Lese-Anfrage", "KI liest E-Mail", "KI-Antwort prüfen", "Auftrag suchen", "Positionen lesen", "Lieferung lesen",
           "Kunde lesen", "Entscheidung", "Entwurf nötig?"),
    ("Entwurf nötig?", "Entwurf in Odoo anlegen", 0), ("Entwurf nötig?", "Antwort-Anfrage", 1),
    *chain("Entwurf in Odoo anlegen", "Antwort-Anfrage", "KI schreibt Antwort", "Stilprüfung", "Stil ok?"),
    ("Stil ok?", "Freigabe-Mail bauen", 0), ("Stil ok?", "Korrektur-Anfrage", 1),
    *chain("Korrektur-Anfrage", "Stil korrigieren", "Freigabe-Mail bauen", "Freigabe anfragen", "Auf Freigabe warten", "Abschluss vorbereiten",
           "Odoo-Aktion?"),
    ("Odoo-Aktion?", "In Odoo buchen", 0), ("Odoo-Aktion?", "Freigegeben?", 1), ("In Odoo buchen", "Freigegeben?"),
    ("Freigegeben?", "Antwort an Kunden", 0), ("Freigegeben?", "Notiz im Auftrag", 1),
    *chain("Antwort an Kunden", "Notiz im Auftrag", "Protokollzeile", "Protokoll schreiben"),
]

# ---------------------------------------------------------------- 2. Reklamation: Posteingang
W2 = [
    every_minute("Jede Minute", [0, 300]),
    read_file("Einstellungen lesen", [220, 300], SETTINGS),
    from_json("Einstellungen", [440, 300]),
    http("Postfach abrufen", [660, 300], f"{MAILPIT}/messages?limit=50", method="GET"),
    code("Neue Reklamationen", [880, 300], js("reklamation/inbox-new.js")),
    http("E-Mail lesen", [1100, 300], f"={MAILPIT}/message/{{{{ $json.ID }}}}", method="GET"),
    http("An Reklamation übergeben", [1320, 300], "http://localhost:5678/webhook/reklamation",
         "={{ JSON.stringify({message_id: $json.MessageID, from_email: $json.From.Address, from_name: $json.From.Name, "
         "subject: $json.Subject, text: $json.Text}) }}"),
    mark_read("Als gelesen markieren", [1540, 300], "$('E-Mail lesen').item.json.ID"),
]
W2_LINKS = chain("Jede Minute", "Einstellungen lesen", "Einstellungen", "Postfach abrufen", "Neue Reklamationen", "E-Mail lesen",
                 "An Reklamation übergeben", "Als gelesen markieren")

# ---------------------------------------------------------------- 3. Reklamation: Einstellungen (settings menu as a form)
# stored value -> label in the form (the save step maps the labels back, see workflows/src/reklamation/settings-save.js)
LANG = {"auto": "Sprache des Kunden übernehmen", "de": "Immer Deutsch", "en-US": "Immer Englisch (US)"}
FORMAL = {"Sie": "Sie", "du": "du", "auto": "Wie der Kunde"}
LENGTH = {"short": "kurz", "normal": "normal", "detailed": "ausführlich"}
APOLOGY = {"when_our_fault": "Nur wenn wir schuld sind", "always": "Immer", "never": "Nie"}
REMEDY = {"replacement": "Ersatzlieferung", "credit": "Gutschrift"}
PROVIDER = {"mock": "Testmodell (offline)", "odoo": "Wie in Odoo eingerichtet", "ollama": "Ollama (lokal)", "lmstudio": "LM Studio (lokal)",
            "openai": "OpenAI", "anthropic": "Anthropic Claude", "gemini": "Google Gemini", "mistral": "Mistral", "azure": "Azure OpenAI",
            "custom": "Eigener Endpunkt"}
W3, W3_LINKS = settings_flow(
    "Einstellungsmenü", "Reklamationen: Einstellungen",
    "So schreibt und entscheidet der Assistent für Reklamationen. Jedes Feld zeigt den Wert, der gerade gilt; nur ändern, was sich ändern soll.",
    [
        heading("Antwortstil", "Wie die Antwort an den Kunden klingt."),
        keep_dd("Sprache der Antwort", list(LANG.values()), "language", LANG),
        keep_dd("Anrede", list(FORMAL.values()), "formality", FORMAL),
        keep_dd("Ton", ["sachlich", "freundlich", "herzlich"], "tone"),
        keep_dd("Länge", list(LENGTH.values()), "length", LENGTH),
        keep_dd("Entschuldigung", list(APOLOGY.values()), "apology", APOLOGY),
        now({"fieldLabel": "Grußformel Deutsch"}, "closing_de"),
        now({"fieldLabel": "Grußformel Englisch"}, "closing_en"),
        now({"fieldLabel": "Signatur", "fieldType": "textarea"}, "signature", prefill=False),
        now({"fieldLabel": "Eigene Regeln", "fieldType": "textarea"}, "custom_rules", "keine", prefill=False, hint="leer = keine eigenen Regeln"),
        heading("Entscheidungen", "Welche Lösung der Assistent vorschlägt. Die Regeln selbst stehen fest im Ablauf."),
        keep_dd("Standardlösung bei Defekt", list(REMEDY.values()), "default_remedy", REMEDY),
        now({"fieldLabel": "Gewährleistung Privatkunden (Monate)", "fieldType": "number"}, "warranty_months_b2c"),
        now({"fieldLabel": "Gewährleistung Firmenkunden (Monate)", "fieldType": "number"}, "warranty_months_b2b"),
        heading("KI", "Testmodell, Ollama und LM Studio laufen auf diesem Rechner: keine Daten gehen nach außen. "
                "Bei einem Cloud-Anbieter gehen der Text der Reklamation und die Rechnungsdaten an diesen Anbieter. "
                "API-Schlüssel stehen nicht in diesem Formular, sondern in der Datei .env.local auf dem Server. "
                "Modell und Adresse leer lassen: es bleibt der bisherige Wert, bei einem neuen Anbieter dessen Standard."),
        keep_dd("KI-Anbieter", list(PROVIDER.values()), "llm_provider", PROVIDER),
        now({"fieldLabel": "KI-Modell"}, "llm_model", "Standard", prefill=False),
        now({"fieldLabel": "KI-Adresse (nur Azure, eigener Endpunkt oder entfernter Ollama)"}, "llm_url", "keine", prefill=False),
        heading("Freigabe", "Wer die Freigabe-Mails bekommt."),
        now({"fieldLabel": "Freigabe an (E-Mail)", "fieldType": "email"}, "approval_email"),
    ],
    "einstellungen", "Die nächste Reklamation nutzt die neuen Einstellungen.",
    js("reklamation/settings-save.js"), ("Neue Einstellungen", "Speichern"))

OUT.mkdir(exist_ok=True)
for fname, f in [("1-reklamation.json", flow("Reklamation: Assistent", W1, W1_LINKS, "rwReklamation001")),
                 ("2-posteingang.json", flow("Reklamation: Posteingang", W2, W2_LINKS, "rwPosteingang002")),
                 ("3-einstellungen.json", flow("Reklamation: Einstellungen", W3, W3_LINKS, "rwEinstellung003"))]:
    (OUT / fname).write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", fname, len(f["nodes"]), "nodes")
