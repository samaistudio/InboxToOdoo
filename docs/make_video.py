"""Builds the 43-second product video (docs/assets/inboxtoodoo.mp4, no sound) and its poster from the walkthrough
screenshots: a title card, one frame per walkthrough note, an end card. Every frame is docs/frame.html in headless Chrome.
Needs: python3 docs/make_tutorial.py has run (assets/tutorial.json), Google Chrome (set CHROME if it is not the macOS
default) and ffmpeg. Run: python3 docs/make_video.py"""
import functools
import http.server
import json
import os
import subprocess
import tempfile
import threading
from pathlib import Path

DOCS = Path(__file__).resolve().parent
ASSETS = DOCS / "assets"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
TITLE, NOTE, END = 3.0, 1.75, 3.0  # seconds on screen


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_address[1]}/frame.html"


def shoot(query, out):
    subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--window-size=1920,1080", "--virtual-time-budget=4000",
                    f"--screenshot={out}", f"{base}?{query}"], check=True, capture_output=True)


steps = json.loads((ASSETS / "tutorial.json").read_text(encoding="utf-8"))
frames = [("k=title", TITLE)] + [(f"s={i}&n={k}", NOTE) for i, s in enumerate(steps) for k in range(len(s["notes"]))] + [("k=end", END)]
total = TITLE + END + NOTE * (len(frames) - 2)
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    lines = []
    for n, (query, secs) in enumerate(frames):
        png = tmp / f"f{n:02d}.png"
        shoot(query, png)
        lines += [f"file '{png}'", f"duration {secs}"]
    lines.append(f"file '{tmp / f'f{len(frames) - 1:02d}.png'}'")  # the concat demuxer needs the last file twice
    (tmp / "list.txt").write_text("\n".join(lines) + "\n")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"),
                    "-t", f"{total:.2f}", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart", "-an",
                    str(ASSETS / "inboxtoodoo.mp4")], check=True)
# poster: the price-difference mail from step 3, plain (no highlight, no caption)
shoot("s=2&n=0&nocap&clean", ASSETS / "poster.png")
server.shutdown()
print(f"wrote inboxtoodoo.mp4 ({len(frames)} frames, {total:.0f} s) and poster.png")
