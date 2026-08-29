/**
 * SYLTRA HEALTH API (Cloudflare Worker + D1).
 * Public:  POST /api/register
 * Admin:   POST /api/admin/login
 *          GET  /api/admin/registrations
 *          PATCH /api/admin/registrations/:id      { status }
 *          GET  /api/admin/services
 *          POST /api/admin/services                { name_en, name_ar, path }
 *          PATCH /api/admin/services/:id           { active }
 */

export interface Env {
  DB: D1Database;
  ALLOWED_ORIGINS: string;
  ADMIN_USER: string;
  ADMIN_PASSWORD: string;
  ADMIN_SECRET: string;
}

const enc = new TextEncoder();

function cors(origin: string | null, allowed: string): Record<string, string> {
  const list = allowed.split(",").map((s) => s.trim());
  const ok = origin && list.includes(origin) ? origin : list[0] ?? "*";
  return {
    "Access-Control-Allow-Origin": ok,
    "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function json(data: unknown, status: number, headers: Record<string, string>): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function b64url(bytes: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function hmac(secret: string, data: string): Promise<string> {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(data));
  return b64url(sig);
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let out = 0;
  for (let i = 0; i < a.length; i++) out |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return out === 0;
}

async function issueToken(env: Env): Promise<string> {
  const payload = b64url(enc.encode(JSON.stringify({ sub: env.ADMIN_USER, exp: Date.now() + 1000 * 60 * 60 * 12 })));
  const sig = await hmac(env.ADMIN_SECRET, payload);
  return `${payload}.${sig}`;
}

async function verifyToken(env: Env, token: string | null): Promise<boolean> {
  if (!token) return false;
  const [payload, sig] = token.split(".");
  if (!payload || !sig) return false;
  const expected = await hmac(env.ADMIN_SECRET, payload);
  if (!timingSafeEqual(sig, expected)) return false;
  try {
    const data = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    return typeof data.exp === "number" && data.exp > Date.now();
  } catch {
    return false;
  }
}

function bearer(req: Request): string | null {
  const h = req.headers.get("Authorization") || "";
  return h.startsWith("Bearer ") ? h.slice(7) : null;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const origin = req.headers.get("Origin");
    const ch = cors(origin, env.ALLOWED_ORIGINS);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: ch });

    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "");

    try {
      // ---- Public: early-access registration ----
      if (req.method === "POST" && path === "/api/register") {
        const b = (await req.json().catch(() => ({}))) as Record<string, string>;
        const name = (b.name || "").trim();
        const email = (b.email || "").trim();
        if (!name || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
          return json({ error: "name and a valid email are required" }, 400, ch);
        }
        await env.DB.prepare(
          "INSERT INTO registrations (name,email,phone,user_type,interest,message) VALUES (?,?,?,?,?,?)"
        )
          .bind(name.slice(0, 200), email.slice(0, 200), (b.phone || "").slice(0, 60), (b.type || "").slice(0, 80), (b.interest || "").slice(0, 120), (b.message || "").slice(0, 2000))
          .run();
        return json({ ok: true }, 201, ch);
      }

      // ---- Admin: login ----
      if (req.method === "POST" && path === "/api/admin/login") {
        const b = (await req.json().catch(() => ({}))) as Record<string, string>;
        const okUser = timingSafeEqual(b.user || "", env.ADMIN_USER);
        const okPass = timingSafeEqual(b.pass || "", env.ADMIN_PASSWORD);
        if (!okUser || !okPass) return json({ error: "invalid credentials" }, 401, ch);
        return json({ token: await issueToken(env) }, 200, ch);
      }

      // ---- Everything below requires a valid admin token ----
      if (path.startsWith("/api/admin/")) {
        if (!(await verifyToken(env, bearer(req)))) return json({ error: "unauthorized" }, 401, ch);

        if (req.method === "GET" && path === "/api/admin/registrations") {
          const { results } = await env.DB.prepare("SELECT * FROM registrations ORDER BY created_at DESC LIMIT 500").all();
          const total = (results as unknown[]).length;
          return json({ registrations: results, total }, 200, ch);
        }

        const regMatch = path.match(/^\/api\/admin\/registrations\/(\d+)$/);
        if (req.method === "PATCH" && regMatch) {
          const b = (await req.json().catch(() => ({}))) as Record<string, string>;
          await env.DB.prepare("UPDATE registrations SET status=? WHERE id=?").bind((b.status || "new").slice(0, 40), Number(regMatch[1])).run();
          return json({ ok: true }, 200, ch);
        }

        if (req.method === "GET" && path === "/api/admin/services") {
          const { results } = await env.DB.prepare("SELECT * FROM services ORDER BY sort").all();
          return json({ services: results }, 200, ch);
        }

        if (req.method === "POST" && path === "/api/admin/services") {
          const b = (await req.json().catch(() => ({}))) as Record<string, string>;
          if (!b.name_en || !b.path) return json({ error: "name_en and path required" }, 400, ch);
          await env.DB.prepare("INSERT OR IGNORE INTO services (name_en,name_ar,path,active,sort) VALUES (?,?,?,1,999)")
            .bind(b.name_en.slice(0, 120), (b.name_ar || b.name_en).slice(0, 120), b.path.slice(0, 200))
            .run();
          return json({ ok: true }, 201, ch);
        }

        const svcMatch = path.match(/^\/api\/admin\/services\/(\d+)$/);
        if (req.method === "PATCH" && svcMatch) {
          const b = (await req.json().catch(() => ({}))) as Record<string, unknown>;
          await env.DB.prepare("UPDATE services SET active=? WHERE id=?").bind(b.active ? 1 : 0, Number(svcMatch[1])).run();
          return json({ ok: true }, 200, ch);
        }
      }

      return json({ error: "not found" }, 404, ch);
    } catch (err) {
      return json({ error: "server error", detail: String(err) }, 500, ch);
    }
  },
};
