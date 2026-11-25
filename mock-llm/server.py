"""Stand-in for a local language model, OpenAI-compatible (POST /v1/chat/completions).

The workflow talks to it exactly as it would talk to Ollama (http://ollama:11434/v1). Each
request is saved to requests/<case>.<task>.json; the answer is read from the prepared file
fixtures/<case>.<task>.txt (case = the MESSAGE-ID in the prompt, task = its "TASK:" line).
The answers are prepared in advance, so this tests the workflow around the AI, not the AI.
It also answers in the Anthropic Messages format. Pick a real model in the settings instead.
"""
import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
FIX, REQ = ROOT / "fixtures", ROOT / "requests"
REQ.mkdir(exist_ok=True)


def answer(body):
    msgs = body.get("messages", [])
    text = str(body.get("system", "")) + "\n" + "\n".join(m.get("content", "") if isinstance(m.get("content"), str) else json.dumps(m.get("content")) for m in msgs)
    task = (re.search(r"TASK:\s*([a-z_]+)", text) or [None, "unknown"])[1]
    case = (re.search(r"MESSAGE-ID:\s*([\w.-]+)", text) or [None, "unknown"])[1]
    stamp = time.strftime("%H%M%S")
    (REQ / f"{case}.{task}.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    f = FIX / f"{case}.{task}.txt"
    content = f.read_text(encoding="utf-8").strip() if f.exists() else f"NO_FIXTURE {case}.{task}"
    print(stamp, case, task, "fixture" if f.exists() else "missing", flush=True)
    return content


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, {"object": "list", "data": [{"id": "local-model", "object": "model"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        content = answer(body)
        if self.path.rstrip("/").endswith("/messages"):  # Anthropic Messages API format
            return self._send(200, {"id": "mock", "type": "message", "role": "assistant", "model": body.get("model"),
                                    "content": [{"type": "text", "text": content}], "stop_reason": "end_turn",
                                    "usage": {"input_tokens": 0, "output_tokens": 0}})
        self._send(200, {"id": "mock", "object": "chat.completion", "created": int(time.time()), "model": body.get("model", "local-model"),
                         "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
                         "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})

    def log_message(self, *a):
        pass


ThreadingHTTPServer(("0.0.0.0", 8099), H).serve_forever()
