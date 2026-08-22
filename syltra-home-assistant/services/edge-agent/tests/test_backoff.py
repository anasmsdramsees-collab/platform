"""Bounded exponential backoff tests (spec §14.1)."""

import random

import pytest
from hypothesis import given
from hypothesis import strategies as st
from syltra_edge_agent.backoff import BoundedExponentialBackoff


def test_delay_grows_and_is_capped() -> None:
    b = BoundedExponentialBackoff(
        initial=1.0, maximum=10.0, factor=2.0, jitter=0.0, rng=random.Random(1)
    )
    assert [b.next_delay() for _ in range(6)] == [1.0, 2.0, 4.0, 8.0, 10.0, 10.0]


def test_reset_returns_to_initial() -> None:
    b = BoundedExponentialBackoff(
        initial=1.0, maximum=10.0, factor=2.0, jitter=0.0, rng=random.Random(1)
    )
    b.next_delay()
    b.next_delay()
    b.reset()
    assert b.attempt == 0
    assert b.next_delay() == 1.0


def test_jitter_stays_within_bounds() -> None:
    b = BoundedExponentialBackoff(
        initial=2.0, maximum=10.0, factor=1.0, jitter=0.5, rng=random.Random(7)
    )
    for _ in range(50):
        delay = b.next_delay()
        assert 1.0 <= delay <= 3.0


@pytest.mark.parametrize(
    ("initial", "maximum", "factor", "jitter"),
    [
        (0.0, 60.0, 2.0, 0.1),  # non-positive initial
        (5.0, 1.0, 2.0, 0.1),  # maximum below initial
        (1.0, 60.0, 0.5, 0.1),  # shrinking factor
        (1.0, 60.0, 2.0, 1.0),  # jitter at/above 1
        (1.0, 60.0, 2.0, -0.1),  # negative jitter
    ],
)
def test_invalid_parameters_rejected(
    initial: float, maximum: float, factor: float, jitter: float
) -> None:
    with pytest.raises(ValueError, match="invalid backoff parameters"):
        BoundedExponentialBackoff(initial=initial, maximum=maximum, factor=factor, jitter=jitter)


@given(
    attempts=st.integers(min_value=1, max_value=200),
    maximum=st.floats(min_value=1.0, max_value=120.0),
)
def test_property_delay_never_exceeds_maximum(attempts: int, maximum: float) -> None:
    b = BoundedExponentialBackoff(initial=0.5, maximum=maximum, rng=random.Random(3))
    for _ in range(attempts):
        assert 0.0 <= b.next_delay() <= maximum
