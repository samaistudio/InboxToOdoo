// Headless Chrome over the DevTools protocol: opens each page, measures the highlighted parts,
// saves a 2x screenshot cut to the page height. Reads the step list as JSON on stdin.
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const outDir = process.argv[2];
const steps = JSON.parse(await new Promise(r => { let d = ""; process.stdin.on("data", c => d += c); process.stdin.on("end", () => r(d)); }));
const port = 9400 + Math.floor(Math.random() * 400);
const chrome = spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ["--headless=new", `--remote-debugging-port=${port}`, "--user-data-dir=" + mkdtempSync(join(tmpdir(), "cap-")), "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let target; for (let i = 0; i < 60 && !target; i++) { await sleep(250); try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === "page"); } catch {} }
const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
let id = 0; const w = {}; ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && w[m.id]) w[m.id](m.result); };
const send = (method, params = {}) => new Promise(r => { w[++id] = r; ws.send(JSON.stringify({ id, method, params })); });
const js = async e => (await send("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true })).result?.value;
await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "light" }] });
const result = {};
let loggedIn = false;
for (const s of steps) {
  await send("Emulation.setDeviceMetricsOverride", { width: s.w, height: s.h, deviceScaleFactor: 2, mobile: false });
  if (s.login && !loggedIn) {
    await send("Page.navigate", { url: "http://localhost:8069/web/login" }); await sleep(2500);
    await js(`fetch('/web/session/authenticate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',params:{db:${JSON.stringify(process.env.ODOO_DB)},login:${JSON.stringify(process.env.ODOO_USER)},password:${JSON.stringify(process.env.ODOO_PASSWORD)}}})}).then(r=>r.json())`);
    loggedIn = true;
  }
  await send("Page.navigate", { url: s.url }); await sleep(s.wait || 1500);
  // optional step before the shot, e.g. opening page 2 of a form
  if (s.pre) { await js(s.pre); await sleep(s.preWait || 3500); }
  const docH = await js("Math.min(Math.max(...[...document.body.children].map(e => e.getBoundingClientRect().bottom)) + 28, " + s.h + ")");
  // a note's JS returns one rect [x, y, w, h] or several [[x, y, w, h], ...]; several are kept as parts, with their union as the rect
  const rects = [], parts = [];
  for (const r of s.rects) {
    let v = await js(r) || [0, 0, 0, 0];
    const many = Array.isArray(v[0]) ? v : null;
    if (many) { const L = Math.min(...many.map(q => q[0])), T = Math.min(...many.map(q => q[1])), R = Math.max(...many.map(q => q[0] + q[2])), B = Math.max(...many.map(q => q[1] + q[3])); v = [L, T, R - L, B - T]; }
    rects.push(v); parts.push(many);
  }
  // optional crop (e.g. without an app's sidebar): [x, y, w, h]; rects are moved into the crop
  const c = s.clip ? await js(s.clip) : null;
  if (c) for (const r of [...rects, ...parts.flat().filter(Boolean)]) { r[0] -= c[0]; r[1] -= c[1]; }
  const h = c ? Math.ceil(c[3]) : Math.ceil(Math.max(...rects.map(r => r[1] + r[3] + 30), docH));
  const W = c ? Math.ceil(c[2]) : s.w;
  const { data } = await send("Page.captureScreenshot", { format: "png", clip: { x: c ? c[0] : 0, y: c ? c[1] : 0, width: W, height: Math.min(h, s.h), scale: 1 } });
  writeFileSync(join(outDir, s.name + ".png"), Buffer.from(data, "base64"));
  result[s.name] = { w: W, h: Math.min(h, s.h), rects, parts };
}
console.log(JSON.stringify(result));
chrome.kill(); process.exit(0);
