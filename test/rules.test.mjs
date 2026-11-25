// Unit tests for the fixed rules that the n8n Code nodes use (workflows/src/rules/*.js).
// Run: node --test test/rules.test.mjs   (Node 20 or newer, no packages needed)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const inv = require('../workflows/src/rules/invoice-rules.js');
const rek = require('../workflows/src/rules/complaint-rules.js');
const { styleProblems } = require('../workflows/src/rules/reply-style.js');

// same helper as seed/seed_purchase.py: a valid German IBAN for a made-up bank code
function ibanDe(blz, account) {
  const bban = blz + String(account).padStart(10, '0');
  const num = BigInt([...(bban + 'DE00')].map(c => parseInt(c, 36)).join(''));
  return 'DE' + String(98n - (num % 97n)).padStart(2, '0') + bban;
}

test('IBAN checksum: the demo suppliers and a textbook IBAN pass', () => {
  for (const iban of ['DE03990200500001234567', 'DE50990701500007654321', 'DE57990440500005550123', 'DE89370400440532013000', 'GB82WEST12345698765432'])
    assert.equal(inv.ibanOk(iban), true, iban);
  assert.equal(ibanDe('99020050', 1234567), 'DE03990200500001234567');
});

test('IBAN checksum: one changed or swapped digit fails', () => {
  assert.equal(inv.ibanOk('DE03990200500001234568'), false);
  assert.equal(inv.ibanOk('DE03990200500001234657'), false);
  assert.equal(inv.ibanOk('DE13990200500001234567'), false);
});

test('VAT ID: German check digit (ISO 7064 MOD 11,10)', () => {
  for (const v of ['DE298765435', 'DE314159262', 'DE271828180', 'DE123456788']) assert.equal(inv.vatIdOk(v), true, v);
  for (const v of ['DE298765436', 'DE123456789']) assert.equal(inv.vatIdOk(v), false, v);
});

test('VAT ID: known gap, a German ID with only 8 digits passes the general format check', () => {
  // Documents today's behaviour: anything that is not DE + 9 digits is only checked for the EU format.
  assert.equal(inv.vatIdOk('DE12345678'), true);
});

test('VAT ID: other EU countries are checked for format only', () => {
  assert.equal(inv.vatIdOk('ATU12345678'), true);
  assert.equal(inv.vatIdOk('FR1'), false);
});

test('sums: 2-cent allowance, rounding to cents', () => {
  assert.equal(inv.near(380.8, 380.81), true);
  assert.equal(inv.near(380.8, 390.8), false); // inv-07: printed total 10 € too high
  assert.equal(inv.near(null, 1), false);
  assert.equal(inv.r2(0.1 + 0.2), 0.3);
  assert.equal(inv.eu(1839.74), '1.839,74 €');
  assert.equal(inv.eu(null), '–');
});

test('price tolerance: the test invoices', () => {
  const tol = 2;
  // inv-02: 20.90 instead of 19.50 = +7.2 % -> flagged
  assert.equal(inv.priceDiffPct(20.9, 19.5).toFixed(1), '7.2');
  assert.equal(inv.priceOutsideTolerance(20.9, 19.5, tol), true);
  // inv-10: 73.00 instead of 71.00 = +2.8 % -> flagged
  assert.equal(inv.priceDiffPct(73, 71).toFixed(1), '2.8');
  assert.equal(inv.priceOutsideTolerance(73, 71, tol), true);
  // matching price, and a difference inside the tolerance
  assert.equal(inv.priceOutsideTolerance(92, 92, tol), false);
  assert.equal(inv.priceOutsideTolerance(19.85, 19.5, tol), false); // +1.8 %
  // cheaper than ordered by more than the tolerance is flagged too
  assert.equal(inv.priceOutsideTolerance(18, 19.5, tol), true);
  // no order price: nothing to compare
  assert.equal(inv.priceOutsideTolerance(5, 0, tol), false);
});

test('quantity: more billed than delivered and not yet billed', () => {
  assert.equal(inv.qtyOverOpen(30, 20), true); // inv-03: 30 billed, 20 received
  assert.equal(inv.qtyOverOpen(20, 20), false);
  assert.equal(inv.qtyOverOpen(0.1 + 0.2, 0.3), false);
});

const S = { warranty_months_b2b: 12, warranty_months_b2c: 24, default_remedy: 'replacement' };
const now = new Date('2026-11-25T10:00:00Z');

test('warranty: B2B 12 months, B2C 24 months, from the settings', () => {
  assert.equal(rek.warrantyMonths(true, S), 12);
  assert.equal(rek.warrantyMonths(false, S), 24);
  assert.equal(rek.warrantyMonths(false, {}), 24);
  assert.equal(rek.monthsSince('2026-11-03 10:00:00', now).toFixed(2), '0.72');
});

test('remedy: the order of the rules', () => {
  const d = o => rek.decideRemedy({ months: 1, limit: 24, problemType: 'defekt', customerWants: 'unklar', defaultRemedy: 'replacement', ...o }).decision;
  assert.equal(d({ months: 37 }), 'out_of_warranty'); // drill broken after 3 years
  assert.equal(d({ months: 37, problemType: 'falsch_geliefert' }), 'out_of_warranty'); // warranty is checked first
  assert.equal(d({ problemType: 'falsch_geliefert', customerWants: 'gutschrift' }), 'replacement'); // wrong item: always sent again
  assert.equal(d({ problemType: 'fehlt' }), 'replacement');
  assert.equal(d({ customerWants: 'gutschrift' }), 'credit'); // display cracked, wants money back
  assert.equal(d({ customerWants: 'ersatz' }), 'replacement');
  assert.equal(d({}), 'replacement'); // no wish: company default
  assert.equal(d({ defaultRemedy: 'credit' }), 'credit');
});

test('order line: named product, only line, or nothing when the hint matches no line', () => {
  const lines = [{ name: '[BS-18] Akku-Bohrschrauber BS-18' }, { name: '[SB-1] Schutzbrille SB-1' }];
  assert.equal(rek.pickLine(lines, 'Schutzbrillen SB-1').name, '[SB-1] Schutzbrille SB-1');
  assert.equal(rek.pickLine(lines, 'Akku-Bohrschrauber').name, '[BS-18] Akku-Bohrschrauber BS-18');
  assert.equal(rek.pickLine(lines, 'Laser'), null);
  assert.equal(rek.pickLine(lines, null).name, '[BS-18] Akku-Bohrschrauber BS-18');
  assert.equal(rek.pickLine([lines[1]], 'Laser').name, '[SB-1] Schutzbrille SB-1');
});

test('amount: gross price of the affected quantity', () => {
  assert.equal(rek.affectedAmount({ price_total: 141.61, product_uom_qty: 1 }, 1), 141.61);
  assert.equal(rek.affectedAmount({ price_total: 117.81, product_uom_qty: 10 }, 2), 23.56); // two of ten safety glasses
});

test('reply style: a clean German reply passes', () => {
  const ok = 'Betreff: Ihre Reklamation zu Auftrag S00042\n\nSehr geehrte Frau Becker,\n\ndas Gerät ersetzen wir kostenlos.\n\nMit freundlichen Grüßen\n\nLena Hoffmann';
  assert.deepEqual(styleProblems(ok), []);
});

test('reply style: typical machine phrases are caught', () => {
  const has = (t, label) => assert.ok(styleProblems('Betreff: x\n\n' + t).includes(label), t);
  has('Wir ersetzen das Gerät — kostenlos.', 'Gedankenstrich (— oder –)');
  has('I hope this email finds you well.', 'englische KI-Floskel');
  has('Zögern Sie nicht, uns zu kontaktieren.', 'deutsche KI-Floskel');
  has('We offer a seamless process.', 'typisches KI-Wort');
  has('Wir melden uns zeitnah.', 'Füllwort');
  has('Es geht nicht nur um das Gerät, sondern um Ihr Vertrauen.', 'Nicht-X-sondern-Y');
  has('Die Lieferung kommt am [Datum].', 'Platzhalter im Text');
  has('**Wichtig:** bitte prüfen', 'Markdown-Formatierung');
  has('Danke! Bis bald!', 'mehr als ein Ausrufezeichen');
  assert.ok(styleProblems('Hallo,\n\ntext').includes('Betreffzeile fehlt'));
  assert.ok(styleProblems('Betreff: x\n\nMit freundlichen Grüßen,').includes('Satzzeichen nach der Grußformel'));
});
