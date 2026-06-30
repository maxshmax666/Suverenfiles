# GreenWave Recorder

Production-ready open-source platform for automatic discovery, recording, and analysis of city video cameras.

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
