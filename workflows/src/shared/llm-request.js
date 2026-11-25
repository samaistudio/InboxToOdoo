// One function builds the HTTP request for whichever AI the company chose in the settings.
// Keys come from the environment (.env.local) or, for "odoo", from the AI keys already stored in Odoo.
// Every provider gets the same prompts; only the request format differs (OpenAI, Anthropic or Azure).
const PROVIDERS = {
  mock:      { label: 'Testmodell (offline)', url: 'http://mock-llm:8099/v1', fmt: 'openai', local: true },
  ollama:    { label: 'Ollama (lokal)', url: 'http://host.docker.internal:11434/v1', fmt: 'openai', local: true, model: 'qwen2.5:7b' },
  lmstudio:  { label: 'LM Studio (lokal)', url: 'http://host.docker.internal:1234/v1', fmt: 'openai', local: true },
  openai:    { label: 'OpenAI', url: 'https://api.openai.com/v1', fmt: 'openai', env: 'OPENAI_API_KEY', model: 'gpt-4o-mini' },
  anthropic: { label: 'Anthropic Claude', url: 'https://api.anthropic.com/v1', fmt: 'anthropic', env: 'ANTHROPIC_API_KEY', model: 'claude-haiku-5-5' },
  gemini:    { label: 'Google Gemini', url: 'https://generativelanguage.googleapis.com/v1beta/openai', fmt: 'openai', env: 'GEMINI_API_KEY',
               model: 'gemini-2.5-flash' },
  mistral:   { label: 'Mistral', url: 'https://api.mistral.ai/v1', fmt: 'openai', env: 'MISTRAL_API_KEY', model: 'mistral-small-latest' },
  azure:     { label: 'Azure OpenAI', url: '', fmt: 'azure', env: 'AZURE_OPENAI_API_KEY' },
  custom:    { label: 'Eigener Endpunkt', url: '', fmt: 'openai', env: 'LLM_API_KEY' },
};

// "Wie in Odoo eingerichtet": find an AI key among the Odoo system parameters listed in the settings
function odooAiKey(s) {
  const rows = ($('KI aus Odoo lesen').first().json.result || []).filter(r => r.value);
  const prefer = s.odoo_ai_prefer || 'openai';
  const kind = r => (/openai/i.test(r.key) ? 'openai' : /google|gemini/i.test(r.key) ? 'gemini' : /anthropic|claude/i.test(r.key) ? 'anthropic' : null);
  const found = rows.map(r => ({ provider: kind(r), key: r.value, param: r.key })).filter(r => r.provider);
  return found.find(r => r.provider === prefer) || found[0] || null;
}

function llmRequest(s, system, user, temperature) {
  let p = s.llm_provider || 'mock', key = null, from = null;
  if (p === 'odoo') {
    const hit = odooAiKey(s);
    if (!hit)
      throw new Error(
        'In Odoo ist kein KI-Schlüssel hinterlegt (gesucht: ' + (s.odoo_ai_params || []).join(', ') + '). ' +
          'Bitte in den Einstellungen einen anderen KI-Anbieter wählen.',
      );
    p = hit.provider;
    key = hit.key;
    from = 'Odoo (' + hit.param + ')';
  }
  const P = PROVIDERS[p];
  if (!P) throw new Error('Unbekannter KI-Anbieter: ' + p);
  const base = String(s.llm_url || P.url).replace(/\/+$/, '');
  if (!base) throw new Error('Für ' + P.label + ' fehlt die Adresse (URL) in den Einstellungen.');
  key = key || (P.env ? $env[P.env] || $env.LLM_API_KEY : null) || null;
  if (P.env && !key) throw new Error('Für ' + P.label + ' fehlt der API-Schlüssel ' + P.env + ' in .env.local.');
  const model = (from ? s.odoo_ai_model || P.model : s.llm_model) || P.model || 'local-model';
  let url, body;
  const headers = { 'Content-Type': 'application/json' };
  if (P.fmt === 'anthropic') {
    url = base + '/messages';
    headers['x-api-key'] = key;
    headers['anthropic-version'] = '2023-06-01';
    body = { model, max_tokens: 1500, temperature, system, messages: [{ role: 'user', content: user }] };
  } else {
    url = P.fmt === 'azure'
      ? `${base}/openai/deployments/${encodeURIComponent(model)}/chat/completions?api-version=${s.azure_api_version || '2024-10-21'}`
      : base + '/chat/completions';
    if (key) {
      if (P.fmt === 'azure') headers['api-key'] = key;
      else headers['Authorization'] = 'Bearer ' + key;
    }
    body = { model, temperature, messages: [{ role: 'system', content: system }, { role: 'user', content: user }] };
  }
  return { url, headers, body, provider: p, label: P.label + (from ? ', Schlüssel aus ' + from : ''), model, local: !!P.local };
}
