"""Clicks a button in the newest approval mail whose subject contains TEXT. Run: python3 test/click.py "RE-2026-1187" post|query|reject|approve"""
import html, json, re, sys, urllib.request
text, action = sys.argv[1], sys.argv[2]
msgs = json.load(urllib.request.urlopen("http://localhost:8025/api/v1/messages?limit=100"))["messages"]
m = next(m for m in msgs if text in m["Subject"] and m["Subject"].startswith("["))
full = json.load(urllib.request.urlopen(f"http://localhost:8025/api/v1/message/{m['ID']}"))
url = next(html.unescape(u) for u in re.findall(r'href="([^"]+)"', full["HTML"]) if u.endswith("d=" + action))
print(action, m["Subject"], urllib.request.urlopen(url).status)
