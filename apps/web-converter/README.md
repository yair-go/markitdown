# Web converter

Local web app for converting files (PDF, Word, PowerPoint, Excel, HTML, EPUB, ...) to
Markdown with [MarkItDown](../../packages/markitdown). Drag & drop, edit the Markdown,
preview, download `.md` / ZIP / PDF, or save straight into a folder (Chrome/Edge).

This app is **not** part of upstream MarkItDown — it lives only in this fork.

## Run with uv

From this folder (`apps/web-converter`):

```powershell
.\run.ps1          # installs Chromium for PDF export if missing, opens the browser
uv run app.py      # or just start the server: http://127.0.0.1:5000
```

## Run with Docker

Build from the **repository root**, because the image includes `packages/markitdown`:

```powershell
docker build -f apps/web-converter/Dockerfile -t web-converter .
docker run --rm -p 127.0.0.1:5000:5000 web-converter
```

Then open http://127.0.0.1:5000.

Notes:
- Keep the `127.0.0.1:` in `-p`: the app converts any file or URL it is given and
  should not be reachable from other computers.
- The build uses `Dockerfile.dockerignore` (next to the Dockerfile), not the root
  `.dockerignore`, which belongs to the MarkItDown CLI image and excludes `apps/`.
- The root `Dockerfile` builds the MarkItDown command-line tool, not this app.
