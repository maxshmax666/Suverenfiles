"""Traffic collection and candidate extraction."""

from __future__ import annotations

from collections import OrderedDict

from greenwave.models.stream import StreamCandidate
from greenwave.models.traffic import NetworkEvent


class TrafficCollector:
    """Bounded collector for normalized browser traffic."""

    def __init__(self, max_events: int = 10_000) -> None:
        self._max_events = max_events
        self._events: OrderedDict[str, NetworkEvent] = OrderedDict()

    def record(self, event: NetworkEvent) -> None:
        """Record or update one network observation."""

        key = f"{event.method}:{event.url}"
        self._events[key] = event
        self._events.move_to_end(key)
        while len(self._events) > self._max_events:
            self._events.popitem(last=False)

    def candidates(self) -> list[StreamCandidate]:
        """Convert traffic observations into classifier candidates."""

        candidates: list[StreamCandidate] = []
        for event in self._events.values():
            content_type = event.response_headers.get("content-type")
            if content_type is None:
                content_type = event.response_headers.get("Content-Type")
            headers = {**event.request_headers}
            candidates.append(
                StreamCandidate(
                    url=event.url,
                    method=event.method,
                    status=event.status,
                    resource_type=event.resource_type,
                    content_type=content_type,
                    headers=headers,
                    body_sample=event.body_sample,
                    source=event.kind.value,
                )
            )
        return candidates
