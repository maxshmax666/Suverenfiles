# GreenWave Recorder

Production-ready open-source platform for automatic discovery, recording, and analysis of city video cameras.

codex/determine-mobile-app-build-capability-h1begz
GreenWave is a Python 3.12+ async application for Linux and Termux(Android where a compatible Chromium executable is available). Phase 1 implements the foundation of the AI Discover Engine: typed stream detection, verification, SQLite persistence, JSON export, and a Playwright/CDP browser capture pipeline.

## Features implemented in this milestone

- Python package managed by `uv`;
- Typer CLI entrypoint: `greenwave`;
- real Chromium browser session abstraction through Playwright;
- CDP network tap for HTTP, XHR, Fetch, WebSocket, Media, Manifest, and ServiceWorker-related traffic;
- stream classifier for HLS, Low Latency HLS, DASH, RTSP, RTMP, FLV, WebRTC, MJPEG, MP4 live, and unknown video traffic;
- async verifier for direct streams and HLS playlists;
- SQLite schema and repository layer for sites, cameras, streams, playlists, segments, history, and errors;
- deterministic `cameras.json` export;
- typed Pydantic models, structlog logging, pytest tests, ruff and mypy configuration;
- interface packages reserved for Recorder, Analyzer, Web UI, and REST API phases.

## CLI

```bash
greenwave discover <url>
greenwave crawl <url>
greenwave scan <url-or-file>
greenwave list
greenwave verify <stream-url>
```

Example:

```bash
greenwave discover https://setitagila.ru/cameras
```

## Install and run

```bash
uv sync --extra dev
uv run playwright install chromium
uv run greenwave --help
uv run greenwave scan https://example.test/live/index.m3u8
```

## Development checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy greenwave tests
uv run pytest
```

## Minimum requirements

- Python 3.12+;
- uv;
- Playwright;
- Chromium-compatible runtime;
- SQLite;
- Linux, or Termux with a compatible Chromium executable.

## Architecture

The architecture specification is maintained in [`docs/architecture.md`](docs/architecture.md). Implementation is split into runnable milestones, and each milestone must keep tests passing.

## Security and operations notes

GreenWave uses legitimate browser behavior: JavaScript execution, cookies, redirects, storage, persistent browser context, and CDP observation. It does not implement exploit-based WAF bypass, CAPTCHA-solving services, or credential extraction. Keep concurrency conservative when scanning public camera sites.
=======
The repository is being migrated from the previous Android project to a Python 3.12+ async application that runs on Linux and, where Chromium support is available, Termux on Android.

## Phase 1: AI Discover Engine

The first implementation phase focuses on:

- launching real Chromium with Playwright;
- connecting to Chrome DevTools Protocol;
- capturing HTTP, Fetch, XHR, WebSocket, Media, Manifest, and ServiceWorker traffic;
- detecting HLS, Low Latency HLS, DASH, RTSP, RTMP, FLV, WebRTC, MJPEG, MP4 live, and unknown video streams;
- verifying playlists, manifests, and segments;
- extracting online status, duration, FPS, resolution, codec, and bitrate when available;
- storing results in SQLite;
- exporting `cameras.json`.

## Planned CLI

```bash
greenwave discover <url>
greenwave crawl <url>
greenwave scan <url-or-file>
greenwave list
greenwave verify <stream-url-or-id>
```

## Architecture-first workflow

Implementation must not start until the architecture is approved. The current architecture proposal is in [`docs/architecture.md`](docs/architecture.md).

After approval, the project will be implemented in small, runnable commits. Each milestone must pass tests before the next milestone starts.

## Minimum Requirements

- Python 3.12+;
- uv;
- Playwright;
- Chromium-compatible runtime;
- SQLite;
- Linux, or Termux with a compatible Chromium executable.
 main
