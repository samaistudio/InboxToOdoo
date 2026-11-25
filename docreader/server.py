"""Local document reader for incoming invoices. POST the raw file to /read?filename=... and get JSON back.

What it returns, most reliable first:
  1. German e-invoice (XRechnung XML, UBL or CII)       -> "einvoice": the workflow hands the file to Odoo's own importer
  2. PDF with an embedded e-invoice (ZUGFeRD/Factur-X)  -> "einvoice", same
  3. PDF with a text layer                              -> "pdf-text": the text, for the AI
  4. Scanned PDF or image                               -> "ocr": Tesseract (German + English) text, for the AI
Odoo Community reads e-invoices itself; OCR is the part it lacks (Odoo's digitisation is a paid Enterprise service).
Everything runs inside this container; nothing is sent anywhere.
"""
import base64
import io
import json
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pypdf import PdfReader

EMBEDDED_NAMES = ("factur-x.xml", "zugferd-invoice.xml", "xrechnung.xml", "zugferd.xml")


def einvoice_kind(xml_bytes):
    """Only recognises the format. Reading the content is Odoo's job (module account_edi_ubl_cii)."""
    head = xml_bytes[:4000].decode("utf-8", "ignore")
    if "CrossIndustryInvoice" in head:
        return "cii"
    if "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" in head or "<Invoice" in head:
        return "ubl"
    return None


def ocr(images_dir):
    texts = []
    for img in sorted(Path(images_dir).glob("*.png")) + sorted(Path(images_dir).glob("*.jpg")) + sorted(Path(images_dir).glob("*.tif*")):
        r = subprocess.run(["tesseract", str(img), "-", "-l", "deu+eng", "--psm", "6"], capture_output=True, text=True, timeout=120)
        texts.append(r.stdout)
    return "\n".join(texts)


def read(data, filename):
    name = (filename or "").lower()
    if name.endswith(".xml") or data.lstrip()[:5] == b"<?xml":
        kind = einvoice_kind(data)
        if not kind:
            raise ValueError("XML is not a UBL or CII invoice")
        return {"source": "einvoice", "syntax": kind, "text": None, "b64": base64.b64encode(data).decode()}
    if data[:4] == b"%PDF":
        pdf = PdfReader(io.BytesIO(data))
        for fname, contents in (pdf.attachments or {}).items():
            if fname.lower() in EMBEDDED_NAMES and einvoice_kind(contents[0]):
                return {"source": "einvoice", "syntax": "zugferd", "text": None, "embedded_file": fname, "b64": base64.b64encode(data).decode()}
        text = "\n".join((p.extract_text() or "") for p in pdf.pages).strip()
        if len(text) >= 40:
            return {"source": "pdf-text", "text": text}
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "in.pdf").write_bytes(data)
            subprocess.run(["pdftoppm", "-r", "300", "-png", str(Path(d) / "in.pdf"), str(Path(d) / "page")], check=True, timeout=120)
            return {"source": "ocr", "text": ocr(d).strip()}
    if name.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        with tempfile.TemporaryDirectory() as d:
            ext = ".png" if name.endswith(".png") else ".jpg" if name.endswith((".jpg", ".jpeg")) else ".tif"
            (Path(d) / f"in{ext}").write_bytes(data)
            return {"source": "ocr", "text": ocr(d).strip()}
    raise ValueError("Unknown file type: " + filename)


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"ok": True})

    def do_POST(self):
        q = parse_qs(urlparse(self.path).query)
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            self._send(200, read(data, q.get("filename", [""])[0]))
        except Exception as e:  # noqa: BLE001
            self._send(200, {"source": "error", "text": None, "error": str(e)})

    def log_message(self, *a):
        pass


ThreadingHTTPServer(("0.0.0.0", 8098), H).serve_forever()
