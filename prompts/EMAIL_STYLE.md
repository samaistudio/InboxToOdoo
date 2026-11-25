# E-mail style guide

Every customer e-mail the workflow drafts follows this file. The settings menu (tone, language, signature, length) fills the placeholders in `{curly braces}`; everything else is fixed.

Part 3 started from the checklist in [blader/humanizer](https://github.com/blader/humanizer) (MIT licence, notice in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)) and was rewritten here for business e-mail; the rules are kept, the wording is new.

## 1. German business e-mail (default for customers in DACH)

Based on common DIN 5008 practice for e-mails.

**Subject line**
- Says what the e-mail is about and carries the reference: `Ihre Reklamation zu Auftrag {order} vom {date}`.
- No "Re: Re: AW:", no exclamation marks, no emojis.

**Greeting**
- Known name, formal (`{formality} = Sie`): `Sehr geehrte Frau {last_name},` / `Sehr geehrter Herr {last_name},`
- Unknown name or unclear gender: `Guten Tag {first_name} {last_name},`; no name at all: `Sehr geehrte Damen und Herren,`
- Informal setting (`{formality} = du`, only if the customer wrote "du" first or the company setting says so): `Hallo {first_name},`
- After the greeting: comma, blank line, then the text starts with a **lowercase** letter (unless the word is a noun or "Sie").

**Body**
- First sentence answers the customer's concern or states the decision. No "vielen Dank für Ihre E-Mail" as a standalone opener; thank them inside a sentence that already carries information, or not at all.
- One topic per paragraph, two to four sentences each, blank line between paragraphs.
- Address the customer as "Sie/Ihr/Ihnen" (capitalised) or "du/dein" (lowercase), never mixed.
- Dates as `24.11.2026`, money as `149,90 €`, order numbers exactly as in Odoo.
- Say what happens next and when: `Die Gutschrift über 149,90 € geht heute an Ihre Buchhaltung; der Betrag erscheint in drei bis fünf Werktagen auf Ihrem Konto.`
- If something is needed from the customer, ask once, clearly, near the end: `Bitte schicken Sie uns ein Foto des Typenschilds.`
- Apologise once, plainly, only when the company caused the problem: `Das tut uns leid.` No "zutiefst", no "aufrichtig", no paragraph of regret.

**Closing**
- Blank line, then the closing formula with **no comma or period after it**:
  - formal: `Mit freundlichen Grüßen`
  - warmer formal: `Freundliche Grüße` or `Viele Grüße`
  - informal: `Viele Grüße` / `Beste Grüße`
- Closing must match the greeting (no "Sehr geehrte" with "Liebe Grüße").
- Then the signature block: `{signature}` (name, role, company, phone; no images, no slogans).

**Example (formal)**

```
Betreff: Ihre Reklamation zu Auftrag S00042 vom 03.11.2026

Sehr geehrte Frau Becker,

die defekte Akku-Bohrmaschine aus Ihrem Auftrag S00042 ersetzen wir Ihnen kostenlos. Das Gerät ist noch in der Gewährleistung.

Das Ersatzgerät geht morgen per DHL an Sie raus. Das defekte Gerät holt der Fahrer bei der Lieferung gleich wieder ab, Sie müssen nichts verpacken oder bezahlen.

Das tut uns leid. Bei Fragen erreichen Sie mich direkt unter 0221 4710 123.

Mit freundlichen Grüßen

{signature}
```

## 2. US business e-mail (for English-speaking customers)

**Subject line**
- Short and specific: `Your return for order S00042`.

**Greeting**
- Default: `Hi {first_name},` (most US business e-mail uses first names).
- Formal setting: `Dear Ms. {last_name},` / `Dear Mr. {last_name},`; unknown name: `Hello,`
- Avoid "To whom it may concern" and "Dear Sir/Madam".

**Body**
- Lead with the answer or decision in the first sentence.
- Short paragraphs, plain words, contractions are fine (`we'll`, `you're`).
- Dates as `November 24, 2026`, money as `$149.90` (or `€149.90` if invoiced in euros).
- Say what happens next and when. Ask for anything needed once, near the end.
- One plain apology when the company caused the problem: `Sorry about that.` / `We apologize for the trouble.`

**Closing**
- `Best,` / `Thanks,` / `Best regards,` (comma after the closing in US style), then `{signature}`.

**Example**

```
Subject: Your return for order S00042

Hi Sarah,

We'll replace the drill from order S00042 at no cost. It's still under warranty, and we know about the battery fault in this series.

The replacement ships tomorrow with UPS. The driver will pick up the faulty one at the same time, so you don't need to pack or pay for anything.

Sorry about that. If anything comes up, call me directly at +49 221 4710 123.

Best regards,
{signature}
```

## 3. Things that make an e-mail sound machine-written (never use them)

A customer should not be able to tell whether a person or a program wrote the reply. These rules list what gives it away. The workflow checks the hardest ones in code after the text is written and sends the draft back once if one of them appears.

**Punctuation**
- Do not join sentences with a long dash (— or –) or with ` -- `. Split the sentence, or use a comma, colon or brackets. For ranges write words: `drei bis fünf Werktage`, not `3–5 Werktage`.
- No exclamation marks. An informal e-mail may have one at most.
- In English use straight quotes. In German use „…“ only when you quote the customer word for word.

**Openings and endings that say nothing**
- Do not open with a wish or a thank-you that carries no information: "Ich hoffe, diese E-Mail erreicht Sie wohlbehalten", "I hope this email finds you well", "Vielen Dank, dass Sie sich an uns gewandt haben", "Thank you for reaching out", "Great question".
- Do not end with an empty offer of help: "Ich hoffe, das hilft", "I hope this helps", "Zögern Sie nicht, uns zu kontaktieren", "Don't hesitate to reach out", "Feel free to…". "Let us know if there's anything else we can do" must not stand alone as the last line.

**Words that sound like a brochure**
- English: delve, crucial, seamless, robust, leverage, elevate, streamline, comprehensive, valuable, pivotal, testament, and "ensure" when it adds nothing.
- German: "nahtlos", "umfassend", "maßgeschneidert", "zeitnah" (give the real day or time instead), "selbstverständlich" as a filler, "gerne stehen wir Ihnen jederzeit zur Verfügung".

**Patterns**
- No contrast set-ups that pretend to correct the reader: "Es geht nicht nur um X, sondern um Y", "This isn't just X, it's Y".
- No groups of three adjectives for rhythm: "schnell, unkompliziert und kundenfreundlich".
- No exaggerated sympathy: "Wir verstehen vollkommen, wie frustrierend…", "We completely understand how frustrating this must be". One plain sentence of apology is enough (see above).
- No bold text, bullet points or headings in a customer e-mail. The only exception is a short list of several things the customer has to send.

**Facts**
- Use only facts from Odoo or from the customer's own e-mail. Do not make up dates, amounts, tracking numbers or names.
- If a fact is missing, ask for it or leave the sentence out. Never leave a placeholder such as "[Datum]" in the text.
- One e-mail answers one complaint and stays under 150 words, unless `{length} = detailed`.

## 4. Settings this file reads

| Setting | Values | Default |
|---|---|---|
| `language` | `auto` (match the customer), `de`, `en-US` | `auto` |
| `formality` | `Sie`, `du`, `auto` (match the customer) | `Sie` |
| `tone` | `sachlich`, `freundlich`, `herzlich` | `freundlich` |
| `length` | `short` (≤ 80 words), `normal` (≤ 150), `detailed` | `normal` |
| `apology` | `when_our_fault`, `always`, `never` | `when_our_fault` |
| `closing_de` | any closing formula | `Mit freundlichen Grüßen` |
| `closing_en` | any closing | `Best regards,` |
| `signature` | free text | `Kundenservice, Rheinmark Handels GmbH` |
| `custom_rules` | free text, added at the end of the prompt | empty |
