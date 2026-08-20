# Local API

The only publicly exposed SYLTRA service (spec §14.9). Everything else lives on
the container network.

Base URL on a hub: `http://<hub>:8080`. OpenAPI at `/v1/openapi.json`, browsable
at `/v1/docs`.

## Authentication

Bearer tokens, issued locally, stored as SHA-256 hashes, valid 12 hours.

```http
Authorization: Bearer <token>
```

Not JWT — deliberately. A JWT needs a signing key, key rotation, and a
synchronised clock the hub may not have, and its advantage (stateless
verification across services) is worthless when every consumer is on the same
box. An opaque random token checked against a local store has a smaller failure
surface.

## Authorization

Every home-scoped endpoint checks **home membership first, then permission**. A
home the caller cannot see returns `404`, never `403` — "forbidden" would
confirm the home exists.

| Role | Read | Approve | Comfort | Security | Audit | Models | Privacy |
|---|---|---|---|---|---|---|---|
| `OWNER` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `ADULT` | ✓ | ✓ | ✓ | ✓ | | | |
| `CHILD` | ✓ | | ✓ | | | | |
| `GUEST` | ✓ | | | | | | |
| `INSTALLER` | ✓ | | ✓ | | | | |

`ACT_SAFETY` appears in no row. Life-safety actuators are commanded by
deterministic safety rules, never by a person holding a permission.

## Endpoints

```text
GET    /v1/health
GET    /v1/system/status
GET    /v1/homes/{home_id}/twin
GET    /v1/homes/{home_id}/rooms
GET    /v1/homes/{home_id}/devices
GET    /v1/homes/{home_id}/contexts/current
GET    /v1/homes/{home_id}/recommendations
GET    /v1/homes/{home_id}/recommendations/{id}
POST   /v1/homes/{home_id}/recommendations/{id}/approve
POST   /v1/homes/{home_id}/recommendations/{id}/reject
POST   /v1/homes/{home_id}/recommendations/{id}/feedback
GET    /v1/homes/{home_id}/risks
GET    /v1/homes/{home_id}/risks/{id}
GET    /v1/homes/{home_id}/actions
GET    /v1/homes/{home_id}/actions/{id}
GET    /v1/homes/{home_id}/models
POST   /v1/homes/{home_id}/models/{name}/suspend
GET    /v1/audit?home_id=...
WS     /v1/stream?home_id=...&token=...
GET    /metrics
```

## Localization

Every response carrying reason codes carries **both**:

```json
{
  "reason_codes": ["CONFIDENCE_BELOW_THRESHOLD"],
  "reasons": ["Not confident enough to act"]
}
```

Machine identifiers stay stable for audit and testing; the wording is free to
change. Locale comes from `Accept-Language` or `?locale=`, and responses include
`"direction": "rtl" | "ltr"` so a client does not have to know which languages
are right-to-left.

## Errors

One envelope for every failure:

```json
{
  "detail": {
    "error": "INSUFFICIENT_PERMISSION",
    "message": "role CHILD does not hold APPROVE_RECOMMENDATION",
    "correlation_id": "…"
  }
}
```

No stack traces, no table names, no broker subjects (spec §14.9). A test sweeps
every read endpoint for `nats://`, `postgresql`, subject names and SQL
fragments.

| Status | Meaning |
|---|---|
| `400` | Malformed request |
| `401` | Missing, invalid, expired or revoked credential |
| `403` | Authenticated, but the role lacks the permission |
| `404` | Not found — **including a home the caller cannot see** |
| `409` | Well-formed but not permitted now (lifecycle skip, promotion below gate) |
| `429` | Rate limited; `retry_after_seconds` included |

## Pagination and rate limits

List endpoints take `limit` and `offset` and return
`{items, total, limit, offset, has_more}`. Mutations are rate-limited per
principal **and per route**, so a burst of feedback cannot exhaust a
household's approval budget.

## WebSocket stream

The token arrives as a query parameter because browsers cannot set headers on a
WebSocket handshake. It is verified **before** the socket is accepted:
unauthenticated peers get close code `4401`, foreign homes `4403`, and neither
ever reaches an open connection.
