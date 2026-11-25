// Node "Rückfrage-Anfrage": for a difference ("abweichung") the AI drafts a short query to the supplier.
// The draft is only sent after a person clicks the button in the approval mail.
const c = $('Abgleich').first().json;
const created = $('Rechnungsentwurf anlegen').isExecuted ? $('Rechnungsentwurf anlegen').first().json.result : null;
const draftId = c.importedBillId || (typeof created === 'number' ? created : null);
const s = c.settings;
const wantQuery = c.decision === 'abweichung' && !!c.supplier;
let llm = null;
if (wantQuery) {
  const settings = { language: 'de', formality: 'Sie', tone: 'sachlich', length: 'short', apology: 'never', closing_de: s.closing_de, signature: s.inv_signature };
  const system = [
    'TASK: supplier_query',
    'Du schreibst für die Kreditorenbuchhaltung der Rheinmark Handels GmbH eine kurze Rückfrage an einen Lieferanten zu einer Rechnung.',
    'Nenne jede Abweichung sachlich mit den Zahlen und bitte um Korrektur oder Gutschrift. Keine Vorwürfe. Halte dich exakt an diesen Stilleitfaden:',
    c.style,
    'Einstellungen: ' + JSON.stringify(settings),
    'Gib NUR die fertige E-Mail zurück: erste Zeile "Betreff: ...", Leerzeile, dann der Text mit Signatur.',
  ].join('\n\n');
  const dd = iso => (iso ? String(iso).slice(0, 10).split('-').reverse().join('.') : '–');
  const user = [
    `MESSAGE-ID: ${c.id}`,
    `Lieferant: ${c.supplier.name}`,
    `Rechnung: ${c.inv.invoice_number} vom ${dd(c.inv.invoice_date)}`,
    `Bestellung: ${c.po ? c.po.name : 'keine'}`,
    `Abweichungen:\n- ${c.checks.map(x => x.text).join('\n- ')}`,
  ].join('\n\n');
  llm = llmRequest(s, system, user, 0.2);
}
return [{ json: { ...c, draftId, wantQuery, llm } }];
