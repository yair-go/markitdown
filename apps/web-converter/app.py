"""Local web app for converting files to Markdown with MarkItDown.

Run:  .venv\\Scripts\\python app.py   then open http://127.0.0.1:5000
"""

import io
import os
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


if __name__ == "__main__":
    # Bound to localhost only: the app reads arbitrary files/URLs you give it.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
