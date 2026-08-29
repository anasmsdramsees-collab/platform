"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH } from "@/lib/health-content";
import { adminLogin, setToken, HEALTH_API } from "@/lib/health-api";

/** Admin sign-in — authenticates against the SYLTRA HEALTH API worker. */
export default function AdminLogin({ locale }: { locale: Locale }) {
  const router = useRouter();
  const ar = locale === "ar";
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!HEALTH_API) {
      setError(ar ? "الـAPI غير مهيّأ بعد." : "API is not configured yet.");
      return;
    }
    setBusy(true);
    try {
      const token = await adminLogin(user, pass);
      if (!token) {
        setError(ar ? "بيانات الدخول غير صحيحة." : "Invalid credentials.");
      } else {
        setToken(token);
        router.push(`/${locale}/health/admin/dashboard`);
      }
    } catch {
      setError(ar ? "تعذّر الاتصال بالخادم." : "Could not reach the server.");
    }
    setBusy(false);
  };

  const field =
    "w-full rounded-lg border border-hairline-strong bg-void-2 px-4 py-3 text-sm text-platinum outline-none focus:border-transparent";

  return (
    <main className="grid min-h-screen place-items-center bg-void px-5">
      <div className="w-full max-w-sm">
        <div dir="ltr" className="flex items-center justify-center gap-2.5">
          <span className="font-display text-lg font-bold tracking-tight text-platinum">SYLTRA</span>
          <span className="h-4 w-px bg-hairline-strong" />
          <span className="font-display text-base font-bold tracking-[0.22em]" style={{ color: HEALTH.accent }}>HEALTH</span>
        </div>
        <p className="mt-2 text-center font-mono text-[11px] uppercase tracking-[0.2em] text-slate">
          {ar ? "لوحة الإدارة" : "Admin Console"}
        </p>

        <form onSubmit={onSubmit} className="mt-10 grid gap-4">
          <label className="grid gap-2">
            <span className="text-[13px] text-chrome-dim">{ar ? "اسم المستخدم" : "Username"}</span>
            <input value={user} onChange={(e) => setUser(e.target.value)} className={field} dir="ltr" autoComplete="username" />
          </label>
          <label className="grid gap-2">
            <span className="text-[13px] text-chrome-dim">{ar ? "كلمة المرور" : "Password"}</span>
            <input value={pass} onChange={(e) => setPass(e.target.value)} type="password" className={field} dir="ltr" autoComplete="current-password" />
          </label>
          {error && <p className="text-sm" style={{ color: "#d64545" }}>{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="mt-2 inline-flex items-center justify-center rounded-lg px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
            style={{ backgroundColor: HEALTH.accentDim }}
          >
            {busy ? (ar ? "جارٍ الدخول…" : "Signing in…") : ar ? "تسجيل الدخول" : "Sign in"}
          </button>
        </form>

        <p className="mt-8 text-center font-mono text-[11px] text-slate">
          {ar ? "دخول خاص بفريق سيلترا هيلث." : "For the SYLTRA HEALTH team only."}
        </p>
      </div>
    </main>
  );
}
