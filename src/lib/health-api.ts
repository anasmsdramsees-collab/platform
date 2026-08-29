// Base URL of the SYLTRA HEALTH API worker. Set NEXT_PUBLIC_HEALTH_API in the
// health Pages project (e.g. https://syltra-health-api.<subdomain>.workers.dev
// or a custom route like https://api.health.syltraone.com). Empty = not wired.
export const HEALTH_API =
  process.env.NEXT_PUBLIC_HEALTH_API ?? "https://syltra-health-api.syltratech.workers.dev";

const TOKEN_KEY = "syltra-health-admin-token";

export function getToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}
export function setToken(t: string) {
  try {
    localStorage.setItem(TOKEN_KEY, t);
  } catch {}
}
export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {}
}

export type RegisterPayload = {
  name: string;
  email: string;
  phone?: string;
  type?: string;
  interest?: string;
  message?: string;
};

/** Submit an early-access registration. Returns true on success. */
export async function registerInterest(p: RegisterPayload): Promise<boolean> {
  if (!HEALTH_API) return false;
  const r = await fetch(`${HEALTH_API}/api/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(p),
  });
  return r.ok;
}

export async function adminLogin(user: string, pass: string): Promise<string | null> {
  if (!HEALTH_API) throw new Error("API not configured");
  const r = await fetch(`${HEALTH_API}/api/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user, pass }),
  });
  if (!r.ok) return null;
  const d = (await r.json()) as { token?: string };
  return d.token ?? null;
}

async function authed(pathname: string, init?: RequestInit) {
  const r = await fetch(`${HEALTH_API}${pathname}`, {
    ...init,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}`, ...(init?.headers || {}) },
  });
  if (r.status === 401) {
    clearToken();
    throw new Error("unauthorized");
  }
  return r;
}

export type Registration = {
  id: number;
  name: string;
  email: string;
  phone: string;
  user_type: string;
  interest: string;
  message: string;
  status: string;
  created_at: string;
};
export type Service = { id: number; name_en: string; name_ar: string; path: string; active: number; sort: number };

export async function getRegistrations(): Promise<{ registrations: Registration[]; total: number }> {
  const r = await authed("/api/admin/registrations");
  return r.json();
}
export async function getServices(): Promise<{ services: Service[] }> {
  const r = await authed("/api/admin/services");
  return r.json();
}
export async function setServiceActive(id: number, active: boolean): Promise<void> {
  await authed(`/api/admin/services/${id}`, { method: "PATCH", body: JSON.stringify({ active }) });
}
export async function addService(name_en: string, name_ar: string, path: string): Promise<void> {
  await authed("/api/admin/services", { method: "POST", body: JSON.stringify({ name_en, name_ar, path }) });
}
