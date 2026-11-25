// Node "Lese-Anfrage": the HTTP request for the AI that reads the complaint (llmRequest from shared/llm-request.js).
const ctx = $('Kontext').first().json;
const llm = llmRequest(ctx.settings, ctx.extractPrompt.system, ctx.extractPrompt.user, 0);
return [{ json: { ...ctx, llm } }];
