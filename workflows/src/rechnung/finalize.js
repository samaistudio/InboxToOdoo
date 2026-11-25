// Node "Abschluss vorbereiten": what the click in the approval mail means (d = post | query | reject).
// A stopped invoice ("blockiert") is never posted, even if someone calls the post link by hand.
const c = $('Freigabe-Mail bauen').first().json;
const d = $json.query?.d || 'reject';
let call = null;
if (c.draftId && d === 'post' && c.decision !== 'blockiert') call = { model: 'account.move', method: 'action_post', args: [[c.draftId]] };
if (c.draftId && d === 'reject') call = { model: 'account.move', method: 'button_cancel', args: [[c.draftId]] };
const label = {
  post: 'gebucht',
  query: 'Rückfrage an den Lieferanten gesendet, Entwurf bleibt offen',
  reject: c.draftId ? 'Entwurf verworfen' : 'als erledigt markiert',
}[d];
const note = `Eingangsrechnung ${c.inv.invoice_number} (${c.id}): ${label}. ${c.checks.map(x => x.text).join(' ')}`.trim();
const target = c.draftId ? { model: 'account.move', id: c.draftId } : c.po ? { model: 'purchase.order', id: c.po.id } : null;
return [{ json: { ...c, d, call, note, target, sendQuery: d === 'query' && !!c.query } }];
