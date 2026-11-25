// Node "Freigabe-Mail bauen": the approval e-mail to the complaint team. Presentation only: the decision,
// the facts and the reply come from the earlier nodes. Uses the helpers in shared/mail-layout.js.
let c = $('Stilprüfung').first().json;
if ($('Stil korrigieren').isExecuted) {
  const fixed = (aiText($('Stil korrigieren').first().json) || '').trim();
  if (fixed && !fixed.startsWith('NO_FIXTURE')) c = { ...c, reply: fixed, fixed: true };
}
const [first, ...rest] = c.reply.split('\n');
const subject = first.replace(/^(Betreff|Subject):\s*/i, '').trim();
const body = rest.join('\n').replace(/^\s+/, '');
const resume = $execution.resumeUrl + ($execution.resumeUrl.includes('?') ? '&' : '?');
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const money = v => Number(v).toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';
const f = c.facts;

// one word per decision, the same in the subject and the headline, then one short line
const label = { credit: 'Gutschrift', replacement: 'Ersatzlieferung', need_info: 'Rückfrage', out_of_warranty: 'Ablehnung' }[c.decision];
const sub = {
  credit: `Gutschrift über ${money(f.amount_eur)} als Entwurf in Odoo, Antwort an den Kunden ist geschrieben.`,
  replacement: 'Ersatzauftrag als Entwurf in Odoo, Antwort an den Kunden ist geschrieben.',
  need_info: 'Angaben fehlen. Die Rückfrage an den Kunden ist geschrieben.',
  out_of_warranty: 'Außerhalb der Gewährleistung. Die Antwort an den Kunden ist geschrieben.',
}[c.decision];
const accent = { credit: M.ok, replacement: M.ok, need_info: M.neutral, out_of_warranty: M.look }[c.decision];
const odooAction = c.draft && c.draft.model === 'sale.order' ? 'sale.action_quotations' : 'account.action_move_out_refund_type';
const odooLink = c.draftId && c.draft ? `${ODOO_WEB}/odoo/action-${odooAction}/${c.draftId}` : null;

// the facts as a person reads them: labels instead of codes, exact age of the delivery, warranty left
const problemDe = { defekt: 'Defekt', beschaedigt: 'Beschädigt', falsch_geliefert: 'Falsche Ware geliefert', fehlt: 'Ware fehlt', sonstiges: 'Sonstiges' }[c.ext.problem_type] || c.ext.problem_type;
const wishDe = { ersatz: 'Ersatz', gutschrift: 'Gutschrift', reparatur: 'Reparatur', unklar: 'nicht genannt' }[c.ext.customer_wants] || c.ext.customer_wants;
const daysSince = f.delivered ? Math.floor((Date.now() - Date.parse(f.delivered + 'T00:00:00Z')) / 86400000) : null;
const ago = d => (d === null ? '' : d < 1 ? 'heute' : d === 1 ? 'vor 1 Tag' : d < 60 ? `vor ${d} Tagen` : `vor ${Math.round(d / 30.44)} Monaten`);
const left = () => {
  const m = f.warranty_months - f.months_since_delivery;
  if (m >= 2) return `noch ${Math.floor(m)} Monate`;
  if (m >= 1) return 'noch 1 Monat';
  return `noch ${Math.max(0, Math.round(m * 30.44))} Tage`;
};
const product = p => {
  if (!p) return null;
  const code = (String(p).match(/^\[(.*?)\]\s*/) || [])[1];
  const name = String(p).replace(/^\[.*?\]\s*/, '');
  return code && !name.includes(code) ? `${name} (${code})` : name;
};
const muted = t => `<span style="color:${M.muted}">${t}</span>`;
const custType = f.customer_type === 'unbekannt' ? 'nicht in Odoo gefunden' : f.customer_type;
const rows = [
  ['Kunde', `${esc(f.customer)} ${muted('· ' + esc(custType))}`],
  ['Auftrag', f.order_ref || f.order ? esc([f.order_ref, f.order && f.order !== f.order_ref ? `Odoo ${f.order}` : null].filter(Boolean).join(' · ')) : null],
  ['Produkt', f.product ? `${esc(product(f.product))}${f.quantity ? ` · ${f.quantity} Stück` : ''}` : null],
  ['Geliefert', f.delivered ? `${deDate(f.delivered)}${daysSince !== null ? ' ' + muted('· ' + ago(daysSince)) : ''}` : null],
  ['Gewährleistung', f.warranty_months
    ? `${f.warranty_months} Monate (${f.customer_type}) · ${c.decision === 'out_of_warranty' ? `<b style="color:${M.stop}">abgelaufen</b>` : left()}`
    : null],
  ['Betrag', f.amount_eur ? `${money(f.amount_eur)} ${muted('inkl. USt')}` : null],
  ['Problem', esc(problemDe)],
  ['Wunsch des Kunden', esc(wishDe)],
];
const original = String(c.mail.text || '').trim();
const short = original.length > 700 ? original.slice(0, 700).replace(/\s+\S*$/, '') + ' …' : original;
const aiRow = `${esc(c.llm.label)}${c.llm.model && c.llm.model !== 'local-model' ? `, Modell ${esc(c.llm.model)}` : ''} · ` +
  (c.llm.local ? 'lokal, keine Daten nach außen' : 'Cloud: Inhalt der Reklamation wurde an diesen Anbieter übertragen');
const styleRow = c.fixed
  ? 'Erster Entwurf verletzte Stilregeln und wurde einmal automatisch überarbeitet'
  : c.problems.length ? `<span style="color:${M.stop}">Stilhinweise: ${esc(c.problems.join(', '))}</span>` : 'Keine Verstöße gegen die Stilregeln';
const what = {
  credit: 'Freigeben bucht die Gutschrift in Odoo und sendet die Antwort.',
  replacement: 'Freigeben bestätigt den Ersatzauftrag in Odoo und sendet die Antwort.',
  need_info: 'Freigeben sendet die Rückfrage an den Kunden.',
  out_of_warranty: 'Freigeben sendet die Antwort an den Kunden.',
}[c.decision];

const html = mail(
  accent,
  kicker('Reklamation', esc(f.customer)) + verdict(esc(label)) + subline(sub) +
    (c.ext.summary ? para(esc(c.ext.summary), `color:${M.muted}`) : '') +
    facts(rows) + (odooLink ? link(odooLink, 'Entwurf in Odoo öffnen') : '') +
    (short
      ? section(`E-Mail des Kunden <span style="font-weight:400;color:${M.muted}">(${esc(c.mail.from_email)})</span>`) +
        quote(`Betreff: ${esc(c.mail.subject)}\n\n${esc(short)}`, `background:#ffffff;color:${M.muted};font-size:14px`)
      : '') +
    section(`Antwort an den Kunden <span style="font-weight:400;color:${M.muted}">(${esc(f.customer_email)})</span>`) +
    quote(`Betreff: ${esc(subject)}\n\n${esc(body)}`) +
    decided([['Regel', esc(c.reason)], ['KI', aiRow], ['Stilprüfung', styleRow]]) +
    buttons(
      [[`${resume}d=approve`, 'Freigeben und senden', 'primary'], [`${resume}d=reject`, 'Ablehnen', 'secondary']],
      `${what} Ablehnen ${c.draftId ? 'storniert den Entwurf in Odoo und ' : ''}sendet nichts an den Kunden. Ohne Klick passiert nichts.`,
    ),
);
const approvalSubject = `[Reklamation] ${label} · ${f.customer}${f.amount_eur && c.decision === 'credit' ? ' · ' + money(f.amount_eur) : ''}`;
return [{ json: { ...c, subject, body, approvalHtml: html, approvalSubject } }];
