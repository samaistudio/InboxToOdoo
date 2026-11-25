"""Shared building blocks for the n8n workflow builders: node helpers, Odoo calls, the settings forms, and js(),
which reads the code of the Code nodes from workflows/src/."""
import json
import uuid
from pathlib import Path

OUT = Path(__file__).parent / "workflows"
SMTP = {"smtp": {"id": "smtp-mailpit", "name": "Mailpit SMTP"}}
SETTINGS = "/files/data/settings.json"     # the company settings, written by the settings forms
STYLE_GUIDE = "/files/prompts/EMAIL_STYLE.md"
MAILPIT = "http://mailpit:8025/api/v1"


def _safe(v):
    """n8n ends an expression at the first '}}', so nested object literals need '} }'."""
    if isinstance(v, str) and v.startswith("={{") and v.endswith("}}"):
        inner = v[3:-2]
        while "}}" in inner:
            inner = inner.replace("}}", "} }")
        return "={{" + inner + "}}"
    if isinstance(v, dict):
        return {k: _safe(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_safe(x) for x in v]
    return v


def node(name, type_, ver, params, pos, **extra):
    params = _safe(params)
    return {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, name)), "name": name, "type": f"n8n-nodes-base.{type_}",
            "typeVersion": ver, "position": pos, "parameters": params, **extra}


def flow(name, nodes, links, wid):
    con = {}
    for a, b, *out in links:
        idx = out[0] if out else 0
        con.setdefault(a, {"main": []})
        while len(con[a]["main"]) <= idx:
            con[a]["main"].append([])
        con[a]["main"][idx].append({"node": b, "type": "main", "index": 0})
    return {"id": wid, "name": name, "nodes": nodes, "connections": con, "active": False,
            "settings": {"executionOrder": "v1", "saveManualExecutions": True}, "pinData": {}}


def http(name, pos, url, body=None, method="POST"):
    p = {"method": method, "url": url, "options": {"timeout": 120000}}
    if body is not None:
        p.update({"sendBody": True, "specifyBody": "json", "jsonBody": body})
    return node(name, "httpRequest", 4.2, p, pos)


def ai_http(name, pos):
    return node(name, "httpRequest", 4.2, {"method": "POST", "url": "={{ $json.llm.url }}", "sendHeaders": True, "specifyHeaders": "json",
                "jsonHeaders": "={{ JSON.stringify($json.llm.headers) }}", "sendBody": True, "specifyBody": "json",
                "jsonBody": "={{ JSON.stringify($json.llm.body) }}", "options": {"timeout": 180000}}, pos)


def code(name, pos, js):
    return node(name, "code", 2, {"jsCode": js.strip()}, pos)


def read_file(name, pos, path):
    return node(name, "readWriteFile", 1, {"operation": "read", "fileSelector": path, "options": {}}, pos)


def from_json(name, pos):
    return node(name, "extractFromFile", 1, {"operation": "fromJson", "options": {}}, pos)


def from_text(name, pos):
    return node(name, "extractFromFile", 1, {"operation": "text", "options": {}}, pos)


def append_log(name, pos):
    return node(name, "readWriteFile", 1, {"operation": "write", "fileName": "/files/data/log.jsonl", "options": {"append": True}}, pos)


def every_minute(name, pos):
    return node(name, "scheduleTrigger", 1.2, {"rule": {"interval": [{"field": "minutes", "minutesInterval": 1}]}}, pos)


def if_true(name, pos, expr, cid=None):
    """IF node: output 0 when the expression is true, output 1 otherwise."""
    cond = {"id": cid or name, "leftValue": expr, "rightValue": True,
            "operator": {"type": "boolean", "operation": "true", "singleValue": True}}
    return node(name, "if", 2.2, {"conditions": {"options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
                                               "conditions": [cond], "combinator": "and"}, "options": {}}, pos)


def send_mail(name, pos, from_, to, subject, body, html=False):
    """Mail through the local SMTP credential; all values are n8n expressions."""
    p = {"fromEmail": from_, "toEmail": to, "subject": subject, "emailFormat": "html" if html else "text",
         ("html" if html else "text"): body, "options": {"appendAttribution": False}}
    return node(name, "emailSend", 2.1, p, pos, credentials=SMTP)


def mark_read(name, pos, id_expr):
    """Marks a Mailpit message as read (the inbox pollers use the read flag as their state)."""
    return node(name, "httpRequest", 4.2, {"method": "PUT", "url": "http://mailpit:8025/api/v1/messages", "sendBody": True, "specifyBody": "json",
                                           "jsonBody": "={{ JSON.stringify({IDs: [" + id_expr + "], Read: true}) }}", "options": {}}, pos)


def chain(*names):
    """Links for nodes that follow each other: chain("A", "B", "C") -> [("A", "B"), ("B", "C")]."""
    return list(zip(names, names[1:]))


# Odoo's JSON-RPC endpoint as n8n reaches it: ODOO_URL from .env.local (the compose stack: http://odoo:8069)
ODOO = "={{ ($env.ODOO_URL || 'http://odoo:8069').replace(/\\/+$/, '') + '/jsonrpc' }}"


def odoo_dyn(name, pos, model, method, args, kwargs="{}"):
    """HTTP node for an Odoo execute_kw call; model, method, args and kwargs are JS expressions (kwargs=None: none)."""
    tail = f", {kwargs}" if kwargs is not None else ""
    body = ('={{ JSON.stringify({jsonrpc: "2.0", method: "call", params: {service: "object", method: "execute_kw", '
            f'args: [$env.ODOO_DB, $("Odoo Login").first().json.result, $env.ODOO_PASSWORD, {model}, {method}, {args}{tail}]}}}}) }}}}')
    return http(name, pos, ODOO, body)


def odoo(name, pos, model, method, args, kwargs="{}"):
    """HTTP node for an Odoo execute_kw call on a fixed model and method; args and kwargs are JS expressions."""
    return odoo_dyn(name, pos, f'"{model}"', f'"{method}"', args, kwargs)


def odoo_login(name, pos):
    body = ('={{ JSON.stringify({jsonrpc: "2.0", method: "call", params: {service: "common", method: "login", '
            'args: [$env.ODOO_DB, $env.ODOO_USER, $env.ODOO_PASSWORD]}}) }}')
    return http(name, pos, ODOO, body)


# ---------------------------------------------------------------- JavaScript of the Code nodes
# The logic of every Code node lives in workflows/src/*.js. The builders only wire nodes together;
# js() reads the files and joins them (shared helpers first) into the code of one node.
SRC = Path(__file__).parent / "workflows" / "src"


def js(*parts):
    """Code for one n8n Code node: the files in workflows/src joined in order. A part that marks the
    end of its node code with '// --- end of node code' keeps only what is above that line (the rest
    exports the functions for the unit tests in test/rules.test.mjs)."""
    out = []
    for p in parts:
        text = (SRC / p).read_text(encoding="utf-8")
        out.append(text.split("// --- end of node code")[0].strip())
    return "\n\n".join(out)


FORM_CSS = (SRC / "shared" / "form.css").read_text(encoding="utf-8")  # the look of the settings forms


KEEP = "Unverändert lassen"


def keep_dd(label, options, key=None, labels=None):
    """Settings dropdown whose first option keeps the stored value: the form shows it as "<value> (aktuell)", and the
    save step finds no mapping for that text, so the old value stays. key/labels: which setting it shows and how a
    stored value reads (see shared/settings-form.js)."""
    d = {"fieldLabel": label, "fieldType": "dropdown", "fieldOptions": {"values": [{"option": o} for o in [KEEP, *options]]},
         "requiredField": False, "defaultValue": KEEP}
    return {**d, "key": key, "labels": labels or {}} if key else d


def now(field, key, empty="", prefill=True, hint=None):
    """A settings field tied to a stored setting. By default it is filled with the value in use; with prefill=False it
    stays empty (empty = keep) and its placeholder says what is in use (see shared/settings-form.js)."""
    return {**field, "key": key, "empty": empty, "prefill": prefill, **({"hint": hint} if hint else {})}


# Builds the fields of settings page 2 from the stored settings (see workflows/src/shared/settings-form.js).
SETTINGS_FORM_JS = js("shared/settings-form.js")


def settings_flow(form, title, intro, fields, hook, done, save_js, save_node_names):
    """Settings as a two-page n8n form. An n8n form cannot read a file while its first page is built, so page 1 only
    loads the stored settings; page 2 shows every field with the value in use; the save step writes settings.json.
    Returns (nodes, links)."""
    page = f"{form} ändern"
    nodes = [
        node(form, "formTrigger", 2.2, {"formTitle": title, "formDescription": "Lädt die Werte, die gerade gelten.",
             "formFields": {"values": []}, "responseMode": "onReceived",
             "options": {"buttonLabel": "Aktuelle Einstellungen laden", "appendAttribution": False, "customCss": FORM_CSS}},
             [0, 300], webhookId=hook),
        read_file("Einstellungen lesen", [220, 300], SETTINGS),
        from_json("Einstellungen", [440, 300]),
        code("Formular vorbereiten", [660, 300], SETTINGS_FORM_JS.replace("/*FIELDS*/[]", json.dumps(fields, ensure_ascii=False))),
        node(page, "form", 1, {"operation": "page", "defineForm": "json", "jsonOutput": "={{ JSON.stringify($json.fields) }}",
             "options": {"formTitle": title, "formDescription": intro, "buttonLabel": "Speichern", "customCss": FORM_CSS}},
             [880, 300], webhookId=hook + "-seite"),
        code(save_node_names[0], [1100, 300], save_js.replace("/*FORM*/", page)),
        node(save_node_names[1], "readWriteFile", 1, {"operation": "write", "fileName": SETTINGS, "options": {}}, [1320, 300]),
        node(f"{form} gespeichert", "form", 1, {"operation": "completion", "respondWith": "text", "completionTitle": "Gespeichert",
             "completionMessage": done, "options": {"customCss": FORM_CSS}}, [1540, 300], webhookId=hook + "-fertig"),
    ]
    return nodes, chain(form, "Einstellungen lesen", "Einstellungen", "Formular vorbereiten", page, *save_node_names, f"{form} gespeichert")


def heading(title, text=""):
    """A small section heading inside an n8n form (static HTML, not a field that is saved)."""
    return {"fieldLabel": f"Abschnitt {title}", "fieldType": "html",
            "html": f"<h3>{title}</h3>" + (f"<p>{text}</p>" if text else "")}


