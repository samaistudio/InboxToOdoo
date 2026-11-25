"""Post one test case straight to the complaint webhook (skips the inbox step). Run: python3 test/send_webhook.py test-01"""
import json, sys, urllib.request, importlib.util
spec = importlib.util.spec_from_file_location("c", __file__.replace("send_webhook.py", "complaints.py"))
src = open(spec.origin, encoding="utf-8").read().split("pick =")[0]
ns = {}; exec(src, ns)
for cid in sys.argv[1:]:
    n, a, s, t = ns["CASES"][cid]
    body = json.dumps({"message_id": f"<{cid}@rheinmark-handel.example>", "from_email": a, "from_name": n, "subject": s, "text": t}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://localhost:5678/webhook/reklamation", body, {"Content-Type": "application/json"}))
    print(cid, r.read().decode())
