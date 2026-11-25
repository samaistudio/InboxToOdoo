// Node "Abgleich": compares the invoice with Odoo (supplier, bank account, duplicates, purchase order, goods receipt)
// and prepares the draft vendor bill. Uses eu, priceDiffPct, priceOutsideTolerance and qtyOverOpen from rules/invoice-rules.js.
const c = $('Prüfungen').first().json;
const s = c.settings, inv = c.inv, checks = [...c.checks];
const result = n => $(n).first().json.result || [];
const supplier = result('Lieferant suchen')[0] || null;
const banks = supplier ? result('Bankkonten lesen') : [];
const pos = supplier ? result('Bestellungen suchen') : [];
const poLines = supplier ? result('Bestellpositionen lesen') : [];
const dupes = supplier ? result('Dubletten prüfen') : [];
const tol = Number(s.inv_price_tolerance_pct ?? 2);
const warn = text => checks.push({ level: 'warn', text });
const block = (text, extra) => checks.push({ level: 'block', text, ...extra });
const clean = x => String(x || '').replace(/\s/g, '').toUpperCase();

// supplier, duplicate, bank account, VAT ID
if (!supplier) block(`Lieferant "${inv.supplier_name}" (${inv.supplier_vat || 'ohne USt-IdNr.'}) ist nicht in Odoo angelegt.`);
if (dupes.length) {
  const state = d => ({ draft: 'Entwurf', posted: 'gebucht' })[d.state] || d.state;
  const found = dupes.map(d => (d.name && d.name !== '/' ? d.name + ', ' : '') + state(d)).join('; ');
  block(`Rechnung ${inv.invoice_number} ist schon erfasst (${found}).`);
}
if (supplier && inv.supplier_iban && banks.length && !banks.some(b => clean(b.acc_number) === inv.supplier_iban))
  block(
    `Bankverbindung weicht ab: Rechnung ${inv.supplier_iban}, in Odoo ${banks.map(b => clean(b.acc_number)).join(', ')}. ` +
      'Nicht per E-Mail klären, beim Lieferanten unter der bekannten Telefonnummer nachfragen.',
    { fraud: true },
  );
if (supplier && supplier.vat && inv.supplier_vat && clean(supplier.vat) !== inv.supplier_vat)
  warn(`USt-IdNr. auf der Rechnung (${inv.supplier_vat}) passt nicht zu Odoo (${supplier.vat}).`);

// pick the purchase order: the one named on the invoice, or the only open one whose lines fit
const byPo = {};
for (const l of poLines) (byPo[l.order_id[0]] = byPo[l.order_id[0]] || []).push(l);
const code = l => (l.name.match(/\[(.*?)\]/) || [])[1] || '';
const fits = (pl, il) =>
  (il.code && code(pl).toUpperCase() === String(il.code).toUpperCase()) ||
  (il.description && pl.name.toLowerCase().includes(il.description.toLowerCase().slice(0, 18)));
let po = null, poNote = null;
if (inv.po_ref) {
  po = pos.find(p => p.name === inv.po_ref || p.partner_ref === inv.po_ref || p.origin === inv.po_ref) || null;
  if (!po && supplier) warn(`Bestellung ${inv.po_ref} gibt es bei diesem Lieferanten in Odoo nicht.`);
} else if (supplier) {
  const open = pos.filter(p =>
    inv.lines.every(il => (byPo[p.id] || []).some(pl => fits(pl, il) && pl.qty_received - pl.qty_invoiced >= il.quantity)),
  );
  if (open.length === 1) {
    po = open[0];
    poNote = `Keine Bestellnummer auf der Rechnung; zugeordnet über Lieferant und Artikel: ${po.name}.`;
  } else
    warn(open.length ? `Keine Bestellnummer; ${open.length} offene Bestellungen passen, bitte zuordnen.` : 'Keine Bestellnummer und keine passende offene Bestellung.');
}

// 3-way match per line: ordered, received, already invoiced, this invoice
const rows = inv.lines.map((il, i) => {
  const pl = po ? (byPo[po.id] || []).find(l => fits(l, il)) : null;
  // a bill Odoo imported may already be linked to this order line; don't count it against itself
  const self = pl && inv.lines[i] && inv.lines[i].linked_po_line === pl.id ? il.quantity : 0;
  const row = {
    pos: i + 1, text: il.description, code: il.code, qty: il.quantity, price: il.unit_price,
    ordered: pl ? pl.product_qty : null, received: pl ? pl.qty_received : null,
    invoiced: pl ? pl.qty_invoiced - self : null, po_price: pl ? pl.price_unit : null, issues: [],
  };
  if (po && !pl) row.issues.push('nicht bestellt');
  if (pl) {
    const open = pl.qty_received - (pl.qty_invoiced - self);
    if (qtyOverOpen(il.quantity, open)) row.issues.push(`Menge ${il.quantity} > geliefert und noch nicht berechnet ${open}`);
    if (priceOutsideTolerance(il.unit_price, pl.price_unit, tol)) {
      const diff = priceDiffPct(il.unit_price, pl.price_unit);
      row.issues.push(`Preis ${eu(il.unit_price)} statt ${eu(pl.price_unit)} (${diff > 0 ? '+' : ''}${diff.toFixed(1).replace('.', ',')} %)`);
    }
    row.line = pl;
  }
  if (dupes.length) row.issues = [];
  row.issues.forEach(t => warn(`Position ${i + 1} (${il.code || il.description}): ${t}.`));
  return row;
});

const blocked = checks.some(x => x.level === 'block');
const decision = blocked ? 'blockiert' : checks.length ? 'abweichung' : 'ok';

// the draft vendor bill: an e-invoice is already a draft in Odoo (only the order lines are linked); otherwise create one
let draft = null;
if (c.importedBillId && !blocked)
  draft = { model: 'account.move', method: 'write', args: [[c.importedBillId], {
    invoice_origin: po ? po.name : false,
    narration: `Automatisch erfasst aus ${c.mail.filename || 'E-Rechnung'} (${c.id}); E-Rechnung von Odoo eingelesen.`,
    invoice_line_ids: rows
      .filter(r => r.line && !inv.lines[r.pos - 1].linked_po_line)
      .map(r => [1, inv.lines[r.pos - 1].move_line_id, { purchase_line_id: r.line.id }]),
  }] };
else if (!blocked && supplier)
  draft = { model: 'account.move', method: 'create', values: {
    move_type: 'in_invoice', partner_id: supplier.id, ref: inv.invoice_number,
    invoice_date: inv.invoice_date, invoice_date_due: inv.due_date || false, invoice_origin: po ? po.name : false,
    partner_bank_id: (banks.find(b => clean(b.acc_number) === inv.supplier_iban) || {}).id || false,
    narration: `Automatisch erfasst aus ${c.mail.filename || 'PDF'} (${c.id}).`,
    invoice_line_ids: rows.map(r => [0, 0, r.line
      ? { product_id: r.line.product_id[0], name: r.line.name, quantity: r.qty, price_unit: r.price, purchase_line_id: r.line.id, tax_ids: [[6, 0, r.line.taxes_id]] }
      : { name: r.text, quantity: r.qty, price_unit: r.price }]),
  } };
if (draft && draft.method === 'create') draft.args = [draft.values];

return [{ json: { ...c, supplier, po: po ? { id: po.id, name: po.name } : null, poNote, rows, checks, decision, draft } }];
