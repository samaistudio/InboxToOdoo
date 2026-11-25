"""Captures the tutorial screens from a running demo and writes docs/tutorial.html and docs/assets/tut-*.png.
Needs: ./install.sh --demo has run and the approval mails have arrived; Google Chrome; Node 22+.
Run: python3 docs/make_tutorial.py            (all screens: desktop and phone)
     python3 docs/make_tutorial.py --phone    (only the phone screens; desktop screens and their marks stay)
     python3 docs/make_tutorial.py --text     (no capture: only the texts, from STEPS below)"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
for line in (ROOT / ".env.local").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k] = v

msgs = json.load(urllib.request.urlopen("http://localhost:8025/api/v1/messages?limit=200"))["messages"]


def mail(part):
    return next(m["ID"] for m in msgs if part in m["Subject"] and "Vorversion" not in (m.get("Tags") or []))


# JS snippets that return [x, y, w, h] for the parts each note explains
BTN = "(()=>{const as=[...document.querySelectorAll('.actions a')].map(a=>a.getBoundingClientRect());const L=Math.min(...as.map(a=>a.left)),R=Math.max(...as.map(a=>a.right)),B=Math.max(...as.map(a=>a.bottom));return [L,as[0].y,R-L,B-as[0].y]})()"
EL = "(()=>{{const r=document.querySelector({sel!r}).getBoundingClientRect();return [r.x,r.y,r.width,r.height]}})()".format
ROW = "(()=>{{const t=[...document.querySelectorAll('table.how td.k')].find(x=>x.textContent.trim()==={k!r});const r=t.parentElement.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}})()".format
# the subject column of the whole list
# (on a phone, sender and subject are stacked in each row, so the whole rows)
SUBJECTS = "(()=>{const r=[...document.querySelectorAll('.message')];let s=r.map(e=>e.children[1].getBoundingClientRect());if(s[0].x-r[0].getBoundingClientRect().x<40){const a=r[0].getBoundingClientRect(),b=r[r.length-1].getBoundingClientRect();return [a.x+6,a.y+6,a.width-12,b.bottom-a.y-12]}return [s[0].x-6,s[0].y-6,Math.max(...s.map(q=>q.width))+12,s[s.length-1].bottom-s[0].y+12]})()"
# every row of RE-2026-1219 (it arrives twice), one rect per row
# (desktop: up to the size column; on a phone the row has no such column, so the whole row)
DUP = "(()=>{const r=[...document.querySelectorAll('.message')];const sz=[...r[0].children].slice(-2)[0].getBoundingClientRect();return r.filter(e=>/RE-2026-1219/.test(e.textContent)).map(e=>{const a=e.getBoundingClientRect();const end=sz.x>a.x+100?sz.x:a.right;return [a.x,a.y,end-a.x,a.height]})})()"
# only the verdict word in each subject (Buchbar / Abweichung / Gestoppt), one rect per row; drawn 3px around the word (the page adds 8)
VERDICTS = "(()=>[...document.querySelectorAll('[data-testid=message-subject] b')].map(b=>{const t=b.firstChild,m=/Buchbar|Abweichung|Gestoppt/.exec(t.textContent);const g=document.createRange();g.setStart(t,m.index);g.setEnd(t,m.index+m[0].length);const q=g.getBoundingClientRect();return [q.x+5,q.y+3,q.width-10,q.height-6]}))()"
# the inbox list shows sender and subject only (the "To:" line under each sender is hidden)
HIDE_TO = "(()=>{for(const e of document.querySelectorAll('.message *'))if(e.children.length===0&&/^To:/.test(e.textContent.trim()))e.style.display='none';return 1})()"
# Mailpit list without its sidebar and without the size/date column
LIST_CLIP = "(()=>{const r=[...document.querySelectorAll('.message')];const a=r[0].getBoundingClientRect(),b=r[r.length-1].getBoundingClientRect();const sz=[...r[0].children].slice(-2)[0].getBoundingClientRect();return [a.x,a.y-8,sz.x-a.x,b.bottom-a.y+16]})()"
# the same list on a phone: every row, full width, without Mailpit's top bar
PHONE_LIST = "(()=>{const r=[...document.querySelectorAll('.message')];const a=r[0].getBoundingClientRect(),b=r[r.length-1].getBoundingClientRect();return [0,a.y-8,innerWidth,b.bottom-a.y+16]})()"
MP = "http://localhost:8025/search?q="
FIELD = "(()=>{{const ls=[...document.querySelectorAll('label')];const f=t=>ls.find(l=>l.textContent.includes(t));const ctrl=l=>(l.htmlFor&&document.getElementById(l.htmlFor))||l.parentElement.querySelector('select,input,textarea')||l;const a=f({a!r}).getBoundingClientRect(),c=ctrl(f({b!r})).getBoundingClientRect();return [Math.min(a.x,c.x)-8,a.y-6,Math.max(a.width,c.width)+16,c.bottom-a.y+12]}})()".format
STEPS = [
    dict(name="tut-1-inbox", phone=3000, pclip=PHONE_LIST, url=MP + "to%3Arechnungen%40", w=1500, h=900, wait=3000, clip=LIST_CLIP, pre=HIDE_TO,
         title="Invoices arrive in the mailbox",
         intro="Suppliers send invoices to the invoice mailbox: PDFs, e-invoices and one scanned paper invoice. Here it is a local test mailbox; in a company it is their normal Outlook or Gmail.",
         notes=[("Every new mail is picked up", "A small workflow checks the mailbox every minute and hands each attachment to the invoice check.", SUBJECTS),
                ("Two invoices arrive twice, on purpose", "The e-invoice RE-2026-1219 is sent again, and RE-2026-1187 comes back as a copy further down. One of each pair should be stopped as a duplicate; step 2 shows what this run did.", DUP)]),
    dict(name="tut-2-approvals", phone=3000, pclip=PHONE_LIST, pre=HIDE_TO, url=MP + "to%3Abuchhaltung%40rheinmark-handel.example%20!tag%3AVorversion", w=1500, h=900, wait=3000, clip=LIST_CLIP,
         title="Accounts gets one mail per invoice",
         intro="The subject already says the verdict, the supplier, the invoice number and the amount: “Buchbar” (ready to book), “Abweichung” (difference) or “Gestoppt” (stopped).",
         notes=[("Sorted at a glance", "Twelve invoice mails, three verdicts. Only the differences and the stops need a person to read further. This run checked the invoices in parallel, so three verdicts differ from the test table: the copy of RE-2026-1187 got Buchbar and the original Gestoppt, and LW-50288 found two open orders (see Limits).", VERDICTS)]),
    dict(name="tut-3-invoice", phone=3200, url=f"http://localhost:8025/view/{mail('Abweichung · Lichtwerk Elektro AG · LW-50231')}.html", w=760, h=1800,
         title="An invoice with a price difference",
         intro="This supplier charged more than agreed in the purchase order.",
         notes=[("The verdict and the reason", "One price is 7.2 % above the order. The tolerance is 2 %, so the invoice is flagged.", "(()=>{const u=document.querySelector('.checks').getBoundingClientRect();const p=document.querySelector('.verdict').getBoundingClientRect();return [p.x,p.y,Math.max(p.width,u.width),u.bottom-p.y]})()"),
                ("Order, receipt and invoice side by side", "Ordered, delivered, already billed and billed now, for every line. Only the cell that breaks a rule is marked.", EL(sel='table.data')),
                ("The expected next step is the filled button", "Send the drafted query to the supplier. Booking anyway and discarding are there too. Nothing happens before a click.", BTN)]),
    dict(name="tut-4-query", phone=3200, url=f"http://localhost:8025/view/{mail('Abweichung · Lichtwerk Elektro AG · LW-50231')}.html", w=760, h=1800,
         title="The query to the supplier is already written",
         intro="For a difference, the AI drafts a short, factual e-mail to the supplier: the numbers, what is wrong and what is needed.",
         notes=[("Drafted, not sent", "It goes out only after the click on “Rückfrage an Lieferanten senden”. The invoice stays a draft in Odoo until the correction arrives.", EL(sel='pre')),
                ("How it was decided", "Tolerance, fixed checks, how the document was read and which AI was used. The AI runs locally here, so no data leaves the machine.", EL(sel='table.how'))]),
    dict(name="tut-5-fraud", phone=3200, url=f"http://localhost:8025/view/{mail('Gestoppt · Werkzeugtechnik Nord GmbH · RE-2026-1203')}.html", w=760, h=1400,
         title="A changed bank account stops everything",
         intro="The invoice asks for payment to a new bank account. That is one of the most common invoice frauds, so this invoice is not even drafted.",
         notes=[("Compared with Odoo, not with the e-mail", "The account on the invoice is shown above the one stored in Odoo, in groups of four. The advice is to call a number already known, never to reply.", "(()=>{const u=document.querySelector('ul.checks').getBoundingClientRect();const b=document.querySelector('.iban').getBoundingClientRect();return [Math.min(u.x,b.x),u.y,Math.max(u.right,b.right)-Math.min(u.x,b.x),b.bottom-u.y]})()"),
                ("No booking button", "Only “Als erledigt markieren”. A stopped invoice cannot be booked from here by mistake.", BTN)]),
    dict(name="tut-6-einvoice", phone=3200, url=f"http://localhost:8025/view/{mail('Buchbar · Werkzeugtechnik Nord GmbH · RE-2026-1219')}.html", w=760, h=1400,
         title="E-invoices are read by Odoo itself",
         intro="XRechnung and ZUGFeRD invoices carry their data inside. Odoo Community reads them, so no AI is needed; the automation adds the checks around it.",
         notes=[("Everything matches", "Order, goods receipt and invoice agree; sums, VAT ID and IBAN were checked. Booking is the filled button.", EL(sel='.checks')),
                ("How it was read", "“E-Rechnung (XRechnung UBL), von Odoo selbst eingelesen, ohne KI”. PDFs are read by the AI, paper scans by OCR first.", ROW(k='Gelesen'))]),
    dict(name="tut-7-odoo", phone=1560, url="http://localhost:8069/odoo/action-account.action_move_in_invoice_type/15", w=1120, h=880, wait=9000, login=True,
         title="The draft bill in Odoo",
         intro="The invoice from step 3 (LW-50231) as a draft vendor bill in Odoo; it stays a draft while the query to the supplier is open. Odoo's interface runs in English here; the company data is German.",
         notes=[("Linked to the purchase order", "The bill points to order P00002, so Odoo's own reports see what was ordered, received and billed.", EL(sel='.oe_stat_button'), "desktop"),
                ("The lines as invoiced", "The 20.90 price stays as the supplier billed it. The bill stays a draft while the query to the supplier is open.", EL(sel='.o_field_widget[name=invoice_line_ids]')),
                ("Written by the automation", "A note on every bill says which file and which mail it came from.", EL(sel='[name=narration]'))]),
    dict(name="tut-8-complaint", phone=3200, url=f"http://localhost:8025/view/{mail('Gutschrift · Anna Schulz')}.html", w=760, h=2000,
         title="A complaint, decided by rule",
         intro="A customer writes that the display was cracked on arrival and wants her money back.",
         notes=[("The facts from Odoo", "Order, product, delivery date, warranty, amount with VAT. The AI only read the e-mail; these values come from Odoo.", EL(sel='table.kv:not(.how)')),
                ("Her own words", "The original e-mail is shown, so the person who approves can check what the AI understood.", "(()=>{const r=document.querySelectorAll('pre')[0].getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()"),
                ("The reply, ready to send", "A credit note of 141.61 € is prepared in Odoo and the reply is written in the company's tone.", "(()=>{const r=document.querySelectorAll('pre')[1].getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()"),
                ("Approve or reject", "Approve books the credit note and sends the reply. Reject cancels the draft and sends nothing.", BTN)]),
    dict(name="tut-9-settings", phone=2790, url="http://localhost:5678/form/einstellungen", w=900, h=2700, wait=3000,
         pre="setTimeout(()=>document.querySelector('#submit-btn').click(),50),1",
         title="The company sets the rules",
         intro="A plain form, no code: how replies are written, how complaints are decided and which AI is used. Every field shows the value in use; a choice marked “(aktuell)” keeps it.",
         notes=[("How replies sound", "Language, Sie or du, tone, length, when to apologise, closing and signature.", FIELD(a='Sprache', b='Signatur')),
                ("Which AI", "A local model, a cloud provider, or the AI key already set up in Odoo. The form says where the data goes. Keys stay in a local file, never in this form.", FIELD(a='KI-Anbieter', b='KI-Adresse'))]),
]

MODE = sys.argv[1] if len(sys.argv) > 1 else ""
KEYS = ("name", "url", "w", "h", "wait", "login", "clip", "pre")
old = {s["img"]: s for s in json.loads((ASSETS / "tutorial.json").read_text(encoding="utf-8"))} if MODE else {}


def geometry(m):
    return {"w": m["w"], "h": m["h"], "notes": [{"r": [round(v) for v in r]} | ({"parts": [[round(v) for v in q] for q in p]} if p else {})
                                                 for r, p in zip(m["rects"], m["parts"])]}


def capture(spec):
    out = subprocess.run(["node", str(ROOT / "docs" / "capture.mjs"), str(ASSETS)], input=json.dumps(spec), capture_output=True, text=True, env=env, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


# desktop screens (skipped with --phone / --text: then the marks come from the last tutorial.json)
desk = {} if MODE else capture([{k: v for k, v in s.items() if k in KEYS} | {"rects": [n[2] for n in s["notes"]]} for s in STEPS])
# phone screens: the same page at 390 px, same notes; the page shows a cut-out per note on phones
phone = {} if MODE == "--text" else capture([{k: v for k, v in s.items() if k in KEYS} | {"name": s["name"] + "-m", "w": 390, "h": s["phone"], "rects": [n[2] for n in s["notes"]]}
                                                | ({"clip": s["pclip"]} if "pclip" in s else {})
                                                for s in STEPS if s.get("phone")])
# steps 3 and 4 show the same mail: keep one phone file
seen = {}
for s in STEPS:
    if s.get("phone") and s["name"] + "-m" in phone:
        f = ASSETS / f"{s['name']}-m.png"
        if s["url"] in seen and f.read_bytes() == (ASSETS / f"{seen[s['url']]}-m.png").read_bytes():
            f.unlink()
            phone[s["name"] + "-m"]["file"] = seen[s["url"]] + "-m.png"
        seen.setdefault(s["url"], s["name"])

steps = []
for s in STEPS:
    img = f"assets/{s['name']}.png"
    g = geometry(desk[s["name"]]) if s["name"] in desk else {"w": old[img]["w"], "h": old[img]["h"], "notes": [{k: v for k, v in n.items() if k in ("r", "parts")} for n in old[img]["notes"]]}
    step = {"title": s["title"], "intro": s["intro"], "img": img, "w": g["w"], "h": g["h"],
            "notes": [{"t": n[0], "d": n[1]} | gn for n, gn in zip(s["notes"], g["notes"])]}
    pm = phone.get(s["name"] + "-m")
    if pm:
        step["m"] = {"img": "assets/" + pm.get("file", s["name"] + "-m.png")} | geometry(pm)
    elif s.get("phone") and img in old and "m" in old[img]:
        step["m"] = old[img]["m"]
    if "m" in step:
        # a note marked "desktop" is cut from the desktop screen on phones (the phone layout hides that part)
        step["m"]["notes"] = [None if len(n) > 3 and n[3] == "desktop" else gn for n, gn in zip(s["notes"], step["m"]["notes"])]
    steps.append(step)
html = (ROOT / "docs" / "tutorial.template.html").read_text(encoding="utf-8").replace("/*STEPS*/[]", json.dumps(steps, ensure_ascii=False, indent=1))
(ROOT / "docs" / "tutorial.html").write_text(html, encoding="utf-8")
(ROOT / "docs" / "assets" / "tutorial.json").write_text(json.dumps(steps, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote tutorial.html with", len(steps), "steps")
