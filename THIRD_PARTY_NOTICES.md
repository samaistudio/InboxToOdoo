# Third-party notices

InboxToOdoo itself is licensed under the Apache License 2.0 (see `LICENSE` and `NOTICE`).

## Material adapted into this repository

### blader/humanizer (MIT)

Part 3 of `prompts/EMAIL_STYLE.md` (the list of phrases and patterns that make an e-mail sound machine-written) started from the checklist in https://github.com/blader/humanizer. The text in this repository is rewritten; the licence notice is kept here as the MIT licence asks.

```
MIT License

Copyright (c) 2025 Siqi Chen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Software the stack downloads at install time

None of the following is included in this repository. `docker compose` pulls the images, and the `docreader` image installs its packages, on the user's own machine. Each keeps its own licence.

| Component | Used for | Licence |
|---|---|---|
| n8n (`n8nio/n8n:2.49.5`) | runs the workflows | Sustainable Use License (fair-code; free for internal business use, not an OSI licence) |
| Odoo 18 Community (`odoo:18`) | the ERP | LGPL-3.0 |
| PostgreSQL 16 (`postgres:16`) | Odoo's database | PostgreSQL License |
| Mailpit (`axllent/mailpit`) | local test mailbox | MIT |
| Python 3.12 (`python:3.12-slim`, base of `docreader` and `mock-llm`) | small local services | PSF License 2.0 (Debian packages in the image under their own licences) |
| Tesseract OCR with German and English language data (Debian `tesseract-ocr*`) | reading scanned invoices in `docreader` | Apache-2.0 |
| Poppler utilities (Debian `poppler-utils`, `pdftoppm`) | turning scanned PDF pages into images in `docreader` | GPL-2.0-or-later; called as a separate program |
| pypdf 5.1.0 | reading PDF text and embedded e-invoice files in `docreader` | BSD-3-Clause |

Tools used only to build the test files and screenshots (Google Chrome, ffmpeg, Node.js) are not part of the stack and are not distributed.

### Requests to outside hosts

The stack itself runs locally, but the two settings forms are pages from n8n's own form template, and that template loads the Open Sans font from Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) and its icon from `n8n.io`. So opening a form sends the viewer's IP address to Google and to n8n. This comes from n8n, not from this project's code. A real setup should serve the forms behind the reverse proxy recommended in the README and strip or replace that link. The product page and the walkthrough in `docs/` load nothing from outside hosts.

## Names and data

All companies, people, orders, bank accounts, phone numbers and e-mail addresses in the demo data are fictional. The three supplier VAT IDs are made up so that they pass the German check digit; they have not been checked against VIES, so one could belong to a real company by chance. Phone numbers come from the range the Bundesnetzagentur keeps free for fiction (0221 4710 …). E-mail addresses use the reserved `.example` domain. Odoo and n8n are trademarks of their owners; this project is not affiliated with either.
