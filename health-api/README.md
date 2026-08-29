# SYLTRA HEALTH API (Cloudflare Worker + D1)

Backend for the SYLTRA HEALTH site: stores early-access registrations and powers
the admin console (login, registrations, services).

## Endpoints
- `POST /api/register` — public. Body: `{ name, email, phone?, type?, interest?, message? }`
- `POST /api/admin/login` — `{ user, pass }` → `{ token }`
- `GET  /api/admin/registrations` — Bearer token. → `{ registrations, total }`
- `PATCH /api/admin/registrations/:id` — `{ status }`
- `GET  /api/admin/services` — → `{ services }`
- `POST /api/admin/services` — `{ name_en, name_ar, path }`
- `PATCH /api/admin/services/:id` — `{ active }`

## One-time setup
```bash
cd health-api
npm install

# 1) Create the D1 database, then paste the returned database_id into wrangler.toml
npx wrangler d1 create syltra-health

# 2) Create the tables + seed services
npm run db:init

# 3) Set the secrets (encrypted at rest in Cloudflare)
npx wrangler secret put ADMIN_USER        # e.g. admin
npx wrangler secret put ADMIN_PASSWORD    # a strong password
npx wrangler secret put ADMIN_SECRET      # a long random string (token signing)

# 4) Deploy
npm run deploy
```
The deploy prints the Worker URL, e.g. `https://syltra-health-api.<subdomain>.workers.dev`
(or bind a custom route like `api.health.syltraone.com`).

## Wire the site to the API
In the **syltra-health** Cloudflare Pages project, add an environment variable and
redeploy:
```
NEXT_PUBLIC_HEALTH_API = https://syltra-health-api.<subdomain>.workers.dev
```
Until this is set, the early-access form falls back to a prefilled email, and the
admin console shows "API not configured".

## Notes
- Credentials live only as Cloudflare secrets, never in the repo.
- CORS origins are controlled by `ALLOWED_ORIGINS` in `wrangler.toml`.
- The admin token is an HMAC-signed value valid for 12 hours.
