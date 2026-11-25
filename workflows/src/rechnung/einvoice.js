// Node "E-Rechnung übernehmen": Odoo has already read the e-invoice (module account_edi_ubl_cii);
// its values are taken over unchanged. A supplier or bank account the importer created in the last
// 10 minutes counts as new (see "Limits" in the README for what that means).
const c = $('Kontext').first().json;
const result = n => $(n).first().json.result || [];
const bill = result('Beleg lesen')[0] || {};
const lines = result('Belegzeilen lesen').filter(l => !l.display_type || l.display_type === 'product');
const partner = result('Belegpartner lesen')[0] || null;
const bank = result('Bankkonto lesen')[0] || null;
const fresh = d => d && Date.now() - new Date(String(d).replace(' ', 'T') + 'Z').getTime() < 10 * 60 * 1000;
const vatPct = bill.amount_untaxed ? Math.round((bill.amount_tax / bill.amount_untaxed) * 1000) / 10 : null;
const inv = {
  supplier_name: partner ? partner.name : null,
  supplier_vat: partner && partner.vat ? partner.vat.replace(/\s/g, '').toUpperCase() : null,
  supplier_iban: bank ? bank.acc_number.replace(/\s/g, '').toUpperCase() : null,
  bank_new: !!(bank && fresh(bank.create_date)),
  partner_new: !!(partner && fresh(partner.create_date)),
  invoice_number: bill.ref || null,
  invoice_date: bill.invoice_date || null,
  due_date: bill.invoice_date_due || null,
  po_ref: bill.invoice_origin || null,
  currency: 'EUR',
  lines: lines.map(l => ({
    code: ((l.product_id && l.product_id[1]) || '').match(/\[(.*?)\]/)?.[1] || null,
    description: l.name, quantity: l.quantity, unit_price: l.price_unit, line_total: l.price_subtotal,
    move_line_id: l.id, linked_po_line: l.purchase_line_id ? l.purchase_line_id[0] : null,
  })),
  net_total: bill.amount_untaxed, vat_rate: vatPct, vat_amount: bill.amount_tax, gross_total: bill.amount_total, note: null,
};
const syntax = { zugferd: 'ZUGFeRD', cii: 'XRechnung CII' }[c.doc.syntax] || 'XRechnung UBL';
return [{ json: { ...c, inv, importedBillId: bill.id || null, readBy: `E-Rechnung (${syntax}), von Odoo selbst eingelesen, ohne KI` } }];
