// Node "Protokollzeile": one JSON line per invoice in data/log.jsonl.
const c = $('Abschluss vorbereiten').first().json;
const entry = {
  at: new Date().toISOString(), kind: 'eingangsrechnung', id: c.id, supplier: c.inv.supplier_name, invoice: c.inv.invoice_number,
  gross: c.inv.gross_total, po: c.po ? c.po.name : null, decision: c.decision, action: c.d, bill: c.draftId,
  checks: c.checks.map(x => x.level + ': ' + x.text),
};
const line = JSON.stringify(entry) + '\n';
return [{ json: { line }, binary: { data: { data: Buffer.from(line).toString('base64'), mimeType: 'application/json', fileName: 'log.jsonl' } } }];
