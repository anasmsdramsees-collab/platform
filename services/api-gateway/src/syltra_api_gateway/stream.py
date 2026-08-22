"""The live change feed behind `/v1/stream`.

The console polled every 15 seconds. That is fine for a demo and wrong in a
house: somebody presses a switch and watches a screen that has not noticed yet,
and the thing they lose faith in is the platform, not the interval.

## What the stream carries, and what it deliberately does not

It carries **notifications that something changed**, not the changed data.
`{"type": "changed", "seq": 41, "reasons": ["RISK_CASE_CONFIRMED"]}` — and the
console re-reads the endpoints it already reads.

Sending the data itself would mean maintaining a second copy of every view
model, one shaped for REST and one for the socket, and the day they disagree is
the day the screen shows one thing and a refresh shows another. A wake-up signal
cannot drift from the thing it wakes you to look at, because there is only one
source of the data and the socket is not it.

The cost is one extra round trip per change. In exchange, a reading that arrives
now is on screen now.

## Sequence numbers, and what they are for

Every home has a monotonic sequence. A client that reconnects sends the last
sequence it saw; if that sequence is still in the buffer, it learns whether
anything happened while it was away. If it is too old — a long disconnection, or
a burst that overran the ring — the server says `resync`, which for a wake-up
feed simply means "re-read everything", and the console does exactly that.

So a missed event cannot leave a stale screen. The worst case is a redundant
refresh, and the failure the sequence exists to prevent — a client that missed
the one message that mattered and does not know it — cannot happen quietly.

## Coalescing

Twenty changes in the same tick become one notification carrying twenty reasons.
Without that, a burst produces a refresh per event and the console spends its
time re-fetching rather than rendering.
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

#: Notifications retained per home. A client away for longer than this comes
#: back to a `resync` rather than a partial history, which is the safe answer.
BUFFER_SIZE = 256

#: How often a quiet connection proves it is still alive. A socket that has
#: silently died looks exactly like a house where nothing is happening, and the
#: console must be able to tell those apart.
HEARTBEAT_SECONDS = 20.0


@dataclass(frozen=True)
class Change:
    """One notification. Deliberately small — it names, it does not carry."""

    seq: int
    home_id: str
    reasons: tuple[str, ...]
    at: datetime

    def as_json(self) -> dict[str, Any]:
        return {
            "type": "changed",
            "seq": self.seq,
            "home_id": self.home_id,
            "reasons": list(self.reasons),
            "at": self.at.isoformat(),
        }


@dataclass
class _HomeFeed:
    sequence: int = 0
    buffer: deque[Change] = field(default_factory=lambda: deque(maxlen=BUFFER_SIZE))
    subscribers: set[asyncio.Queue[Change]] = field(default_factory=set)


class StreamHub:
    """Per-home change feeds, with enough history to answer "did I miss any?"."""

    def __init__(self) -> None:
        self._homes: dict[str, _HomeFeed] = {}

    def _feed(self, home_id: str) -> _HomeFeed:
        return self._homes.setdefault(home_id, _HomeFeed())

    # ── producing ──

    def publish(self, home_id: str, *reasons: str, now: datetime | None = None) -> Change:
        """Record that something changed, and wake anyone watching.

        Never raises and never blocks: a full subscriber queue drops its oldest
        notification rather than stalling the caller. The caller is usually a
        safety path, and a screen refresh must not be able to delay one.
        """
        feed = self._feed(home_id)
        feed.sequence += 1
        change = Change(
            seq=feed.sequence,
            home_id=home_id,
            reasons=tuple(reasons) or ("UPDATED",),
            at=now or datetime.now(tz=UTC),
        )
        feed.buffer.append(change)
        for queue in feed.subscribers:
            if queue.full():
                # The client is behind. Dropping the oldest is right for a
                # wake-up feed: the newest notification alone tells it to
                # re-read, and re-reading catches up on everything.
                with_suppressed_empty(queue)
            queue.put_nowait(change)
        return change

    # ── consuming ──

    def latest_sequence(self, home_id: str) -> int:
        return self._feed(home_id).sequence

    def missed(self, home_id: str, cursor: int) -> tuple[list[Change], bool]:
        """What happened since `cursor`, and whether the answer is complete.

        Returns `(changes, resync_required)`. `resync_required` is True when the
        cursor is older than anything retained — the client cannot be told what
        it missed, so it is told to re-read instead of being left with a gap it
        does not know about.
        """
        feed = self._feed(home_id)
        if cursor >= feed.sequence:
            return [], False
        if not feed.buffer:
            return [], cursor > 0
        oldest = feed.buffer[0].seq
        if cursor < oldest - 1:
            return [], True
        return [change for change in feed.buffer if change.seq > cursor], False

    def subscribe(self, home_id: str) -> asyncio.Queue[Change]:
        queue: asyncio.Queue[Change] = asyncio.Queue(maxsize=64)
        self._feed(home_id).subscribers.add(queue)
        return queue

    def unsubscribe(self, home_id: str, queue: asyncio.Queue[Change]) -> None:
        self._feed(home_id).subscribers.discard(queue)

    @property
    def subscriber_count(self) -> int:
        return sum(len(feed.subscribers) for feed in self._homes.values())


def with_suppressed_empty(queue: asyncio.Queue[Change]) -> None:
    """Drop one item, tolerating the race where another consumer took it."""
    try:
        queue.get_nowait()
    except asyncio.QueueEmpty:  # pragma: no cover - timing dependent
        return
