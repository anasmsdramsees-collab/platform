"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH } from "@/lib/health-content";
import {
  getRegistrations,
  getServices,
  setServiceActive,
  clearToken,
  getToken,
  HEALTH_API,
  type Registration,
  type Service,
} from "@/lib/health-api";

type Section = "registrations" | "services" | "settings";

export default function AdminDashboard({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const router = useRouter();
  const [section, setSection] = useState<Section>("registrations");
  const [regs, setRegs] = useState<Registration[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const [r, s] = await Promise.all([getRegistrations(), getServices()]);
      setRegs(r.registrations || []);
      setServices(s.services || []);
    } catch (e) {
      if (String(e).includes("unauthorized")) {
        router.push(`/${locale}/health/admin`);
        return;
      }
      setErr(ar ? "تعذّر تحميل البيانات." : "Could not load data.");
    }
    setLoading(false);
  }, [ar, locale, router]);

  useEffect(() => {
    if (!HEALTH_API || !getToken()) {
      router.push(`/${locale}/health/admin`);
      return;
    }
    load();
  }, [load, locale, router]);

  const signOut = () => {
    clearToken();
    router.push(`/${locale}/health/admin`);
  };

  const toggle = async (svc: Service) => {
    setServices((prev) => prev.map((s) => (s.id === svc.id ? { ...s, active: svc.active ? 0 : 1 } : s)));
    try {
      await setServiceActive(svc.id, !svc.active);
    } catch {
      load();
    }
  };

  const nav: { key: Section; label: string }[] = [
    { key: "registrations", label: ar ? "التسجيلات" : "Registrations" },
    { key: "services", label: ar ? "الخدمات" : "Services" },
    { key: "settings", label: ar ? "الإعدادات" : "Settings" },
  ];
  const navBtn = (active: boolean) =>
    `flex w-full items-center rounded-lg px-3 py-2.5 text-sm transition-colors ${active ? "bg-graphite-2 text-platinum" : "text-chrome-dim hover:text-platinum"}`;

  const weekAgo = Date.now() - 7 * 864e5;
  const stats = {
    total: regs.length,
    week: regs.filter((r) => new Date(r.created_at).getTime() > weekAgo).length,
    pilot: regs.filter((r) => /pilot|clinic|organization|مؤسس|عيادة/i.test(`${r.user_type} ${r.interest}`)).length,
    providers: regs.filter((r) => /care provider|مقدم رعاية/i.test(r.user_type)).length,
  };

  return (
    <div className="flex min-h-screen bg-void text-platinum">
      <aside className="hidden w-60 flex-none border-e border-hairline p-5 md:block">
        <div dir="ltr" className="flex items-center gap-2">
          <span className="font-display text-base font-bold text-platinum">SYLTRA</span>
          <span className="font-display text-sm font-bold tracking-[0.2em]" style={{ color: HEALTH.accent }}>HEALTH</span>
        </div>
        <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-slate">{ar ? "الإدارة" : "Admin"}</p>
        <nav className="mt-8 grid gap-1">
          {nav.map((n) => (
            <button key={n.key} type="button" onClick={() => setSection(n.key)} className={navBtn(section === n.key)}>{n.label}</button>
          ))}
        </nav>
        <div className="mt-8 border-t border-hairline pt-4">
          <button type="button" onClick={signOut} className="text-sm text-chrome-dim transition-colors hover:text-platinum">
            {ar ? "تسجيل الخروج" : "Sign out"}
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-x-auto">
        <header className="flex items-center justify-between border-b border-hairline px-5 py-4 sm:px-8">
          <h1 className="font-display text-lg font-bold text-platinum">{nav.find((n) => n.key === section)?.label}</h1>
          <div className="flex items-center gap-3">
            <button type="button" onClick={load} className="font-mono text-[11px] uppercase tracking-widest text-slate transition-colors hover:text-platinum">
              {ar ? "تحديث" : "Refresh"}
            </button>
            <div className="flex gap-2 md:hidden">
              {nav.map((n) => (
                <button key={n.key} type="button" onClick={() => setSection(n.key)} className={`rounded-md px-2.5 py-1 text-xs ${section === n.key ? "bg-graphite-2 text-platinum" : "text-slate"}`}>{n.label}</button>
              ))}
            </div>
          </div>
        </header>

        <div className="px-5 py-6 sm:px-8">
          {err && <p className="mb-4 text-sm" style={{ color: "#d64545" }}>{err}</p>}

          {section === "registrations" && (
            <div className="grid gap-8">
              <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
                <Stat label={ar ? "الإجمالي" : "Total"} value={String(stats.total)} />
                <Stat label={ar ? "هذا الأسبوع" : "This week"} value={String(stats.week)} />
                <Stat label={ar ? "طلبات تجريبية" : "Pilot requests"} value={String(stats.pilot)} />
                <Stat label={ar ? "مقدمو رعاية" : "Providers"} value={String(stats.providers)} />
              </div>
              <div className="overflow-x-auto border-t border-hairline">
                <table className="w-full min-w-[720px] text-sm">
                  <thead>
                    <tr className="border-b border-hairline font-mono text-[11px] uppercase tracking-widest text-slate">
                      {(ar ? ["الاسم", "البريد", "الهاتف", "النوع", "الاهتمام", "التاريخ"] : ["Name", "Email", "Phone", "Type", "Interest", "Date"]).map((c) => (
                        <th key={c} className="py-3 pe-4 text-start font-normal">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr><td colSpan={6} className="py-16 text-center text-sm text-slate">{ar ? "جارٍ التحميل…" : "Loading…"}</td></tr>
                    ) : regs.length === 0 ? (
                      <tr><td colSpan={6} className="py-16 text-center text-sm text-slate">{ar ? "لا توجد تسجيلات بعد." : "No registrations yet."}</td></tr>
                    ) : (
                      regs.map((r) => (
                        <tr key={r.id} className="border-b border-hairline">
                          <td className="py-3 pe-4 text-platinum">{r.name}</td>
                          <td className="py-3 pe-4 text-chrome-dim" dir="ltr">{r.email}</td>
                          <td className="py-3 pe-4 text-chrome-dim" dir="ltr">{r.phone || "-"}</td>
                          <td className="py-3 pe-4 text-chrome-dim">{r.user_type || "-"}</td>
                          <td className="py-3 pe-4 text-chrome-dim">{r.interest || "-"}</td>
                          <td className="py-3 pe-4 text-slate" dir="ltr">{new Date(r.created_at).toLocaleDateString("en-GB")}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {section === "services" && (
            <div className="border-t border-hairline">
              {loading ? (
                <p className="py-16 text-center text-sm text-slate">{ar ? "جارٍ التحميل…" : "Loading…"}</p>
              ) : (
                services.map((s) => (
                  <div key={s.id} className="flex items-center justify-between border-b border-hairline py-4">
                    <div>
                      <p className="font-semibold text-platinum">{ar ? s.name_ar : s.name_en}</p>
                      <Link href={`/${locale}/health${s.path}`} dir="ltr" className="font-mono text-[11px] text-slate transition-colors hover:text-platinum">/health{s.path}</Link>
                    </div>
                    <button
                      type="button"
                      onClick={() => toggle(s)}
                      className="rounded-full px-3 py-1 text-[11px] font-medium"
                      style={s.active ? { backgroundColor: `rgba(${HEALTH.rgb},0.14)`, color: HEALTH.accentDim } : { backgroundColor: "var(--color-graphite-2)", color: "var(--color-slate)" }}
                    >
                      {s.active ? (ar ? "مُفعّلة" : "Active") : (ar ? "مسودّة" : "Draft")}
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {section === "settings" && (
            <div className="max-w-lg border-s-2 border-hairline-strong ps-4">
              <p className="text-sm leading-relaxed text-chrome-dim">
                {ar
                  ? "بيانات الدخول تُدار كأسرار في Cloudflare (ADMIN_USER / ADMIN_PASSWORD). إدارة المستخدمين والصلاحيات تُضاف لاحقًا."
                  : "Credentials are managed as Cloudflare secrets (ADMIN_USER / ADMIN_PASSWORD). User and role management will be added later."}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-s-2 border-hairline-strong ps-4">
      <p className="font-mono text-[11px] uppercase tracking-widest text-slate">{label}</p>
      <p className="font-display mt-1 text-2xl font-bold text-platinum">{value}</p>
    </div>
  );
}
