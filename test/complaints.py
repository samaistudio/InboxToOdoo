"""Eight fictional complaint e-mails, sent to the local Mailpit inbox (service@rheinmark-handel.example).
Run: python3 test/complaints.py [case ...]   (no argument = all)"""
import smtplib
import time
import sys
from email.message import EmailMessage

CASES = {
 "test-01": ("Thomas Becker", "einkauf@becker-haustechnik.example", "Reklamation Akkuschrauber Bestellung RW-2026-0412",
  "Guten Tag,\n\nvon den vier Akku-Bohrschraubern BS-18 aus unserer Bestellung RW-2026-0412 lädt einer nicht mehr. "
  "Der Akku zeigt nach dem Laden keine Anzeige, mit einem anderen Akku geht das Gerät. Wir brauchen das Gerät auf der Baustelle, "
  "bitte schicken Sie uns schnell Ersatz.\n\nMit freundlichen Grüßen\nThomas Becker\nBecker Haustechnik GmbH"),
 "test-02": ("Anna Schulz", "anna.schulz@privat.example", "Laser-Entfernungsmesser kaputt angekommen",
  "Hallo,\n\nich habe den Laser-Entfernungsmesser LM-50 bestellt (Bestellnummer RW-2026-0431). Das Display war schon beim Auspacken gesprungen. "
  "Ich möchte das Gerät nicht noch einmal, sondern bitte mein Geld zurück.\n\nViele Grüße\nAnna Schulz"),
 "test-03": ("Murat Yilmaz", "info@elektro-yilmaz.example", "Falsche Ware RW-2026-0388",
  "Sehr geehrte Damen und Herren,\n\nin der Lieferung zu RW-2026-0388 war statt dem Werkzeugkoffer Pro ein kleiner Kunststoffkoffer ohne Einsätze. "
  "Den Koffer haben wir so nicht bestellt. Bitte liefern Sie den richtigen Koffer nach.\n\nFreundliche Grüße\nMurat Yilmaz\nElektro Yilmaz KG"),
 "test-04": ("Jonas Weber", "jonas.weber@privat.example", "Bohrschrauber defekt",
  "Hallo,\n\nmein Akku-Bohrschrauber BS-18 (Bestellung RW-2023-0117) geht seit gestern nicht mehr an. "
  "Können Sie ihn reparieren oder ersetzen?\n\nGruß\nJonas Weber"),
 "test-05": ("Sarah Miller", "sarah.miller@privat.example", "Flickering work light, order RW-2026-0447",
  "Hi,\n\none of the two LED-30 work lights from order RW-2026-0447 keeps flickering after a few minutes. The other one works fine. "
  "Could you send me a replacement?\n\nThanks,\nSarah Miller"),
 "test-06": ("Kai Krüger", "kontakt@maler-krueger.example", "Koffer Griff ab",
  "Hi,\n\nbei einem von den Werkzeugkoffern, die letzte Woche kamen, ist der Griff abgebrochen, als ich ihn das erste Mal hochgehoben hab. "
  "Was machen wir da?\n\nGruß Kai"),
 "test-08": ("Thomas Becker", "einkauf@becker-haustechnik.example", "Schutzbrillen zerkratzt RW-2026-0412",
  "Guten Tag,\n\nzwei der zehn Schutzbrillen SB-1 aus RW-2026-0412 sind schon zerkratzt angekommen. Bitte schreiben Sie uns die beiden gut.\n\nMit freundlichen Grüßen\nThomas Becker"),
 "test-07": ("Petra Lang", "p.lang@privat.example", "Beschwerde",
  "Guten Tag,\n\nich bin mit meinem Werkzeug sehr unzufrieden, es funktioniert nicht richtig. Bitte melden Sie sich.\n\nPetra Lang"),
}

pick = sys.argv[1:] or list(CASES)
with smtplib.SMTP("localhost", 1025) as smtp:
    for cid in pick:
        name, addr, subject, text = CASES[cid]
        m = EmailMessage()
        m["From"], m["To"], m["Subject"] = f"{name} <{addr}>", "Rheinmark Service <service@rheinmark-handel.example>", subject
        m["Message-ID"] = f"<{cid}@rheinmark-handel.example>"
        m.set_content(text)
        smtp.send_message(m)
        time.sleep(1.1)  # distinct arrival times, so the inbox order is the send order
        print("sent", cid, subject)
