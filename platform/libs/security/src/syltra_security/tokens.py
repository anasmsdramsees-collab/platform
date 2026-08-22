"""Local access tokens (spec §25.1, §25.3).

Short-lived, locally issued, and never stored in plaintext. The token registry
keeps only a SHA-256 hash, so a leaked database of tokens cannot be replayed —
the same reasoning that applies to passwords applies here.

Deliberately *not* JWT. A JWT would need a signing key, key rotation, and a
clock the hub may not have synchronised; and its main advantage — stateless
verification across services — is worthless when every consumer is on the same
box. An opaque random token checked against a local store is simpler to reason
about and has a smaller failure surface.
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from syltra_security.authorization import Principal, Role, constant_time_equals

TOKEN_BYTES = 32
DEFAULT_TTL = timedelta(hours=12)
"""Short-lived where practical (spec §25.1). Twelve hours suits a household
device that people use daily without wanting to re-authenticate constantly."""


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class TokenRecord:
    """A stored token. Holds the hash, never the token itself."""

    token_hash: str
    subject: str
    role: Role
    home_ids: frozenset[str]
    issued_at: datetime
    expires_at: datetime
    display_name: str | None = None
    revoked: bool = False

    def is_valid_at(self, now: datetime) -> bool:
        return not self.revoked and now < self.expires_at


class AuthenticationError(PermissionError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


class TokenStore:
    """In-memory token registry.

    Persistence arrives with the operator account model; the verification rules
    live here so they are identical whichever store backs them.
    """

    def __init__(self) -> None:
        self._records: dict[str, TokenRecord] = {}

    def issue(
        self,
        subject: str,
        role: Role,
        home_ids: frozenset[str] | set[str],
        ttl: timedelta = DEFAULT_TTL,
        display_name: str | None = None,
        now: datetime | None = None,
    ) -> tuple[str, TokenRecord]:
        """Issue a token, returning it once. Only the hash is retained."""
        moment = now or datetime.now(tz=UTC)
        token = secrets.token_urlsafe(TOKEN_BYTES)
        record = TokenRecord(
            token_hash=hash_token(token),
            subject=subject,
            role=role,
            home_ids=frozenset(home_ids),
            issued_at=moment,
            expires_at=moment + ttl,
            display_name=display_name,
        )
        self._records[record.token_hash] = record
        return token, record

    def verify(self, token: str, now: datetime | None = None) -> Principal:
        """Resolve a token to a principal, or raise."""
        moment = now or datetime.now(tz=UTC)
        if not token:
            raise AuthenticationError("MISSING_TOKEN", "no credential supplied")

        candidate = hash_token(token)
        record = self._records.get(candidate)
        if record is None:
            # Compare against a dummy so an unknown token costs the same time
            # as a known one.
            constant_time_equals(candidate, "0" * 64)
            raise AuthenticationError("INVALID_TOKEN", "credential not recognised")
        if record.revoked:
            raise AuthenticationError("TOKEN_REVOKED", "credential has been revoked")
        if not record.is_valid_at(moment):
            raise AuthenticationError("TOKEN_EXPIRED", "credential has expired")

        return Principal(
            subject=record.subject,
            role=record.role,
            home_ids=record.home_ids,
            display_name=record.display_name,
        )

    def revoke(self, token: str) -> bool:
        record = self._records.get(hash_token(token))
        if record is None:
            return False
        self._records[record.token_hash] = TokenRecord(
            token_hash=record.token_hash,
            subject=record.subject,
            role=record.role,
            home_ids=record.home_ids,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            display_name=record.display_name,
            revoked=True,
        )
        return True

    def revoke_subject(self, subject: str) -> int:
        """Revoke every token for a subject — the response to a compromise."""
        count = 0
        for token_hash, record in list(self._records.items()):
            if record.subject == subject and not record.revoked:
                self._records[token_hash] = TokenRecord(
                    token_hash=record.token_hash,
                    subject=record.subject,
                    role=record.role,
                    home_ids=record.home_ids,
                    issued_at=record.issued_at,
                    expires_at=record.expires_at,
                    display_name=record.display_name,
                    revoked=True,
                )
                count += 1
        return count

    def purge_expired(self, now: datetime | None = None) -> int:
        moment = now or datetime.now(tz=UTC)
        expired = [h for h, r in self._records.items() if moment >= r.expires_at]
        for token_hash in expired:
            del self._records[token_hash]
        return len(expired)

    def __len__(self) -> int:
        return len(self._records)


def bearer_token(authorization_header: str | None) -> str:
    """Extract a bearer token from an Authorization header."""
    if not authorization_header:
        return ""
    scheme, _, value = authorization_header.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return value.strip()
