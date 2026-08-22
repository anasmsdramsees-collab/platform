"""Request-scoped authentication, authorization, locale and rate limiting."""

import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, Query, Request

from syltra_api_gateway.errors import forbidden, not_found, rate_limited, unauthenticated
from syltra_api_gateway.translations import negotiate_locale
from syltra_security import (
    AuthenticationError,
    AuthorizationError,
    Permission,
    Principal,
    TokenStore,
    authorize,
    bearer_token,
)


@dataclass
class RateLimiter:
    """Sliding-window limiter for mutations (spec §21).

    Keyed by principal *and* route, so a burst of feedback submissions cannot
    exhaust a household's approval budget.
    """

    limit: int = 30
    window_seconds: float = 60.0
    _hits: dict[tuple[str, str], deque[float]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._hits = defaultdict(deque)

    def check(self, subject: str, route: str, now: float | None = None) -> None:
        moment = now if now is not None else time.monotonic()
        bucket = self._hits[(subject, route)]
        cutoff = moment - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            raise rate_limited(bucket[0] + self.window_seconds - moment)
        bucket.append(moment)

    def reset(self) -> None:
        self._hits.clear()


def get_token_store(request: Request) -> TokenStore:
    store: TokenStore = request.app.state.tokens
    return store


def get_rate_limiter(request: Request) -> RateLimiter:
    limiter: RateLimiter = request.app.state.rate_limiter
    return limiter


def correlation_id(
    x_correlation_id: Annotated[str | None, Header(alias="X-Correlation-ID")] = None,
) -> str:
    """Reuse a caller's correlation id, or mint one (spec §21)."""
    return x_correlation_id or str(uuid4())


def current_locale(
    accept_language: Annotated[str | None, Header(alias="Accept-Language")] = None,
    locale: Annotated[str | None, Query(description="Override the negotiated locale")] = None,
) -> str:
    return negotiate_locale(accept_language, locale)


def current_principal(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    store: TokenStore = request.app.state.tokens
    try:
        return store.verify(bearer_token(authorization))
    except AuthenticationError as exc:
        raise unauthenticated(exc.code, str(exc)) from exc


PrincipalDep = Annotated[Principal, Depends(current_principal)]
LocaleDep = Annotated[str, Depends(current_locale)]
CorrelationDep = Annotated[str, Depends(correlation_id)]


def require(permission: Permission) -> Callable[[str, Principal], None]:
    """Build a home-scoped permission check for one endpoint."""

    def _check(home_id: str, principal: Principal) -> None:
        try:
            authorize(principal, home_id, permission)
        except AuthorizationError as exc:
            # A home the caller cannot see is reported as absent, never as
            # forbidden: "forbidden" would confirm the home exists.
            if exc.code == "HOME_NOT_FOUND":
                raise not_found("HOME_NOT_FOUND", f"no home {home_id}") from exc
            raise forbidden(exc.code, str(exc)) from exc

    return _check


check_read = require(Permission.READ_HOME)
check_audit = require(Permission.READ_AUDIT)
check_approve = require(Permission.APPROVE_RECOMMENDATION)
check_models = require(Permission.MANAGE_MODELS)
check_privacy = require(Permission.MANAGE_PRIVACY)
check_automations = require(Permission.MANAGE_AUTOMATIONS)
check_users = require(Permission.MANAGE_USERS)
check_acknowledge_safety = require(Permission.ACKNOWLEDGE_SAFETY)
