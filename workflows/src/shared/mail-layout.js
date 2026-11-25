// One look for every approval e-mail: light, inline styles, a table shell, no script.
// Warm near-black ink, one hairline, 4px corners, one width, a coloured top edge per verdict,
// one filled button for the expected next step. A small <style> block only adapts it to phones.
const M = {
  ink: '#1d1c1a', muted: '#5c5a55', line: '#e2e0db', soft: '#f6f5f2', page: '#efeeea',
  ok: '#24663b', look: '#8f8230', stop: '#a3231a', neutral: '#77746d', lookBg: '#f4efd4', stopBg: '#f9e5e2',
  font: "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif",
  mono: 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace',
};

const MAIL_CSS = [
  '@media (max-width:600px){',
  '.page{padding:12px 6px!important}.pad{padding:22px 14px 26px!important}.iban{padding:12px 12px!important}',
  '.hide-s{display:none!important}.show-s{display:block!important}',
  '.btn{display:block!important;margin:0 0 10px!important;text-align:center!important}',
  'table.ib td{display:block!important;padding:2px 0!important}table.ib td.k{padding-top:8px!important}',
  'table.kv td{display:block!important;width:auto!important;padding:0!important;border:0!important}table.kv td.k{padding-top:10px!important}',
  `table.kv tr td.v{padding-bottom:10px!important;border-bottom:1px solid ${M.line}!important}`,
  'table.data td,table.data th{font-size:13px!important;padding-right:6px!important}}',
].join('\n');

const mail = (accent, inner) =>
  '<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
  `<style>${MAIL_CSS}</style></head>\n` +
  `<body style="margin:0;padding:0;background:${M.page}">` +
  `<div class="page" style="margin:0;padding:24px 12px;background:${M.page};font-family:${M.font};color:${M.ink};-webkit-text-size-adjust:100%">\n` +
  '<table class="shell" role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" ' +
  `style="max-width:680px;margin:0 auto;background:#ffffff;border:1px solid ${M.line};border-top:4px solid ${accent};border-radius:4px;border-collapse:separate">\n` +
  `<tr><td class="pad" style="padding:28px 32px 32px;font-family:${M.font};font-size:15px;line-height:1.55;color:${M.ink}">${inner}</td></tr></table></div></body></html>`;

// small line above the headline: "Eingangsrechnung · Supplier"
const kicker = (flow, who) =>
  `<p style="margin:0 0 6px;font-size:13px;line-height:1.4;color:${M.muted}"><span style="font-weight:600;color:${M.ink}">${flow}</span>${who ? ' · ' + who : ''}</p>`;
// the verdict: the same word as in the subject, then one short line that says what it means
const verdict = (t, color) =>
  `<h1 class="verdict" style="margin:0 0 4px;font-size:22px;line-height:1.3;font-weight:600;color:${color || M.ink}">${t}</h1>`;
const subline = t => `<p class="subline" style="margin:0 0 12px;font-size:15px;line-height:1.5;color:${M.ink}">${t}</p>`;
const para = (t, extra) => `<p style="margin:0 0 12px;font-size:15px;line-height:1.55;color:${M.ink};${extra || ''}">${t}</p>`;
const note = t => `<p style="margin:0 0 8px;font-size:13px;line-height:1.5;color:${M.muted}">${t}</p>`;
const section = t => `<h2 style="margin:28px 0 10px;font-size:15px;line-height:1.4;font-weight:600;color:${M.ink}">${t}</h2>`;
const link = (href, t) => `<p style="margin:14px 0 0;font-size:15px"><a href="${href}" style="color:${M.ink};text-decoration:underline">${t}</a></p>`;
const quote = (t, extra) =>
  `<pre style="margin:0;white-space:pre-wrap;word-wrap:break-word;font-family:${M.font};font-size:15px;line-height:1.55;color:${M.ink};` +
  `background:${M.soft};border:1px solid ${M.line};border-radius:4px;padding:16px 20px;${extra || ''}">${t}</pre>`;

// tables: th / td cells, a data table with a header row, and label / value rows ("facts")
const th = (t, right, cls) =>
  `<th${cls ? ` class="${cls}"` : ''} style="padding:8px 12px 8px 0;border-bottom:1px solid ${M.ink};font-size:13px;font-weight:500;` +
  `color:${M.muted};text-align:${right ? 'right' : 'left'};vertical-align:bottom">${t}</th>`;
const td = (t, right, extra, cls) =>
  `<td${cls ? ` class="${cls}"` : ''} style="padding:9px 12px 9px 0;border-bottom:1px solid ${M.line};font-size:14px;` +
  `text-align:${right ? 'right' : 'left'};${right ? 'white-space:nowrap;' : ''}${extra || ''}">${t}</td>`;
const dataTable = (head, rows) =>
  '<table class="data" role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" ' +
  `style="border-collapse:collapse;margin:16px 0 4px;font-family:${M.font};color:${M.ink}">${head ? `<tr>${head}</tr>` : ''}${rows}</table>`;
// rows without a value are left out instead of printing a dash
const facts = (rows, cls) =>
  `<table class="kv${cls ? ' ' + cls : ''}" role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" ` +
  `style="border-collapse:collapse;margin:16px 0 4px;font-family:${M.font};color:${M.ink}">` +
  rows
    .filter(r => r && r[1] !== null && r[1] !== undefined && r[1] !== '')
    .map(([k, v]) =>
      `<tr><td class="k" style="width:150px;padding:9px 12px 9px 0;border-bottom:1px solid ${M.line};font-size:13px;font-weight:500;color:${M.muted};vertical-align:top">${k}</td>` +
      `<td class="v" style="padding:9px 0;border-bottom:1px solid ${M.line};font-size:14px;line-height:1.5;vertical-align:top">${v}</td></tr>`)
    .join('') +
  '</table>';
const decided = rows => section('Wie entschieden wurde') + facts(rows, 'how');

// buttons: [href, label, kind] with kind 'primary' (filled), 'secondary' (outlined) or 'text' (plain link)
const button = ([href, t, kind]) =>
  kind === 'text'
    ? `<a class="btn" href="${href}" style="display:inline-block;margin:0 8px 8px 4px;padding:11px 4px;color:${M.ink};font-family:${M.font};font-size:15px;line-height:1.2;text-decoration:underline">${t}</a>`
    : `<a class="btn" href="${href}" style="display:inline-block;margin:0 8px 8px 0;padding:12px 20px;border:1px solid ${M.ink};border-radius:4px;` +
      `background:${kind === 'primary' ? M.ink : '#ffffff'};color:${kind === 'primary' ? '#ffffff' : M.ink};font-family:${M.font};font-size:15px;font-weight:600;line-height:1.2;text-decoration:none">${t}</a>`;
const buttons = (list, after) =>
  `<div class="actions" style="margin-top:28px">${list.filter(Boolean).map(button).join('')}` +
  (after ? `<p style="margin:10px 0 0;font-size:13px;line-height:1.5;color:${M.muted}">${after}</p>` : '') +
  '</div>';

const deDate = iso => (iso ? String(iso).slice(0, 10).split('-').reverse().join('.') : null);
const groups = s => String(s || '').replace(/\s/g, '').toUpperCase().replace(/(.{4})/g, '$1 ').trim();
// Odoo is linked at the address the person opens in the browser (ODOO_PUBLIC_URL in .env.local, default localhost)
const ODOO_WEB = String($env.ODOO_PUBLIC_URL || 'http://localhost:8069').replace(/\/+$/, '');
