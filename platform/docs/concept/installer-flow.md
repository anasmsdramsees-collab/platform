# Installer Flow (Stage 15)

Section 36/37 of the build prompt describe the installer flow as: create project → register hub → connect Home Assistant → discover devices → map rooms → test devices → save configuration → handover.

## MVP scope

A dedicated `apps/installer` mobile/web flow is **not yet built** — `apps/installer/` remains a placeholder for a later stage. For Stage 1, the same flow is achievable through the Admin dashboard (`frontend/admin`) plus the Edge Agent setup, in this order:

1. **Create project** — register (`POST /v1/auth/register`) creates a user, an organization, and an owner membership in one call.
2. **Register hub** — from the Admin dashboard (or `POST /v1/organizations/:organizationId/hubs`), register a hub. The response includes a one-time **pairing token** — this is the QR-pairing payload referenced in section 37 (`{ apiUrl, tenantId: organizationId, hubId, hubToken: pairingToken }`). A real QR flow just needs to encode this JSON and have the SYLTRA Edge Agent's provisioning step scan/decode it into its `.env`.
3. **Connect Home Assistant** — configure `backend/edge-agent/.env` with the pairing payload plus the Home Assistant URL and long-lived access token, then start the agent.
4. **Discover devices** — the Edge Agent runs discovery automatically on startup and every `DISCOVERY_INTERVAL_MS`; discovered devices appear in the Admin dashboard's Devices table.
5. **Map rooms** — `PATCH /v1/organizations/:organizationId/devices/:deviceId` with `{ "roomId": "..." }` assigns a discovered device to a room (validated against the organization's own room hierarchy). Discovery also sets `roomId` directly if the Edge Agent already knows it.
6. **Test devices** — send a manual command (`POST /v1/organizations/:organizationId/devices/:deviceId/commands`) and confirm the resulting state change appears under the device's state history.
7. **Save configuration / handover** — the hub's `status`/`lastSeenAt` (visible in the dashboard) confirms the hub is online and reporting; audit logs record every registration and command for handover review.

## Follow-up for a dedicated installer app

A real `apps/installer` should add: guided room mapping UI, a QR *generator* (cloud side) and QR *scanner* (mobile/agent side) instead of copy-pasting the pairing token, and a "test all devices" checklist view. None of that changes the underlying API contract above.
