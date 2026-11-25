// Node "Abschluss vorbereiten": what the click means. Approve books the draft (credit note posted,
// replacement order confirmed); reject cancels it. The note goes on the order in Odoo.
const c = $('Freigabe-Mail bauen').first().json;
const approved = ($json.query?.d || $json.d) === 'approve';
let call = null;
if (c.draftId && c.draft) {
  const isOrder = c.draft.model === 'sale.order';
  const method = approved ? (isOrder ? 'action_confirm' : 'action_post') : isOrder ? 'action_cancel' : 'button_cancel';
  call = { model: c.draft.model, method, args: [[c.draftId]] };
}
const de = { credit: 'Gutschrift', replacement: 'Ersatzlieferung', need_info: 'Rückfrage', out_of_warranty: 'Ablehnung (außerhalb Gewährleistung)' }[c.decision];
const note = `Reklamation ${c.id}: ${de} ${approved ? 'freigegeben' : 'abgelehnt'}. ${c.reason}`;
return [{ json: { ...c, approved, call, note } }];
