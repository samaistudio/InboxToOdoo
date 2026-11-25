// Node "Formular vorbereiten": builds the fields of settings page 2 from the stored settings.
// - Dropdowns start on "<value in use> (aktuell)". The save step has no mapping for that option, so the stored value is kept.
// - Text, number and e-mail fields are filled with the value in use, so saving without a change writes the same value back.
// - Fields marked prefill: false stay empty and the placeholder says what is in use: the AI model and address (empty =
//   keep, or the new provider's default) and the multi-line fields (a browser would send their line breaks as CRLF).
//   Careful: an empty "Eigene Regeln" clears the company's rules; its placeholder says so.
// Labels stay as they are: the save step reads the answers by label.
const s = $('Einstellungen').first().json.data || {};
const KEEP = 'Unverändert lassen';
const shown = f => {
  const v = s[f.key];
  const t = v === undefined || v === null || v === '' ? '' : String((f.labels || {})[v] ?? v).replace(/\s*\n\s*/g, ' · ');
  return t || f.empty || 'nicht gesetzt';
};
const fields = /*FIELDS*/[].flatMap(f => {
  if (!f.key) return [f];
  const { key, labels, empty, prefill, hint, ...o } = f;
  const cur = shown(f);
  if (o.fieldType === 'dropdown') {
    const k = `${cur} (aktuell)`;
    const values = o.fieldOptions.values.filter(v => v.option !== cur).map(v => (v.option === KEEP ? { option: k } : v));
    return [{ ...o, fieldOptions: { values }, defaultValue: k }];
  }
  if (prefill === false) return [{ ...o, placeholder: `${hint || 'leer = wie bisher'} · jetzt: ${cur}` }];
  const v = s[key];
  return [{ ...o, defaultValue: v === undefined || v === null ? '' : v }];
});
return [{ json: { fields } }];
