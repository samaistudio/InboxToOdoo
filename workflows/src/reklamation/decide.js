// Node "Entscheidung": finds the order line and decides the remedy with the rules in rules/complaint-rules.js,
// then prepares the draft for Odoo (credit note or replacement order).
const c = $('KI-Antwort prüfen').first().json;
const s = c.settings, ext = c.ext;
const result = n => $(n).first().json.result || [];
const order = result('Auftrag suchen')[0] || null;
const lines = order ? result('Positionen lesen') : [];
const picks = order ? result('Lieferung lesen') : [];
const partner = order ? result('Kunde lesen')[0] || {} : {};
const now = new Date();

let decision, reason, line = null, amount = 0, delivered = null, months = null, limit = null;
if (!order) {
  decision = 'need_info';
  reason = 'Kein passender Auftrag gefunden: Auftragsnummer fehlt oder stimmt nicht.';
} else {
  line = pickLine(lines, ext.product_hint);
  delivered = picks.map(p => p.date_done).filter(Boolean).sort()[0] || null;
  if (!line) {
    decision = 'need_info';
    reason = 'Auftrag gefunden, aber unklar, welches Produkt betroffen ist.';
  } else if (!delivered) {
    decision = 'need_info';
    reason = 'Der Auftrag ist laut Odoo noch nicht ausgeliefert.';
  } else {
    amount = affectedAmount(line, Math.min(ext.quantity_affected, line.product_uom_qty));
    months = monthsSince(delivered, now);
    limit = warrantyMonths(partner.is_company, s);
    ({ decision, reason } = decideRemedy({ months, limit, problemType: ext.problem_type, customerWants: ext.customer_wants, defaultRemedy: s.default_remedy }));
  }
}

const qty = line ? Math.min(ext.quantity_affected, line.product_uom_qty) : 0;
const facts = {
  customer: partner.name || c.mail.from_name,
  customer_type: partner.id ? (partner.is_company ? 'Firmenkunde' : 'Privatkunde') : 'unbekannt',
  customer_email: partner.email || c.mail.from_email,
  customer_lang: partner.lang || null,
  order: order ? order.name : null,
  order_ref: order ? order.client_order_ref : ext.order_ref,
  order_date: order ? order.date_order.slice(0, 10) : null,
  delivered: delivered ? delivered.slice(0, 10) : null,
  product: line ? line.name : ext.product_hint,
  quantity: qty,
  amount_eur: amount,
  invoice: order && order.invoice_ids.length ? order.invoice_ids[0] : null,
  months_since_delivery: months ? Math.round(months * 10) / 10 : null,
  warranty_months: limit,
};

// the draft in Odoo: a credit note against the customer's invoice, or a free replacement order
let draft = null;
if (decision === 'credit')
  draft = { model: 'account.move', values: {
    move_type: 'out_refund', partner_id: order.partner_id[0], reversed_entry_id: facts.invoice, invoice_origin: order.name, ref: `Reklamation ${c.id}`,
    invoice_line_ids: [[0, 0, { product_id: line.product_id[0], quantity: qty, price_unit: line.price_unit, tax_ids: [[6, 0, line.tax_id]] }]],
  } };
if (decision === 'replacement')
  draft = { model: 'sale.order', values: {
    partner_id: order.partner_id[0], origin: order.name, client_order_ref: `Ersatz zu ${order.client_order_ref || order.name}`,
    note: `Ersatzlieferung, Reklamation ${c.id}`,
    order_line: [[0, 0, { product_id: line.product_id[0], product_uom_qty: qty, price_unit: 0 }]],
  } };

return [{ json: { ...c, order, decision, reason, facts, draft } }];
