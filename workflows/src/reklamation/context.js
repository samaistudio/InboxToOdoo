// Node "Kontext": the complaint mail, the settings and the style guide, and the prompt that asks the AI to read the mail.
const body = $('Reklamation eingegangen').first().json.body || {};
const settings = $('Einstellungen').first().json.data || {};
const style = $('Stilregeln lesen').first().json.data || '';
const mail = {
  message_id: String(body.message_id || ('web-' + Date.now())),
  from_email: String(body.from_email || '').toLowerCase().trim(),
  from_name: String(body.from_name || ''),
  subject: String(body.subject || ''),
  text: String(body.text || '').slice(0, 6000),
  received: new Date().toISOString(),
};
const id = mail.message_id.replace(/[<>]/g, '');
const extractPrompt = [
  'TASK: extract',
  'Du liest Reklamations-E-Mails eines Werkzeug-Großhändlers und gibst NUR ein JSON-Objekt zurück, ohne Text davor oder danach.',
  'Felder:',
  '  order_ref: Auftrags- oder Bestellnummer aus der E-Mail (z. B. "RW-2026-0412" oder "S00002"), sonst null',
  '  product_hint: Produktname oder Artikelnummer, die der Kunde nennt, sonst null',
  '  quantity_affected: betroffene Stückzahl als Zahl, sonst 1',
  '  problem_type: "defekt" | "beschaedigt" | "falsch_geliefert" | "fehlt" | "sonstiges"',
  '  customer_wants: "ersatz" | "gutschrift" | "reparatur" | "unklar"',
  '  urgency: "normal" | "hoch"',
  '  language: "de" | "en"',
  '  formality_used: "Sie" | "du"',
  '  summary: ein Satz auf Deutsch, worum es geht',
  'Erfinde nichts. Was nicht in der E-Mail steht, ist null oder "unklar".',
].join('\n');
const user = `MESSAGE-ID: ${id}\nVon: ${mail.from_name} <${mail.from_email}>\nBetreff: ${mail.subject}\n\n${mail.text}`;
return [{ json: { id, mail, settings, style, extractPrompt: { system: extractPrompt, user } } }];
