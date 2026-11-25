// Node "Antwort-Anfrage": the AI writes the reply to the customer from the decision and the Odoo facts,
// following prompts/EMAIL_STYLE.md and the company settings (llmRequest from shared/llm-request.js).
const c = $('Entscheidung').first().json;
const draftId = $('Entwurf in Odoo anlegen').isExecuted ? $('Entwurf in Odoo anlegen').first().json.result : null;
const s = c.settings;
const lang = s.language === 'auto' ? (c.ext.language === 'en' ? 'en-US' : 'de') : s.language;
const formality = s.formality === 'auto' ? c.ext.formality_used : s.formality;
const what = {
  credit: 'Gutschrift über den genannten Betrag',
  replacement: 'kostenlose Ersatzlieferung',
  need_info: 'Rückfrage: fehlende Angaben anfordern',
  out_of_warranty: 'Ablehnung, weil die Gewährleistung abgelaufen ist; kostenpflichtige Reparatur anbieten',
}[c.decision];
const replySettings = {
  language: lang, formality, tone: s.tone, length: s.length, apology: s.apology,
  closing_de: s.closing_de, closing_en: s.closing_en, signature: s.signature,
};
const system = [
  'TASK: reply',
  'Du schreibst die Antwort-E-Mail des Kundenservice der Rheinmark Handels GmbH auf eine Reklamation.',
  'Halte dich exakt an diesen Stilleitfaden:',
  c.style,
  'Einstellungen für diese E-Mail:',
  JSON.stringify(replySettings),
  s.custom_rules ? 'Zusätzliche Regeln des Unternehmens: ' + s.custom_rules : '',
  'Gib NUR die fertige E-Mail zurück: erste Zeile "Betreff: ..." (bzw. "Subject: ..."), Leerzeile, dann der Text mit Signatur.',
].filter(Boolean).join('\n\n');
const user = [
  `MESSAGE-ID: ${c.id}`,
  `Entscheidung: ${what}`,
  `Begründung (intern): ${c.reason}`,
  `Fakten aus Odoo: ${JSON.stringify(c.facts)}`,
  `Original-E-Mail des Kunden:\nBetreff: ${c.mail.subject}\n${c.mail.text}`,
].join('\n\n');
return [{ json: { ...c, draftId, lang, llm: llmRequest(s, system, user, 0.3) } }];
