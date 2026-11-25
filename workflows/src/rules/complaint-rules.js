// Fixed complaint rules: which order line is meant, warranty, and which remedy is proposed.
// The AI only fills in what the customer wrote (problem type, wish, product hint); everything here is plain logic.
// The builder puts this file in front of the "Entscheidung" Code node; test/rules.test.mjs tests the same functions.

const DAY_MS = 1000 * 60 * 60 * 24;
const MONTH_DAYS = 30.44;

// The order line the customer means: the product they named, else the only line, else (no hint at all) the first line.
function pickLine(lines, productHint) {
  const hint = (productHint || '').toLowerCase();
  const code = l => (l.name.match(/\[(.*?)\]/) || [])[1]?.toLowerCase() || '###';
  return (
    lines.find(l => hint && (l.name.toLowerCase().includes(hint) || hint.includes(code(l)))) ||
    (lines.length === 1 ? lines[0] : null) ||
    (hint ? null : lines[0])
  );
}

// Months between an Odoo datetime ("2026-11-03 10:00:00", UTC) and now, as a decimal number
const monthsSince = (odooDatetime, now) => (now - new Date(odooDatetime.replace(' ', 'T') + 'Z')) / (DAY_MS * MONTH_DAYS);

// Warranty in months from the settings: business customers (B2B) and private customers (B2C)
const warrantyMonths = (isCompany, s) => (isCompany ? Number(s.warranty_months_b2b || 12) : Number(s.warranty_months_b2c || 24));

// The remedy for a complaint whose order, line and delivery are known.
// Order of the rules: warranty first, then wrong or missing goods, then the customer's wish, then the company default.
function decideRemedy({ months, limit, problemType, customerWants, defaultRemedy }) {
  if (months > limit) return { decision: 'out_of_warranty', reason: `Lieferung vor ${Math.round(months)} Monaten, Gewährleistung ${limit} Monate.` };
  if (['falsch_geliefert', 'fehlt'].includes(problemType)) return { decision: 'replacement', reason: 'Falsche oder fehlende Ware wird nachgeliefert.' };
  if (customerWants === 'gutschrift') return { decision: 'credit', reason: 'Kunde wünscht Gutschrift, innerhalb der Gewährleistung.' };
  if (customerWants === 'ersatz') return { decision: 'replacement', reason: 'Kunde wünscht Ersatz, innerhalb der Gewährleistung.' };
  return { decision: defaultRemedy === 'credit' ? 'credit' : 'replacement', reason: 'Innerhalb der Gewährleistung, Standardlösung laut Einstellungen.' };
}

// Amount for the affected quantity, gross, rounded to cents
const affectedAmount = (line, qty) => Math.round((line.price_total / line.product_uom_qty) * qty * 100) / 100;

// --- end of node code
module.exports = { pickLine, monthsSince, warrantyMonths, decideRemedy, affectedAmount };
