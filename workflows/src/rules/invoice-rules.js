// Fixed invoice rules. None of them depends on the AI: they only do arithmetic on the values that were read.
// The builder puts this file in front of the "Prüfungen" and "Abgleich" Code nodes;
// test/rules.test.mjs tests the same functions.

// 2-decimal rounding and the 2-cent allowance used for every sum check
const r2 = v => Math.round(v * 100) / 100;
const near = (a, b) => a !== null && b !== null && Math.abs(a - b) <= 0.02;

// 1234.5 -> "1.234,50 €"; null -> "–"
const eu = v =>
  v === null || v === undefined
    ? '–'
    : Number(v).toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';

// German VAT ID (USt-IdNr.): check digit after ISO 7064 MOD 11,10. Other EU countries: format only.
function vatIdOk(v) {
  if (!/^DE\d{9}$/.test(v)) return /^[A-Z]{2}[0-9A-Z]{2,13}$/.test(v);
  let p = 10;
  for (const d of v.slice(2, 10)) {
    const s = (Number(d) + p) % 10 || 10;
    p = (2 * s) % 11;
  }
  const check = 11 - p === 10 ? 0 : 11 - p;
  return check === Number(v[10]);
}

// IBAN checksum (ISO 13616, mod 97 = 1). Expects the IBAN without spaces, upper case.
function ibanOk(iban) {
  const s = iban.slice(4) + iban.slice(0, 4);
  let r = 0;
  for (const ch of s) {
    const v = parseInt(ch, 36);
    r = Number(String(r) + String(v)) % 97;
  }
  return r === 1;
}

// Price on the invoice compared with the purchase order, in percent (+7.2 = 7.2 % more expensive)
const priceDiffPct = (price, orderPrice) => (orderPrice ? ((price - orderPrice) / orderPrice) * 100 : 0);
const priceOutsideTolerance = (price, orderPrice, tolPct) => Math.abs(priceDiffPct(price, orderPrice)) > tolPct;

// More billed than delivered and not yet billed? (1e-9 absorbs floating point noise)
const qtyOverOpen = (qty, open) => qty > open + 1e-9;

// --- end of node code
module.exports = { r2, near, eu, vatIdOk, ibanOk, priceDiffPct, priceOutsideTolerance, qtyOverOpen };
