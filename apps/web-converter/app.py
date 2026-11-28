"""Local web app for converting files to Markdown with MarkItDown.

Run:  uv run app.py   then open http://127.0.0.1:5000
"""

import html
import io
import os
import threading
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file
from markitdown import MarkItDown, StreamInfo

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB per request

md = MarkItDown(enable_plugins=False)


def md_name(name: str) -> str:
    stem = Path(name).stem or "document"
    return f"{stem}.md"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/convert")
def convert_files():
    files = request.files.getlist("files")
    if not files:
        return jsonify(error="לא נבחרו קבצים"), 400

    results = []
    for f in files:
        filename = f.filename or "file"
        ext = os.path.splitext(filename)[1].lower() or None
        try:
            data = io.BytesIO(f.read())
            result = md.convert_stream(
                data,
                stream_info=StreamInfo(filename=filename, extension=ext),
            )
            results.append(
                {
                    "source": filename,
                    "name": md_name(filename),
                    "title": result.title,
                    "markdown": result.markdown,
                }
            )
        except Exception as e:  # report per-file errors, keep going
            results.append(
                {"source": filename, "error": f"{type(e).__name__}: {e}"}
            )
    return jsonify(results=results)


@app.post("/api/convert-url")
def convert_url():
    url = (request.get_json(silent=True) or {}).get("url", "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify(error="יש להזין כתובת http או https תקינה"), 400
    try:
        result = md.convert_uri(url)
    except Exception as e:
        return jsonify(results=[{"source": url, "error": f"{type(e).__name__}: {e}"}])
    name = md_name(Path(parsed.path).name or parsed.netloc.replace(".", "_"))
    return jsonify(
        results=[
            {
                "source": url,
                "name": name,
                "title": result.title,
                "markdown": result.markdown,
            }
        ]
    )


@app.post("/api/zip")
def make_zip():
    items = (request.get_json(silent=True) or {}).get("items", [])
    buf = io.BytesIO()
    used = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            name = Path(item.get("name") or "document.md").name
            base, n = name, 1
            while name in used:
                name = f"{Path(base).stem} ({n}).md"
                n += 1
            used.add(name)
            zf.writestr(name, item.get("markdown", ""))
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name="markdown.zip",
    )


PDF_CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Segoe UI", Arial, "David", sans-serif; font-size: 11pt;
  line-height: 1.6; color: #111; }
h1, h2, h3 { line-height: 1.3; page-break-after: avoid; }
table { border-collapse: collapse; margin: 8px 0; }
th, td { border: 1px solid #999; padding: 4px 8px; vertical-align: top; }
th { background: #f0f0f0; }
tr, img, pre { page-break-inside: avoid; }
img { max-width: 100%; }
pre, code { font-family: Consolas, monospace; font-size: 9.5pt; background: #f4f4f4; }
pre { padding: 8px; white-space: pre-wrap; overflow-wrap: anywhere; }
blockquote { margin: 0; padding: 0 12px; border-inline-start: 3px solid #ccc; color: #444; }
"""

# Playwright's sync API isn't thread-safe; Flask serves requests on threads.
_pdf_lock = threading.Lock()


@app.post("/api/pdf")
def make_pdf():
    """Render the preview HTML (already sanitized in the browser) to a PDF."""
    from playwright.sync_api import sync_playwright

    payload = request.get_json(silent=True) or {}
    body = payload.get("html", "")
    title = html.escape(payload.get("title") or "document")
    direction = "rtl" if payload.get("dir") == "rtl" else "ltr"
    doc = (
        f'<!doctype html><html dir="{direction}"><head><meta charset="utf-8">'
        f"<title>{title}</title><style>{PDF_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )
    with _pdf_lock, sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_context(java_script_enabled=False).new_page()
            page.set_content(doc, wait_until="load")
            pdf = page.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        finally:
            browser.close()
    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{Path(payload.get('name') or 'document').stem}.pdf",
    )


if __name__ == "__main__":
    # Localhost only by default: the app reads arbitrary files/URLs you give it.
    # The Docker image sets HOST=0.0.0.0 (needed inside a container).
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
