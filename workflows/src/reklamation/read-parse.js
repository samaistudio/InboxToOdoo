// Node "KI-Antwort prüfen": checks the AI's reading of the complaint against the allowed values
// and builds the Odoo search for the order (by order number, else by the sender's e-mail).
const ctx = $('Lese-Anfrage').first().json;
const raw = aiText($json) || '';
let ext = {};
try {
  ext = JSON.parse(raw.slice(raw.indexOf('{'), raw.lastIndexOf('}') + 1));
} catch (e) {
  ext = { parse_error: raw.slice(0, 200) };
}
const allowed = {
  problem_type: ['defekt', 'beschaedigt', 'falsch_geliefert', 'fehlt', 'sonstiges'],
  customer_wants: ['ersatz', 'gutschrift', 'reparatur', 'unklar'],
  urgency: ['normal', 'hoch'],
  language: ['de', 'en'],
  formality_used: ['Sie', 'du'],
};
const defaults = { problem_type: 'sonstiges', customer_wants: 'unklar', urgency: 'normal', language: 'de', formality_used: 'Sie' };
for (const [k, vals] of Object.entries(allowed)) if (!vals.includes(ext[k])) ext[k] = defaults[k];
ext.quantity_affected = Math.max(1, parseInt(ext.quantity_affected) || 1);
const ref = ext.order_ref ? String(ext.order_ref).trim() : null;
const domain = ref ? ['|', ['client_order_ref', '=', ref], ['name', '=', ref]] : [['partner_id.email', '=ilike', ctx.mail.from_email]];
return [{ json: { ...ctx, ext, orderDomain: domain } }];
