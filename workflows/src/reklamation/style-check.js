// Node "Stilprüfung": checks the AI's reply against the hard writing rules (styleProblems from rules/reply-style.js).
const c = $('Antwort-Anfrage').first().json;
const text = (aiText($json) || '').trim();
return [{ json: { ...c, reply: text, problems: styleProblems(text) } }];
