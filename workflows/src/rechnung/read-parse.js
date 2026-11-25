// Node "KI-Antwort prüfen": turns the AI's answer into numbers. Nothing is decided here; the checks come next.
const c = $('Lese-Anfrage').first().json;
const raw = aiText($json) || '';
let inv = {};
try {
  inv = JSON.parse(raw.slice(raw.indexOf('{'), raw.lastIndexOf('}') + 1));
} catch (e) {
  inv = { parse_error: raw.slice(0, 200) };
}
const num = v => (v === null || v === undefined || v === '' ? null : Number(v));
inv.lines = (inv.lines || []).map(l => ({
  code: l.code || null, description: String(l.description || ''), quantity: num(l.quantity) || 0,
  unit_price: num(l.unit_price) || 0, line_total: num(l.line_total),
}));
for (const k of ['net_total', 'vat_rate', 'vat_amount', 'gross_total']) inv[k] = num(inv[k]);
inv.supplier_vat = inv.supplier_vat ? String(inv.supplier_vat).replace(/\s/g, '').toUpperCase() : null;
inv.supplier_iban = inv.supplier_iban ? String(inv.supplier_iban).replace(/\s/g, '').toUpperCase() : null;
const readBy = c.doc.source === 'ocr' ? 'Scan, per OCR gelesen, KI hat die Werte erkannt' : 'PDF-Text, KI hat die Werte erkannt';
return [{ json: { ...c, inv, readBy } }];
