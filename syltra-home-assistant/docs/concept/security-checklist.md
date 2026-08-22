# Security Checklist (Stage 17)

Status against section 39 of the build prompt.

| Item | Status | Notes |
|---|---|---|
| TLS | Deployment concern | Terminate TLS at the load balancer / ingress in staging & production. Local dev intentionally runs plain HTTP. |
| Token rotation readiness | Done | Access tokens are short-lived (15m default); refresh tokens are long-lived (30d default) and independently rotatable by changing `JWT_REFRESH_SECRET`. |
| Device identity | Done | Hubs authenticate with a dedicated pairing token (`type: 'hub'` JWT claim), distinct from user tokens — see `src/hubs/guards/hub-auth.guard.ts`. |
| Secrets management | Partial | All secrets are env-driven (`.env`, never committed — see `.gitignore`). `device_credentials.secret_ref` stores only a pointer, never a plaintext secret; wiring to an actual secret manager (Vault/AWS Secrets Manager/etc.) is a production deployment task, not code in this repo. |
| RBAC | Done | `RoleName` enum (owner/admin/installer/resident/guest/developer/service), enforced via `TenantGuard` + `RolesGuard` + `@Roles()` decorator. |
| Audit logs | Done | `AuditService` records registration, hub registration, and membership changes to `audit_logs`. Device/command/plan activity is recorded to `device_events` (append-only, per-organization). |
| API rate limiting | Done | `@nestjs/throttler` applied globally (120 req/min per client by default) via `APP_GUARD` in `app.module.ts`. |
| Input validation | Done | Global `ValidationPipe` (`whitelist`, `forbidNonWhitelisted`, `transform`) in `main.ts`; every DTO uses `class-validator` decorators. |
| Secure WebSocket | Deployment concern | No raw WebSocket server is exposed by the API in Stage 1 (state/events flow over MQTT). When a live WebSocket API is added, terminate it behind the same TLS as the REST API. |
| Encrypted database backups | Deployment concern | Configure encryption-at-rest and encrypted backups at the managed Postgres provider / infrastructure layer. |
| Don't log secrets | Done | No token, password, or secret value is passed to `Logger` calls anywhere in the codebase — verified by inspection, not just convention. |

## Also added

- `helmet()` for standard security headers.
- CORS enabled (default: allow-all for MVP — tighten `app.enableCors()` to an explicit origin allowlist before production).
