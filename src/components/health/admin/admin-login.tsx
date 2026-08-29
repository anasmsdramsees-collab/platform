"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH } from "@/lib/health-content";

/** Admin sign-in shell (UI only — authentication is wired to the backend later). */
export default function AdminLogin({ locale }: { locale: Locale }) {
  const router = useRouter();
  const ar = locale === "ar";
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Placeholder: navigate to the dashboard shell. Real auth comes later.
    router.push(`/${locale}/health/admin/dashboard`);
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
          <button
            type="submit"
            className="mt-2 inline-flex items-center justify-center rounded-lg px-5 py-3 text-sm font-semibold text-white"
            style={{ backgroundColor: HEALTH.accentDim }}
          >
            {ar ? "تسجيل الدخول" : "Sign in"}
          </button>
        </form>

        <p className="mt-8 text-center font-mono text-[11px] text-slate">
          {ar ? "واجهة أولية — الربط بقاعدة البيانات لاحقًا." : "Shell only — connected to the backend later."}
        </p>
      </div>
    </main>
  );
}
