// Node "Protokollzeile": one JSON line per complaint in data/log.jsonl.
const c = $('Abschluss vorbereiten').first().json;
const entry = {
  at: new Date().toISOString(), id: c.id, customer: c.facts.customer, order: c.facts.order, decision: c.decision,
  approved: c.approved, draft: c.draft ? c.draft.model + ':' + c.draftId : null, amount_eur: c.facts.amount_eur, style_fixed: !!c.fixed,
};
const line = JSON.stringify(entry) + '\n';
return [{ json: { line }, binary: { data: { data: Buffer.from(line).toString('base64'), mimeType: 'application/json', fileName: 'log.jsonl' } } }];
