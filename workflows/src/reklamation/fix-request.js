// Node "Korrektur-Anfrage": a reply that broke a style rule goes back to the AI once, with the problems named.
const c = $json;
const system =
  'TASK: fix_style\nÜberarbeite die E-Mail so, dass diese Probleme verschwinden. Ändere keine Fakten, Beträge, Daten oder Namen. ' +
  'Gib nur die fertige E-Mail zurück.\n\nStilleitfaden:\n' + c.style;
const user = `MESSAGE-ID: ${c.id}\nProbleme: ${c.problems.join('; ')}\n\n${c.reply}`;
return [{ json: { ...c, llm: llmRequest(c.settings, system, user, 0.2) } }];
