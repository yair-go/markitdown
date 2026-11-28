# Docker image for the web converter app.
#
# Build from the REPOSITORY ROOT (the app uses ../../packages/markitdown):
#   docker build -f apps/web-converter/Dockerfile -t web-converter .
# Run (published on this computer only):
#   docker run --rm -p 127.0.0.1:5000:5000 web-converter
#
# Files sent to the build are controlled by Dockerfile.dockerignore next to this
# file, not by the repository's root .dockerignore (that one belongs to the
# MarkItDown CLI image and would exclude apps/).

FROM python:3.13-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.7.20 /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    ORT_DISABLE_TELEMETRY=1 \
    EXIFTOOL_PATH=/usr/bin/exiftool \
    FFMPEG_PATH=/usr/bin/ffmpeg \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# ffmpeg/exiftool: audio and metadata converters. Noto fonts: Hebrew (and other
# scripts) in generated PDFs - slim images ship with almost no fonts.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libimage-exiftool-perl fonts-noto-core fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Dependencies first, so code changes don't reinstall everything.
COPY packages/markitdown packages/markitdown
COPY apps/web-converter/pyproject.toml apps/web-converter/uv.lock apps/web-converter/
WORKDIR /src/apps/web-converter
RUN uv sync --locked --no-dev

# Headless Chromium for PDF export, plus the system libraries it needs.
RUN .venv/bin/playwright install --with-deps --only-shell chromium \
    && rm -rf /var/lib/apt/lists/*

COPY apps/web-converter/app.py ./
COPY apps/web-converter/templates templates

RUN useradd --create-home --uid 1000 app
USER app

# Inside the container the app must listen on all interfaces; limit exposure
# with the -p 127.0.0.1:... mapping when running it.
ENV HOST=0.0.0.0 PORT=5000
EXPOSE 5000
CMD [".venv/bin/python", "app.py"]
