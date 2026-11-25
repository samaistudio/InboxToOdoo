// Reads the text out of an answer in OpenAI format (choices) or Anthropic format (content blocks).
const aiText = j => (j.choices?.[0]?.message?.content ?? (j.content || []).map(b => b.text || '').join('') ?? '');
