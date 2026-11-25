// Node "Freigabe-Mail bauen": the approval e-mail to Accounts. Presentation only: every value and finding
// comes from the earlier nodes. Uses the helpers in shared/mail-layout.js.
const c = $('Rückfrage-Anfrage').first().json;
const i = c.inv;

// the supplier query the AI drafted (only for "abweichung"), with a quick check of the hardest style rules
let query = null;
if (c.wantQuery && $('KI schreibt Rückfrage').isExecuted) {
  const t = (aiText($('KI schreibt Rückfrage').first().json) || '').trim();
  const bad = /[—–]|\s--\s|zögern Sie nicht|erreicht Sie wohlbehalten|jederzeit (gerne )?zur Verfügung|\*\*/i.test(t);
  if (t && !t.startsWith('NO_FIXTURE')) {
    const [first, ...rest] = t.split('\n');
    query = { subject: first.replace(/^Betreff:\s*/i, '').trim(), body: rest.join('\n').replace(/^\s+/, ''), styleWarning: bad };
  }
}

const esc = v => String(v ?? '–').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const money = v => (v === null || v === undefined ? '–' : Number(v).toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €');
const resume = $execution.resumeUrl + ($execution.resumeUrl.includes('?') ? '&' : '?');
const R = true; // right-aligned cell
const tol = Number(c.settings.inv_price_tolerance_pct ?? 2);
const pct = v => `${v > 0 ? '+' : ''}${v.toFixed(1).replace('.', ',')} %`;

// one word per verdict, the same in the subject and the headline, then one short line
const short = { ok: 'Buchbar', abweichung: 'Abweichung', blockiert: 'Gestoppt' }[c.decision];
const n = c.checks.length;
const sub = {
  ok: 'Kann gebucht werden.',
  abweichung: `${n} ${n === 1 ? 'Punkt weicht' : 'Punkte weichen'} ab. ${query ? 'Die Rückfrage an den Lieferanten ist vorbereitet.' : 'Bitte prüfen.'}`,
  blockiert: 'Nicht buchen.',
}[c.decision];
const color = c.decision === 'blockiert' ? M.stop : M.ink;
const accent = { ok: M.ok, abweichung: M.look, blockiert: M.stop }[c.decision];

// 3-way match table: only the cell that breaks a rule is marked; matching rows stay plain
const mark = `background:${M.lookBg};font-weight:600;`;
const small = t => `<br><span style="font-weight:400;font-size:12px;color:${M.muted}">${t}</span>`;
const table = dataTable(
  th('Pos.', false, 'hide-s') + th('Artikel') + th('bestellt', R) + th('geliefert', R) + th('schon berechnet', R, 'hide-s') +
    th('diese Rechnung', R) + th('Preis Bestellung', R, 'hide-s') + th('Preis Rechnung', R),
  c.rows
    .map(r => {
      const priceOff = r.issues.some(t => t.startsWith('Preis'));
      const qtyOff = r.issues.some(t => t.startsWith('Menge'));
      const notOrdered = r.issues.includes('nicht bestellt');
      const open = r.received !== null && r.invoiced !== null ? r.received - r.invoiced : null;
      const qty = qtyOff ? esc(r.qty) + small(`offen ${esc(open)}`) : esc(r.qty);
      const price =
        (priceOff && r.po_price ? money(r.price) + small(pct(((r.price - r.po_price) / r.po_price) * 100)) : money(r.price)) +
        (r.po_price !== null ? `<span class="show-s" style="display:none;font-weight:400;font-size:12px;color:${M.muted}">Bestellung ${money(r.po_price)}</span>` : '');
      const item = `<span style="white-space:nowrap">${esc(r.code || r.text)}</span>` + (notOrdered ? small('nicht bestellt') : '');
      return '<tr>' + td(r.pos, false, '', 'hide-s') + td(item, false, notOrdered ? mark : '') + td(esc(r.ordered), R) + td(esc(r.received), R) +
        td(esc(r.invoiced), R, '', 'hide-s') + td(qty, R, qtyOff ? mark : '') + td(money(r.po_price), R, '', 'hide-s') + td(price, R, priceOff ? mark : '') + '</tr>';
    })
    .join(''),
);

// a stopped bank account: the invoice IBAN above the one stored in Odoo, in groups of four.
// The invoice IBAN is red; only the groups that differ are bold (and underlined when some groups match,
// because one or two changed digits are the easy ones to miss).
const clean = x => String(x || '').replace(/\s/g, '').toUpperCase();
const fraud = c.checks.some(x => x.fraud);
const banks = (($('Bankkonten lesen').isExecuted ? $('Bankkonten lesen').first().json.result : null) || [])
  .map(b => clean(b.acc_number))
  .filter(b => b && b !== i.supplier_iban);
const ibanLine = (v, other) => {
  const a = groups(v).split(' '), b = groups(other).split(' ');
  const off = a.map((g, k) => !!other && g !== b[k]), some = off.includes(false);
  const strong = g => `<span style="font-weight:700;${some ? 'text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px' : ''}">${g}</span>`;
  return a.map((g, k) => (off[k] ? strong(g) : g)).join(' ');
};
const ibanRow = (k, v) =>
  `<tr><td class="k" style="padding:8px 14px 8px 0;font-size:13px;font-weight:500;color:${M.muted};white-space:nowrap;vertical-align:top">${k}</td>` +
  `<td style="padding:8px 0;font-family:${M.mono};font-size:15px;letter-spacing:.02em;line-height:1.5">${v}</td></tr>`;
const supplierLink = c.supplier
  ? ` <a href="${ODOO_WEB}/odoo/action-account.res_partner_action_supplier/${c.supplier.id}" style="color:${M.ink};text-decoration:underline">Lieferant in Odoo öffnen</a>`
  : '';
const phone = c.supplier && c.supplier.phone
  ? `Rückruf unter der in Odoo gespeicherten Nummer: <b>${esc(c.supplier.phone)}</b>.`
  : 'In Odoo ist für diesen Lieferanten keine Telefonnummer hinterlegt. Nur eine schon bekannte Nummer verwenden, nicht die aus der Rechnung oder der E-Mail.';
const fraudBlock = fraud && i.supplier_iban
  ? `<div class="iban" style="margin:4px 0 18px;padding:14px 18px;background:${M.stopBg};border-left:3px solid ${M.stop};border-radius:0 4px 4px 0">\n` +
    '<table class="ib" role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse">' +
    ibanRow('IBAN auf der Rechnung', `<span style="color:${M.stop}">${ibanLine(i.supplier_iban, banks[0] || '')}</span>`) +
    (banks.length
      ? banks.map((b, k) => ibanRow(k ? '' : 'IBAN in Odoo', groups(b))).join('')
      : ibanRow('IBAN in Odoo', `<span style="font-family:${M.font};font-size:14px">keine andere hinterlegt</span>`)) +
    '</table>\n' +
    `<p style="margin:10px 0 0;font-size:14px;line-height:1.5;color:${M.ink}">${phone}${supplierLink}</p></div>`
  : '';
// when the IBAN block is shown, the bullet leaves the IBANs out (same finding, the values are in the block)
const checkText = x =>
  !(x.fraud && fraudBlock)
    ? x.text
    : x.text.startsWith('Bankverbindung weicht ab:')
      ? 'Bankverbindung weicht von Odoo ab. Nicht per E-Mail klären, beim Lieferanten unter der bekannten Telefonnummer nachfragen.'
      : x.text.replace(' ' + i.supplier_iban, '');
const findings = n
  ? `<ul class="checks" style="margin:14px 0 16px;padding:0 0 0 20px;font-size:15px;line-height:1.55;color:${color}">` +
    c.checks.map(x => `<li style="margin:0 0 4px">${x.fraud ? '<b>' : ''}${esc(checkText(x))}${x.fraud ? '</b>' : ''}</li>`).join('') +
    '</ul>'
  : `<p class="checks" style="margin:14px 0 16px;font-size:15px;line-height:1.55;color:${M.ink}">Bestellung, Wareneingang und Rechnung stimmen überein. Summen, USt-IdNr. und IBAN geprüft.</p>`;

const odoo = c.draftId ? link(`${ODOO_WEB}/odoo/action-account.action_move_in_invoice_type/${c.draftId}`, 'Rechnungsentwurf in Odoo öffnen') : '';
const readAi = $('Lese-Anfrage').isExecuted ? $('Lese-Anfrage').first().json.llm : null;
const ai = c.llm || readAi;
// name the query only when this mail contains one (c.llm can also be the read request carried along)
const aiUse = readAi && query ? 'hat die Rechnung gelesen und die Rückfrage entworfen' : readAi ? 'hat die Rechnung gelesen' : query ? 'hat die Rückfrage entworfen' : '';

// buttons: the expected next step is the filled one
const draftLabel = c.draftId ? 'Entwurf verwerfen' : 'Als erledigt markieren';
const canPost = c.draftId && c.decision !== 'blockiert';
const btns = [
  query ? [`${resume}d=query`, 'Rückfrage an Lieferanten senden', 'primary'] : null,
  canPost ? [`${resume}d=post`, 'Buchen', c.decision === 'ok' ? 'primary' : 'secondary'] : null,
  [`${resume}d=reject`, draftLabel, canPost || query ? 'text' : 'secondary'],
];
const after = [
  query ? `Rückfrage sendet den Entwurf oben an ${esc(c.supplier.email)}; die Rechnung bleibt als Entwurf offen.` : null,
  canPost ? 'Buchen bucht die Rechnung in Odoo.' : null,
  c.draftId ? 'Entwurf verwerfen storniert den Entwurf in Odoo.' : 'Als erledigt markieren bucht nichts, es wird nur vermerkt.',
  'Ohne Klick passiert nichts.',
].filter(Boolean).join(' ');

const html = mail(
  accent,
  kicker('Eingangsrechnung', esc(i.supplier_name)) + verdict(esc(short), color) + subline(sub) + findings + fraudBlock +
    facts([
      ['Rechnung', `<b>${esc(i.invoice_number)}</b>${i.invoice_date ? ` vom ${deDate(i.invoice_date)}` : ''}${i.due_date ? ` <span style="color:${M.muted}">· fällig ${deDate(i.due_date)}</span>` : ''}`],
      ['Betrag', `<b>${money(i.gross_total)}</b> <span style="color:${M.muted}">brutto · netto ${money(i.net_total)} · USt ${money(i.vat_amount)}</span>`],
      ['Bestellung', esc(c.po ? c.po.name : i.po_ref || 'keine')],
    ]) +
    (c.poNote ? note(esc(c.poNote)) : '') +
    (c.rows.length ? table : '') + odoo +
    (query
      ? section(`Entwurf der Rückfrage an ${esc(c.supplier.email)}${query.styleWarning ? ` <span style="color:${M.stop}">(Stilregeln verletzt, bitte prüfen)</span>` : ''}`) +
        quote(`Betreff: ${esc(query.subject)}\n\n${esc(query.body)}`)
      : '') +
    decided([
      ['Preistoleranz', `${String(tol).replace('.', ',')} % (aus den Einstellungen)`],
      ['Feste Prüfungen', 'Summen, USt-IdNr., IBAN, Dubletten, Bankverbindung'],
      ['Gelesen', esc(c.readBy)],
      ai ? ['KI', `${esc(ai.label)} · ${ai.local ? 'lokal, keine Daten nach außen' : 'Cloud: Rechnungsdaten gingen an diesen Anbieter'}${aiUse ? ` · ${aiUse}` : ''}`] : null,
      ['Datei', esc(c.mail.filename)],
    ]) +
    buttons(btns, after),
);
const approvalSubject = `[Eingangsrechnung] ${short} · ${i.supplier_name} · ${i.invoice_number} · ${money(i.gross_total)}`;
return [{ json: { ...c, query, approvalHtml: html, approvalSubject } }];
