const f = $('/*FORM*/').first().json;
const old = $('Einstellungen').first().json.data;
const pick = (v, d) => (v === undefined || v === null || v === '') ? d : v;
const map = { 'Sprache des Kunden übernehmen': 'auto', 'Immer Deutsch': 'de', 'Immer Englisch (US)': 'en-US',
  'Sie': 'Sie', 'du': 'du', 'Wie der Kunde': 'auto', 'sachlich': 'sachlich', 'freundlich': 'freundlich', 'herzlich': 'herzlich',
  'kurz': 'short', 'normal': 'normal', 'ausführlich': 'detailed', 'Nur wenn wir schuld sind': 'when_our_fault', 'Immer': 'always', 'Nie': 'never',
  'Ersatzlieferung': 'replacement', 'Gutschrift': 'credit',
  'Testmodell (offline)': 'mock', 'Wie in Odoo eingerichtet': 'odoo', 'Ollama (lokal)': 'ollama', 'LM Studio (lokal)': 'lmstudio', 'OpenAI': 'openai',
  'Anthropic Claude': 'anthropic', 'Google Gemini': 'gemini', 'Mistral': 'mistral', 'Azure OpenAI': 'azure', 'Eigener Endpunkt': 'custom' };
const s = { ...old,
  language: map[f['Sprache der Antwort']] ?? old.language, formality: map[f['Anrede']] ?? old.formality, tone: map[f['Ton']] ?? old.tone,
  length: map[f['Länge']] ?? old.length, apology: map[f['Entschuldigung']] ?? old.apology,
  closing_de: pick(f['Grußformel Deutsch'], old.closing_de), closing_en: pick(f['Grußformel Englisch'], old.closing_en),
  signature: pick(f['Signatur'], old.signature), custom_rules: f['Eigene Regeln'] ?? old.custom_rules,
  default_remedy: map[f['Standardlösung bei Defekt']] ?? old.default_remedy,
  warranty_months_b2c: Number(pick(f['Gewährleistung Privatkunden (Monate)'], old.warranty_months_b2c)),
  warranty_months_b2b: Number(pick(f['Gewährleistung Firmenkunden (Monate)'], old.warranty_months_b2b)),
  approval_email: pick(f['Freigabe an (E-Mail)'], old.approval_email),
  llm_provider: map[f['KI-Anbieter']] ?? old.llm_provider };
const newProvider = s.llm_provider !== old.llm_provider;
s.llm_model = pick(f['KI-Modell'], newProvider ? '' : old.llm_model);
s.llm_url = pick(f['KI-Adresse (nur Azure, eigener Endpunkt oder entfernter Ollama)'], newProvider ? '' : old.llm_url);
return [{ json: s, binary: { data: { data: Buffer.from(JSON.stringify(s, null, 1)).toString('base64'), mimeType: 'application/json', fileName: 'settings.json' } } }];
