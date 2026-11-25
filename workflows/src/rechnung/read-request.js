// Node "Lese-Anfrage": the HTTP request for the AI that reads a PDF or scan (llmRequest from shared/llm-request.js).
const c = $('Kontext').first().json;
return [{ json: { ...c, llm: llmRequest(c.settings, c.extractPrompt.system, c.extractPrompt.user, 0) } }];
