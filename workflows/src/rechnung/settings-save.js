// Node "Neue Einstellungen" (invoice settings form): empty fields keep the stored value.
const f = $('/*FORM*/').first().json;
const old = $('Einstellungen').first().json.data;
const pick = (v, d) => (v === undefined || v === null || v === '' ? d : v);
const s = {
  ...old,
  inv_price_tolerance_pct: Number(pick(f['Preistoleranz (%)'], old.inv_price_tolerance_pct ?? 2)),
  inv_approval_email: pick(f['Freigabe an (E-Mail der Buchhaltung)'], old.inv_approval_email),
  inv_mailbox: pick(f['Rechnungs-Postfach'], old.inv_mailbox),
  inv_signature: pick(f['Signatur für Rückfragen'], old.inv_signature),
};
const file = { data: Buffer.from(JSON.stringify(s, null, 1)).toString('base64'), mimeType: 'application/json', fileName: 'settings.json' };
return [{ json: s, binary: { data: file } }];
