/**
 * SYLTRA HEALTH API (Cloudflare Worker + D1).
 *
 * Two surfaces:
 *   /api/*      the marketing site: early-access registrations + admin console
 *   /api/v1/*   the mobile app, against the contract in
 *               syltra-health-app/mobile/src/services/api/contract.ts
 *
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
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,OPTIONS",
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

function b64url(bytes: ArrayBuffer | Uint8Array): string {
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  return btoa(String.fromCharCode(...view)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
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

/**
 * Tokens are DOMAIN-SEPARATED by audience.
 *
 * Both the admin console and the app are signed with the same secret, so the
 * audience is mixed into the signed data itself: an app token's signature can
 * never validate as an admin token even if its claims were forged, because a
 * different string was signed. The `typ` claim is then checked on top as
 * defence in depth.
 *
 * This matters because device tokens are handed out by an unauthenticated
 * endpoint. Without separation, anyone could mint one and walk into
 * /api/admin/* — which returns every early-access registration.
 */
type Audience = "admin" | "app";

const signed = (aud: Audience, payload: string) => `${aud}:${payload}`;

async function mintToken(env: Env, aud: Audience, claims: Record<string, unknown>, ttlMs: number) {
  const payload = b64url(enc.encode(JSON.stringify({ ...claims, typ: aud, exp: Date.now() + ttlMs })));
  return `${payload}.${await hmac(env.ADMIN_SECRET, signed(aud, payload))}`;
}

/** Returns the token's claims when the signature, audience and expiry all hold. */
async function readToken(
  env: Env,
  aud: Audience,
  token: string | null
): Promise<Record<string, unknown> | null> {
  if (!token) return null;
  const [payload, sig] = token.split(".");
  if (!payload || !sig) return null;
  if (!timingSafeEqual(sig, await hmac(env.ADMIN_SECRET, signed(aud, payload)))) return null;
  try {
    const data = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    if (data.typ !== aud) return null;
    if (typeof data.exp !== "number" || data.exp <= Date.now()) return null;
    return data;
  } catch {
    return null;
  }
}

async function issueToken(env: Env): Promise<string> {
  return mintToken(env, "admin", { sub: env.ADMIN_USER }, 1000 * 60 * 60 * 12);
}

async function verifyToken(env: Env, token: string | null): Promise<boolean> {
  const claims = await readToken(env, "admin", token);
  // The subject must be the configured admin, not merely a valid signature.
  return claims !== null && claims.sub === env.ADMIN_USER;
}

/**
 * App sessions are bound to a device, not to a password: there is no login
 * screen yet, and health data should not sit behind a shared credential.
 * The token carries the profile it unlocks and expires on its own.
 */
async function issueAppToken(env: Env, profileId: string, deviceId: string): Promise<string> {
  return mintToken(env, "app", { sub: profileId, did: deviceId }, 1000 * 60 * 60 * 24 * 30);
}

/**
 * Returns the profile id a token unlocks, or null.
 *
 * The device row is checked on every request, so deleting it revokes access
 * immediately. A 30-day token with no way to revoke it is not an acceptable
 * key to someone's health data.
 */
async function profileFromToken(env: Env, token: string | null): Promise<string | null> {
  const claims = await readToken(env, "app", token);
  if (!claims) return null;
  const profileId = typeof claims.sub === "string" ? claims.sub : null;
  const deviceId = typeof claims.did === "string" ? claims.did : null;
  if (!profileId || !deviceId) return null;

  const device = await env.DB.prepare("SELECT profile_id FROM devices WHERE id=?")
    .bind(deviceId)
    .first<{ profile_id: string }>();
  if (!device || device.profile_id !== profileId) return null;

  return profileId;
}

/** Fixed-window limiter, backed by D1. Keeps device registration from being farmed. */
async function rateLimit(env: Env, key: string, limit: number, windowSeconds: number): Promise<boolean> {
  const now = Math.floor(Date.now() / 1000);
  const windowStart = now - (now % windowSeconds);
  await env.DB.prepare(
    "INSERT INTO rate_limits (key, window_start, count) VALUES (?,?,1) " +
      "ON CONFLICT(key, window_start) DO UPDATE SET count = count + 1"
  )
    .bind(key, windowStart)
    .run();
  const row = await env.DB.prepare("SELECT count FROM rate_limits WHERE key=? AND window_start=?")
    .bind(key, windowStart)
    .first<{ count: number }>();
  return (row?.count ?? 0) <= limit;
}

function bearer(req: Request): string | null {
  const h = req.headers.get("Authorization") || "";
  return h.startsWith("Bearer ") ? h.slice(7) : null;
}


/* ------------------------------------------------------------------ app v1 */

const KIND_LABEL: Record<string, string> = {
  heart_rate: "النبض",
  sleep: "النوم",
  steps: "الحركة",
  glucose: "السكر",
};

type BaselineRow = {
  days_collected: number;
  days_required: number;
  glucose_low: number;
  glucose_high: number;
  heart_rate_low: number;
  heart_rate_high: number;
  nightly_motion_gap_minutes: number;
};

/**
 * NOTE: the presentation strings on `readings` (label, baseline.text) are part
 * of the contract the app compiles against, so they are produced here. That
 * duplicates four Arabic labels between this Worker and the app — the contract
 * should move to raw readings and let the app phrase them. Tracked in
 * syltra-health-app/api/README.md.
 */
function readingView(row: any, b: BaselineRow) {
  const value = Number(row.value);
  let text = "من مصدرك المتصل";
  let state: "within" | "below" | "above" | "neutral" = "neutral";

  if (row.kind === "glucose" || row.kind === "heart_rate") {
    const low = row.kind === "glucose" ? b.glucose_low : b.heart_rate_low;
    const high = row.kind === "glucose" ? b.glucose_high : b.heart_rate_high;
    text = `معتادك ${low} – ${high}`;
    state = value < low ? "below" : value > high ? "above" : "within";
  }

  return {
    id: String(row.id),
    kind: row.kind,
    label: KIND_LABEL[row.kind] ?? row.kind,
    value: row.unit === "steps" ? value.toLocaleString("en-US") : String(value),
    unit: row.unit ?? undefined,
    source: row.source,
    takenAt: row.taken_at,
    baseline: { text, state },
  };
}

async function bootstrapFor(env: Env, profileId: string) {
  const db = env.DB;
  const [profile, baseline, plan] = await Promise.all([
    db.prepare("SELECT id,name,time_zone FROM profiles WHERE id=?").bind(profileId).first<any>(),
    db.prepare("SELECT * FROM baselines WHERE profile_id=?").bind(profileId).first<BaselineRow>(),
    db.prepare("SELECT verify_window_seconds FROM response_plans WHERE profile_id=?").bind(profileId).first<any>(),
  ]);
  if (!profile || !baseline) return null;

  const [levels, consent, rooms, people, shares, readings] = await Promise.all([
    db.prepare("SELECT level_id,enabled FROM response_levels WHERE profile_id=?").bind(profileId).all(),
    db.prepare("SELECT source,purpose,enabled FROM consent_sources WHERE profile_id=?").bind(profileId).all(),
    db
      .prepare(
        "SELECT r.id,r.name,s.temperature,s.humidity,s.co2,s.last_motion FROM rooms r " +
          "LEFT JOIN room_states s ON s.profile_id=r.profile_id AND s.room_id=r.id WHERE r.profile_id=?"
      )
      .bind(profileId)
      .all(),
    db
      .prepare("SELECT * FROM trusted_people WHERE profile_id=? AND removed_at IS NULL ORDER BY priority")
      .bind(profileId)
      .all(),
    db
      .prepare(
        "SELECT sr.person_id, sr.field, sr.scope FROM share_rules sr " +
          "JOIN trusted_people p ON p.id = sr.person_id WHERE p.profile_id=?"
      )
      .bind(profileId)
      .all(),
    db
      .prepare("SELECT * FROM readings WHERE profile_id=? ORDER BY taken_at DESC LIMIT 20")
      .bind(profileId)
      .all(),
  ]);

  const LEVEL_META: Record<string, { index: string; title: string; description: string; locked?: boolean }> = {
    daily: { index: "01", title: "دعم يومي", description: "تذكير بالحركة أو القياس أو التهوية داخل التطبيق فقط." },
    verify: { index: "02", title: "تحقق منك", description: "سؤال مباشر على الهاتف والساعة وشاشة المنزل." },
    trusted: { index: "03", title: "تنبيه شخص موثوق", description: "شخص واحد في كل مرة، وفق زمن الوصول والتوفر." },
    authorized: {
      index: "04",
      title: "تصعيد معتمد",
      description: "يتطلب تكاملاً رسمياً معتمداً ومختبراً. غير متاح بعد.",
      locked: true,
    },
  };

  const SHARE_LABEL: Record<string, string> = {
    reason: "سبب التنبيه",
    location: "موقعك",
    readings: "قراءاتك اليومية",
  };

  const SOURCE_NAME: Record<string, string> = {
    apple_health: "Apple Health",
    health_connect: "Health Connect",
    glucose_meter: "جهاز قياس السكر",
    bp_monitor: "جهاز قياس الضغط",
    home_sensors: "حساسات المنزل",
    location: "موقعك",
  };

  // SQLite returns rows in whatever order it likes; these screens are ordered
  // lists, so the order is fixed here rather than left to the query planner.
  const ORDER = {
    level: ["daily", "verify", "trusted", "authorized"],
    source: ["apple_health", "health_connect", "glucose_meter", "bp_monitor", "home_sensors", "location"],
    share: ["reason", "location", "readings"],
    reading: ["heart_rate", "sleep", "steps", "glucose"],
  };
  const by = (seq: string[], key: string) => {
    const i = seq.indexOf(key);
    return i === -1 ? seq.length : i;
  };

  const shareRows = (shares.results ?? []) as any[];

  return {
    profile: { id: profile.id, name: profile.name, timeZone: profile.time_zone },
    baseline: {
      daysCollected: baseline.days_collected,
      daysRequired: baseline.days_required,
      glucoseRange: { low: baseline.glucose_low, high: baseline.glucose_high },
      heartRateRange: { low: baseline.heart_rate_low, high: baseline.heart_rate_high },
      nightlyMotionGapMinutes: baseline.nightly_motion_gap_minutes,
    },
    thresholds: { verifyWeight: 2, motionGapFactor: 2, minBaselineDays: 14 },
    readings: ((readings.results ?? []) as any[])
      .sort((a, b) => by(ORDER.reading, a.kind) - by(ORDER.reading, b.kind))
      .map((r) => readingView(r, baseline)),
    rooms: ((rooms.results ?? []) as any[]).map((r) => ({
      id: r.id,
      name: r.name,
      temperature: r.temperature ?? 0,
      humidity: r.humidity ?? 0,
      airQuality: { label: (r.co2 ?? 0) > 900 ? "متوسطة" : "جيدة", co2: r.co2 ?? 0 },
      motion: { label: r.last_motion ? "نشِطة" : "—", lastSeen: r.last_motion ?? "" },
    })),
    circle: ((people.results ?? []) as any[]).map((p) => ({
      id: p.id,
      name: p.name,
      initial: (p.name as string).slice(0, 1),
      relation: p.relation,
      feminine: p.feminine === 1,
      priority: p.priority,
      available: p.available === 1,
      availabilityNote: p.available === 1 ? (p.feminine === 1 ? "متاحة" : "متاح") : "خارج أوقات التوفر",
      etaMinutes: p.eta_minutes ?? undefined,
      hasKey: p.has_key === 1,
      shares: shareRows
        .filter((sr) => sr.person_id === p.id)
        .sort((a, b) => by(ORDER.share, a.field) - by(ORDER.share, b.field))
        .map((sr) => ({ label: SHARE_LABEL[sr.field] ?? sr.field, scope: sr.scope })),
    })),
    plan: {
      verifyWindowSeconds: plan?.verify_window_seconds ?? 120,
      levels: ((levels.results ?? []) as any[])
        .sort((a, b) => by(ORDER.level, a.level_id) - by(ORDER.level, b.level_id))
        .map((l) => ({
          id: l.level_id,
          ...LEVEL_META[l.level_id],
          enabled: l.enabled === 1,
        })),
    },
    consent: ((consent.results ?? []) as any[])
      .sort((a, b) => by(ORDER.source, a.source) - by(ORDER.source, b.source))
      .map((c) => ({
        id: c.source,
        name: SOURCE_NAME[c.source] ?? c.source,
        purpose: c.purpose,
        enabled: c.enabled === 1,
      })),
  };
}

/** Creates a profile with safe defaults: nothing shared, nothing learned yet. */
async function createProfile(env: Env, name: string): Promise<string> {
  const id = crypto.randomUUID();
  const db = env.DB;
  await db.batch([
    db.prepare("INSERT INTO profiles (id,name) VALUES (?,?)").bind(id, name),
    db.prepare("INSERT INTO baselines (profile_id) VALUES (?)").bind(id),
    db.prepare("INSERT INTO response_plans (profile_id) VALUES (?)").bind(id),
    ...["daily", "verify", "trusted", "authorized"].map((lvl) =>
      db
        .prepare("INSERT INTO response_levels (profile_id,level_id,enabled) VALUES (?,?,?)")
        .bind(id, lvl, lvl === "authorized" ? 0 : 1)
    ),
    ...[
      ["apple_health", "النبض والنوم والخطوات — لبناء نمطك"],
      ["health_connect", "أجهزة أندرويد والساعات المتصلة"],
      ["glucose_meter", "القراءات فقط — لا نفترض قراءة غير متاحة"],
      ["home_sensors", "حركة ووجود وحرارة وهواء — بدون كاميرات"],
      ["location", "أثناء الأحداث فقط — لاختيار الأقرب إليك"],
    ].map(([src, purpose]) =>
      db.prepare("INSERT INTO consent_sources (profile_id,source,purpose,enabled) VALUES (?,?,?,0)").bind(id, src, purpose)
    ),
  ]);
  return id;
}

/** The demo cast for `seed=demo`. Mirrors CAST in the app's src/data/mock.ts. */
const DEMO_CAST = [
  { name: "نورة", relation: "الزوجة", feminine: 1, priority: 1, key: 1, eta: 7 as number | null, avail: 1 },
  { name: "سلطان", relation: "الأخ", feminine: 0, priority: 2, key: 0, eta: 21 as number | null, avail: 1 },
  { name: "منيرة", relation: "الجارة", feminine: 1, priority: 3, key: 0, eta: null as number | null, avail: 0 },
];

/** Optional demo content, so a device can exercise the whole flow end to end. */
async function seedDemo(env: Env, profileId: string) {
  const db = env.DB;
  // The demo cast lives here and nowhere else, mirroring CAST in the app's
  // src/data/mock.ts. Keep the two in step when a persona changes.
  const people = DEMO_CAST.map((p) => ({ id: crypto.randomUUID(), ...p }));
  const now = new Date().toISOString();
  await db.batch([
    db.prepare("UPDATE baselines SET days_collected=11 WHERE profile_id=?").bind(profileId),
    db.prepare("UPDATE consent_sources SET enabled=1 WHERE profile_id=? AND source<>'location'").bind(profileId),
    ...[
      ["bedroom", "غرفة النوم", 23, 45, 640],
      ["living", "المعيشة", 24, 42, 700],
      ["majlis", "المجلس", 25, 40, 910],
    ].flatMap(([rid, rname, t, h, co2]) => [
      db.prepare("INSERT OR IGNORE INTO rooms (id,profile_id,name) VALUES (?,?,?)").bind(rid, profileId, rname),
      db
        .prepare(
          "INSERT OR REPLACE INTO room_states (profile_id,room_id,temperature,humidity,co2,last_motion) VALUES (?,?,?,?,?,?)"
        )
        .bind(profileId, rid, t, h, co2, now),
    ]),
    ...people.flatMap((p) => [
      db
        .prepare(
          "INSERT INTO trusted_people (id,profile_id,name,relation,feminine,priority,has_key,eta_minutes,available,accepted_at) " +
            "VALUES (?,?,?,?,?,?,?,?,?,?)"
        )
        .bind(p.id, profileId, p.name, p.relation, p.feminine, p.priority, p.key, p.eta, p.avail, now),
      db.prepare("INSERT INTO share_rules (person_id,field,scope) VALUES (?,?,?)").bind(p.id, "reason", "event_only"),
      db
        .prepare("INSERT INTO share_rules (person_id,field,scope) VALUES (?,?,?)")
        .bind(p.id, "location", p.priority === 3 ? "never" : "event_only"),
      db.prepare("INSERT INTO share_rules (person_id,field,scope) VALUES (?,?,?)").bind(p.id, "readings", "never"),
    ]),
    ...[
      ["heart_rate", 72, "bpm", "apple_health"],
      ["glucose", 110, "mg/dL", "glucose_meter"],
      ["steps", 3240, "steps", "health_connect"],
    ].map(([kind, value, unit, source]) =>
      db
        .prepare("INSERT INTO readings (id,profile_id,kind,value,unit,source,taken_at) VALUES (?,?,?,?,?,?,?)")
        .bind(crypto.randomUUID(), profileId, kind, value, unit, source, now)
    ),
  ]);
}

async function handleV1(
  req: Request,
  env: Env,
  ch: Record<string, string>,
  path: string
): Promise<Response | null> {
  // ---- device registration: the only unauthenticated app route ----
  if (req.method === "POST" && path === "/api/v1/devices") {
    const b = (await req.json().catch(() => ({}))) as Record<string, string>;
    const deviceId = (b.deviceId || "").trim();
    if (deviceId.length < 8 || deviceId.length > 128) return json({ error: "deviceId required" }, 400, ch);

    const ip = req.headers.get("CF-Connecting-IP") || "unknown";
    if (!(await rateLimit(env, `dev:${ip}`, 10, 3600))) return json({ error: "too many requests" }, 429, ch);

    const existing = await env.DB.prepare("SELECT profile_id FROM devices WHERE id=?")
      .bind(deviceId)
      .first<{ profile_id: string }>();

    let profileId = existing?.profile_id;
    if (!profileId) {
      profileId = await createProfile(env, (b.name || "مستخدم").slice(0, 80));
      await env.DB.prepare("INSERT INTO devices (id,profile_id) VALUES (?,?)").bind(deviceId, profileId).run();
      if (b.seed === "demo") await seedDemo(env, profileId);
    } else {
      await env.DB.prepare("UPDATE devices SET last_seen=datetime('now') WHERE id=?").bind(deviceId).run();
    }

    return json({ profileId, token: await issueAppToken(env, profileId, deviceId) }, 200, ch);
  }

  // ---- everything else needs a device token ----
  const profileId = await profileFromToken(env, bearer(req));
  if (!profileId) return json({ error: "unauthorized" }, 401, ch);

  if (req.method === "GET" && path === "/api/v1/bootstrap") {
    const data = await bootstrapFor(env, profileId);
    return data ? json(data, 200, ch) : json({ error: "profile not found" }, 404, ch);
  }

  if (req.method === "PUT" && path === "/api/v1/response-plan") {
    const b = (await req.json().catch(() => ({}))) as any;
    const seconds = Math.max(60, Math.min(600, Number(b.verifyWindowSeconds) || 120));
    const levels = Array.isArray(b.levels) ? b.levels : [];
    await env.DB.batch([
      env.DB.prepare("UPDATE response_plans SET verify_window_seconds=?, updated_at=datetime('now') WHERE profile_id=?")
        .bind(seconds, profileId),
      ...levels.map((l: any) =>
        env.DB.prepare("UPDATE response_levels SET enabled=? WHERE profile_id=? AND level_id=?")
          .bind(l.enabled ? 1 : 0, profileId, String(l.id))
      ),
    ]);
    return new Response(null, { status: 204, headers: ch });
  }

  if (req.method === "PUT" && path === "/api/v1/consent") {
    const b = (await req.json().catch(() => ({}))) as any;
    const list = Array.isArray(b.consent) ? b.consent : [];
    await env.DB.batch(
      list.map((c: any) =>
        env.DB.prepare(
          "UPDATE consent_sources SET enabled=?, granted_at=CASE WHEN ? THEN COALESCE(granted_at, datetime('now')) ELSE granted_at END, " +
            "revoked_at=CASE WHEN ? THEN NULL ELSE datetime('now') END WHERE profile_id=? AND source=?"
        ).bind(c.enabled ? 1 : 0, c.enabled ? 1 : 0, c.enabled ? 1 : 0, profileId, String(c.id))
      )
    );
    return new Response(null, { status: 204, headers: ch });
  }

  if (req.method === "PUT" && path === "/api/v1/circle") {
    const b = (await req.json().catch(() => ({}))) as any;
    const list = Array.isArray(b.circle) ? b.circle : [];
    await env.DB.batch(
      list.map((p: any) =>
        env.DB.prepare(
          "UPDATE trusted_people SET priority=?, has_key=?, eta_minutes=?, available=? WHERE id=? AND profile_id=?"
        ).bind(
          Number(p.priority) || 99,
          p.hasKey ? 1 : 0,
          p.etaMinutes ?? null,
          p.available ? 1 : 0,
          String(p.id),
          profileId
        )
      )
    );
    return new Response(null, { status: 204, headers: ch });
  }

  if (req.method === "POST" && path === "/api/v1/events") {
    const b = (await req.json().catch(() => ({}))) as any;
    const id = crypto.randomUUID();
    // Caps, so a client cannot use its own audit trail as unbounded storage.
    const cap = (v: unknown, n: number) => (Array.isArray(v) ? v.slice(0, n) : []);
    const text = (v: unknown, n: number) => String(v ?? "").slice(0, n);
    const signals = cap(b.signals, 50);
    const audit = cap(b.audit, 200);
    const shared = cap(b.shared, 20);

    await env.DB.batch([
      env.DB.prepare(
        "INSERT INTO events (id,profile_id,started_at,ended_at,outcome,simulated) VALUES (?,?,?,?,?,?)"
      ).bind(id, profileId, Number(b.startedAt) || Date.now(), b.endedAt ?? null, b.outcome ?? null, b.simulated ? 1 : 0),
      ...signals.map((s: any) =>
        env.DB.prepare(
          "INSERT INTO event_signals (event_id,signal_id,at,kind,title,detail,weight) VALUES (?,?,?,?,?,?,?)"
        ).bind(id, text(s.id, 80), Number(s.at) || 0, text(s.kind, 40), text(s.title, 300), s.detail == null ? null : text(s.detail, 300), Number(s.weight) || 0)
      ),
      ...audit.map((a: any) =>
        env.DB.prepare(
          "INSERT INTO event_audit (id,event_id,at,phase,phase_label,title,detail) VALUES (?,?,?,?,?,?,?)"
        ).bind(
          crypto.randomUUID(),
          id,
          Number(a.at) || 0,
          text(a.phase, 40),
          text(a.phaseLabel, 40),
          text(a.title, 300),
          a.detail == null ? null : text(a.detail, 300)
        )
      ),
      ...shared.map((sh: any) =>
        env.DB.prepare(
          "INSERT INTO event_shares (event_id,person_id,fields,shared_at,expires_at) VALUES (?,?,?,?,?)"
        ).bind(
          id,
          text(sh.personId, 80),
          JSON.stringify(cap(sh.fields, 20).map((f: unknown) => text(f, 80))),
          Number(b.startedAt) || Date.now(),
          sh.expiresAt ?? null
        )
      ),
    ]);
    return json({ id }, 201, ch);
  }

  if (req.method === "GET" && path === "/api/v1/events") {
    const { results } = await env.DB.prepare(
      "SELECT id,started_at,ended_at,outcome FROM events WHERE profile_id=? ORDER BY started_at DESC LIMIT 100"
    )
      .bind(profileId)
      .all();
    return json(
      ((results ?? []) as any[]).map((e) => ({
        id: e.id,
        startedAt: e.started_at,
        endedAt: e.ended_at ?? undefined,
        outcome: e.outcome ?? undefined,
      })),
      200,
      ch
    );
  }

  const eventMatch = path.match(/^\/api\/v1\/events\/([\w-]+)$/);
  if (req.method === "GET" && eventMatch) {
    const eventId = eventMatch[1];
    const event = await env.DB.prepare("SELECT * FROM events WHERE id=? AND profile_id=?")
      .bind(eventId, profileId)
      .first<any>();
    if (!event) return json(null, 404, ch);

    const [signals, audit, shares] = await Promise.all([
      env.DB.prepare("SELECT * FROM event_signals WHERE event_id=?").bind(eventId).all(),
      env.DB.prepare("SELECT * FROM event_audit WHERE event_id=? ORDER BY at").bind(eventId).all(),
      env.DB.prepare("SELECT * FROM event_shares WHERE event_id=?").bind(eventId).all(),
    ]);

    return json(
      {
        id: event.id,
        startedAt: event.started_at,
        endedAt: event.ended_at ?? undefined,
        outcome: event.outcome ?? undefined,
        signals: ((signals.results ?? []) as any[]).map((s) => ({
          id: s.signal_id,
          at: s.at,
          kind: s.kind,
          title: s.title,
          detail: s.detail ?? undefined,
          weight: s.weight,
        })),
        audit: ((audit.results ?? []) as any[]).map((a) => ({
          id: a.id,
          at: a.at,
          phase: a.phase,
          phaseLabel: a.phase_label,
          title: a.title,
          detail: a.detail ?? undefined,
        })),
        shared: ((shares.results ?? []) as any[]).map((sh) => ({
          personId: sh.person_id,
          fields: JSON.parse(sh.fields),
          expiresAt: sh.expires_at ?? undefined,
        })),
      },
      200,
      ch
    );
  }

  return json({ error: "not found" }, 404, ch);
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const origin = req.headers.get("Origin");
    const ch = cors(origin, env.ALLOWED_ORIGINS);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: ch });

    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "");

    try {
      // ---- App surface ----
      if (path.startsWith("/api/v1/")) {
        const res = await handleV1(req, env, ch, path);
        if (res) return res;
      }

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
        // Without this the admin password is open to unlimited guessing.
        const ip = req.headers.get("CF-Connecting-IP") || "unknown";
        if (!(await rateLimit(env, `login:${ip}`, 8, 900))) {
          return json({ error: "too many attempts" }, 429, ch);
        }
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
      // The message is for the operator, not the caller: D1 errors name tables
      // and columns, which is a free map of the schema for anyone probing.
      console.error("unhandled", err);
      return json({ error: "server error" }, 500, ch);
    }
  },
};
