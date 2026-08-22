"""Bounded exponential backoff with jitter (spec §14.1: reconnect with
bounded exponential backoff)."""

import random


class BoundedExponentialBackoff:
    """Delay grows by ``factor`` from ``initial`` and never exceeds ``maximum``.

    Jitter is proportional and non-security-relevant; a seeded ``rng`` makes
    tests deterministic.
    """

    def __init__(
        self,
        initial: float = 1.0,
        maximum: float = 60.0,
        factor: float = 2.0,
        jitter: float = 0.1,
        rng: random.Random | None = None,
    ) -> None:
        if initial <= 0 or maximum < initial or factor < 1 or not 0 <= jitter < 1:
            msg = "invalid backoff parameters"
            raise ValueError(msg)
        self._initial = initial
        self._maximum = maximum
        self._factor = factor
        self._jitter = jitter
        self._rng = rng or random.Random()  # noqa: S311  # nosec B311 - jitter, not crypto
        self._attempt = 0

    def next_delay(self) -> float:
        base = min(self._initial * (self._factor**self._attempt), self._maximum)
        self._attempt += 1
        spread = base * self._jitter
        delay = base + self._rng.uniform(-spread, spread)
        return min(max(delay, 0.0), self._maximum)

    def reset(self) -> None:
        self._attempt = 0

    @property
    def attempt(self) -> int:
        return self._attempt
