// The hard writing rules from prompts/EMAIL_STYLE.md that code can check after the AI has written a reply.
// A reply with a problem is sent back to the AI once ("Stil korrigieren"). test/rules.test.mjs tests the list.
const STYLE_RULES = [
  [/[—–]|\s--\s/, 'Gedankenstrich (— oder –)'],
  [/hope this (email|e-mail) finds you|reaching out|don'?t hesitate|feel free to|i hope this helps|great question/i, 'englische KI-Floskel'],
  [/erreicht Sie wohlbehalten|zögern Sie nicht|ich hoffe, (das|dies) hilft|an uns gewandt haben|jederzeit (gerne )?zur Verfügung/i, 'deutsche KI-Floskel'],
  [/\b(delve|seamless|robust|leverage|elevate|streamline|comprehensive|pivotal|testament)\b/i, 'typisches KI-Wort'],
  [/\b(nahtlos|umfassend|maßgeschneidert|zeitnah)\b/i, 'Füllwort'],
  [/nicht nur .{0,60}, sondern|isn'?t just .{0,40}, it'?s/i, 'Nicht-X-sondern-Y'],
  [/\[[^\]]{2,30}\]|\{[a-z_]+\}/, 'Platzhalter im Text'],
  [/\*\*|^#+\s/m, 'Markdown-Formatierung'],
  [/!.*!/s, 'mehr als ein Ausrufezeichen'],
];

function styleProblems(text) {
  const problems = STYLE_RULES.filter(([re]) => re.test(text)).map(([, label]) => label);
  if (!/^(Betreff|Subject):/i.test(text)) problems.push('Betreffzeile fehlt');
  if (/Mit freundlichen Grüßen[,.]/.test(text)) problems.push('Satzzeichen nach der Grußformel');
  return problems;
}

// --- end of node code
module.exports = { styleProblems, STYLE_RULES };
