// Node "Prüfungen": the fixed checks on the invoice itself (sums, VAT, VAT ID, IBAN, records the importer just created).
// Uses r2, near, eu, vatIdOk and ibanOk from rules/invoice-rules.js.
const c = $json, inv = c.inv;
const checks = [];
const warn = text => checks.push({ level: 'warn', text });
const block = (text, extra) => checks.push({ level: 'block', text, ...extra });

if (inv.parse_error) block('Rechnung konnte nicht gelesen werden.');

// each line: quantity × price = line total
inv.lines.forEach((l, i) => {
  const calc = r2(l.quantity * l.unit_price);
  if (l.line_total !== null && !near(calc, l.line_total))
    warn(`Position ${i + 1}: Menge × Preis ergibt ${eu(calc)}, nicht ${eu(l.line_total)}.`);
});

// lines add up to the net total, VAT is right, net + VAT = gross
const sumLines = r2(inv.lines.reduce((s, l) => s + l.quantity * l.unit_price, 0));
if (inv.net_total !== null && !near(sumLines, inv.net_total))
  warn(`Summe der Positionen ${eu(sumLines)} weicht vom Nettobetrag ${eu(inv.net_total)} ab.`);
if (inv.net_total !== null && inv.vat_rate !== null && inv.vat_amount !== null) {
  const vat = r2((inv.net_total * inv.vat_rate) / 100);
  if (!near(vat, inv.vat_amount))
    warn(`Umsatzsteuer: ${inv.vat_rate} % von ${eu(inv.net_total)} sind ${eu(vat)}, auf der Rechnung ${eu(inv.vat_amount)}.`);
}
if (inv.net_total !== null && inv.vat_amount !== null && inv.gross_total !== null) {
  const gross = r2(inv.net_total + inv.vat_amount);
  if (!near(gross, inv.gross_total))
    warn(`Rechenfehler: Netto ${eu(inv.net_total)} + USt ${eu(inv.vat_amount)} = ${eu(gross)}, auf der Rechnung steht ${eu(inv.gross_total)}.`);
}

// VAT ID and IBAN check digits
if (!inv.supplier_vat) warn('Keine USt-IdNr. auf der Rechnung (Pflichtangabe nach § 14 UStG, oder Steuernummer).');
else if (!vatIdOk(inv.supplier_vat)) warn(`USt-IdNr. ${inv.supplier_vat} hat keine gültige Prüfziffer.`);
if (inv.supplier_iban && !ibanOk(inv.supplier_iban)) block(`IBAN ${inv.supplier_iban} ist ungültig (Prüfsumme).`);

// e-invoices: a supplier or bank account that Odoo's importer had to create is not a known one
if (inv.partner_new)
  block(`Lieferant "${inv.supplier_name}" wurde gerade erst beim Einlesen neu angelegt, ist also kein bekannter Lieferant.`);
if (inv.bank_new)
  block(
    `Bankverbindung ${inv.supplier_iban} wurde beim Einlesen neu angelegt und war vorher nicht in Odoo. ` +
      'Nicht per E-Mail klären, beim Lieferanten unter der bekannten Telefonnummer nachfragen.',
    { fraud: true },
  );

return [{ json: { ...c, inv, checks } }];
