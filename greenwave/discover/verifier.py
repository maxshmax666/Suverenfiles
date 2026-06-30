"""Async stream verification."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiohttp

from greenwave.models.stream import StreamDescriptor, StreamType, VerificationResult
from greenwave.utils.media import parse_hls_manifest


class StreamVerifier:
    """Verify stream availability and extract best-effort metadata."""

    def __init__(self, timeout_seconds: int = 30) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async def verify(self, stream: StreamDescriptor) -> VerificationResult:
        """Probe a stream URL and return a typed verification result."""

        try:
            async with self._session(stream) as session:
                async with session.get(stream.url, allow_redirects=True) as response:
                    text = await self._safe_text(response)
                    online = 200 <= response.status < 400
                    content_type = response.headers.get("content-type", "")
                    if stream.type in {StreamType.HLS, StreamType.LL_HLS} and text:
                        metadata = parse_hls_manifest(text, str(response.url))
                        return VerificationResult(
                            stream=stream,
                            online=online,
                            width=metadata.width,
                            height=metadata.height,
                            codec=metadata.codec,
                            bitrate=metadata.bitrate,
                            duration_seconds=metadata.duration_seconds,
                            playlist_url=str(response.url),
                            playlist_text=text[:200_000],
                            segments=list(metadata.segments[:10]),
                            raw_metadata={
                                "content_type": content_type,
                                "is_live": metadata.is_live,
                            },
                        )
                    return VerificationResult(
                        stream=stream,
                        online=online,
                        raw_metadata={"status": response.status, "content_type": content_type},
                    )
        except (TimeoutError, aiohttp.ClientError, asyncio.CancelledError) as exc:
            if isinstance(exc, asyncio.CancelledError):
                raise
            return VerificationResult(stream=stream, online=False, error=str(exc))

    @asynccontextmanager
    async def _session(self, stream: StreamDescriptor) -> AsyncIterator[aiohttp.ClientSession]:
        jar = aiohttp.CookieJar(unsafe=True)
        for name, value in stream.cookies.items():
            jar.update_cookies({name: value})
        async with aiohttp.ClientSession(
            headers=stream.headers, cookie_jar=jar, timeout=self._timeout
        ) as session:
            yield session

    async def _safe_text(self, response: aiohttp.ClientResponse) -> str:
        body = await response.content.read(512_000)
        return body.decode(response.charset or "utf-8", errors="replace")
