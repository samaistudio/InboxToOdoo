// Node "Kontext": collects the mail, the settings, the style guide and the document text, and writes the
// prompt for the AI (used only for PDFs and scans; e-invoices are read by Odoo).
const body = $('Rechnung eingegangen').first().json.body || {};
const settings = { ...($('Einstellungen').first().json.data || {}) };
const style = $('Stilregeln lesen').first().json.data || '';
const doc = $('Dokument erkennen').first().json;
const pdfText = String(doc.text || '').slice(0, 12000);
const id = String(body.message_id || 'web-' + Date.now()).replace(/[<>]/g, '');
const system = [
  'TASK: invoice_extract',
  'Du liest eine Eingangsrechnung (Text aus einem PDF) und gibst NUR ein JSON-Objekt zurück, ohne Text davor oder danach.',
  'Felder: supplier_name, supplier_vat (USt-IdNr. ohne Leerzeichen), supplier_iban (ohne Leerzeichen), invoice_number, invoice_date (YYYY-MM-DD),',
  'due_date (YYYY-MM-DD), po_ref (unsere Bestellnummer, z. B. "P00001", sonst null), currency, lines (Liste aus {code, description, quantity, unit_price, line_total}),',
  'net_total, vat_rate (z. B. 19), vat_amount, gross_total, note (Hinweise des Lieferanten, sonst null).',
  'Zahlen als Zahl mit Punkt (1234.5). Erfinde nichts: was nicht im Dokument steht, ist null.',
].join('\n');
const source = doc.source === 'ocr' ? 'per OCR aus einem Scan, kann Lesefehler enthalten' : 'aus dem PDF';
const user =
  `MESSAGE-ID: ${id}\nAbsender: ${body.from_name || ''} <${body.from_email || ''}>\nBetreff: ${body.subject || ''}\nDatei: ${body.filename || ''}\n\n` +
  `--- Text des Dokuments (${source}) ---\n${pdfText}`;
return [{ json: { id, mail: body, settings, style, doc, pdfChars: pdfText.length, extractPrompt: { system, user } } }];
