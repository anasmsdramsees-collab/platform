"use client";

import { useState } from "react";
import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH } from "@/lib/health-content";

type Section = "registrations" | "services" | "settings";

const SERVICES = [
  { name: { ar: "الصحة اليومية", en: "Everyday Wellness" }, path: "/individuals", active: true },
  { name: { ar: "كبار السن", en: "Older Adults" }, path: "/older-adults", active: true },
  { name: { ar: "ضغط الدم", en: "Blood Pressure" }, path: "/chronic-conditions/blood-pressure", active: true },
  { name: { ar: "السكري", en: "Diabetes" }, path: "/chronic-conditions/diabetes", active: true },
  { name: { ar: "النوم والتعافي", en: "Sleep & Recovery" }, path: "/sleep-recovery", active: true },
  { name: { ar: "صحة المنزل", en: "Home Wellness" }, path: "/home-wellness", active: true },
  { name: { ar: "لمقدمي الرعاية", en: "For Care Providers" }, path: "/care-providers", active: false },
];

export default function AdminDashboard({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const [section, setSection] = useState<Section>("registrations");

  const nav: { key: Section; label: string }[] = [
    { key: "registrations", label: ar ? "التسجيلات" : "Registrations" },
    { key: "services", label: ar ? "الخدمات" : "Services" },
    { key: "settings", label: ar ? "الإعدادات" : "Settings" },
  ];

  const navBtn = (active: boolean) =>
    `flex w-full items-center rounded-lg px-3 py-2.5 text-sm transition-colors ${
      active ? "bg-graphite-2 text-platinum" : "text-chrome-dim hover:text-platinum"
    }`;

  return (
    <div className="flex min-h-screen bg-void text-platinum">
      {/* Sidebar */}
      <aside className="hidden w-60 flex-none border-e border-hairline p-5 md:block">
        <div dir="ltr" className="flex items-center gap-2">
          <span className="font-display text-base font-bold text-platinum">SYLTRA</span>
          <span className="font-display text-sm font-bold tracking-[0.2em]" style={{ color: HEALTH.accent }}>HEALTH</span>
        </div>
        <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-slate">{ar ? "الإدارة" : "Admin"}</p>

        <nav className="mt-8 grid gap-1">
          {nav.map((n) => (
            <button key={n.key} type="button" onClick={() => setSection(n.key)} className={navBtn(section === n.key)}>
              {n.label}
            </button>
          ))}
        </nav>

        <div className="mt-8 border-t border-hairline pt-4">
          <Link href={`/${locale}/health/admin`} className="text-sm text-chrome-dim transition-colors hover:text-platinum">
            {ar ? "تسجيل الخروج" : "Sign out"}
          </Link>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-x-auto">
        {/* Top bar */}
        <header className="flex items-center justify-between border-b border-hairline px-5 py-4 sm:px-8">
          <h1 className="font-display text-lg font-bold text-platinum">
            {nav.find((n) => n.key === section)?.label}
          </h1>
          {/* Mobile section switch */}
          <div className="flex gap-2 md:hidden">
            {nav.map((n) => (
              <button key={n.key} type="button" onClick={() => setSection(n.key)} className={`rounded-md px-2.5 py-1 text-xs ${section === n.key ? "bg-graphite-2 text-platinum" : "text-slate"}`}>
                {n.label}
              </button>
            ))}
          </div>
        </header>

        <div className="px-5 py-6 sm:px-8">
          {section === "registrations" && <Registrations ar={ar} />}
          {section === "services" && <Services ar={ar} locale={locale} />}
          {section === "settings" && <Settings ar={ar} />}
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

function Registrations({ ar }: { ar: boolean }) {
  const cols = ar
    ? ["الاسم", "البريد", "النوع", "الاهتمام", "التاريخ", "الحالة"]
    : ["Name", "Email", "Type", "Interest", "Date", "Status"];
  return (
    <div className="grid gap-8">
      <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
        <Stat label={ar ? "الإجمالي" : "Total"} value="0" />
        <Stat label={ar ? "هذا الأسبوع" : "This week"} value="0" />
        <Stat label={ar ? "طلبات تجريبية" : "Pilot requests"} value="0" />
        <Stat label={ar ? "مقدمو رعاية" : "Providers"} value="0" />
      </div>

      <div className="overflow-x-auto border-t border-hairline">
        <table className="w-full min-w-[640px] text-start text-sm">
          <thead>
            <tr className="border-b border-hairline text-start font-mono text-[11px] uppercase tracking-widest text-slate">
              {cols.map((c) => (
                <th key={c} className="py-3 pe-4 text-start font-normal">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={cols.length} className="py-16 text-center text-sm text-slate">
                {ar
                  ? "لا توجد تسجيلات بعد. ستظهر هنا بمجرد ربط النموذج بقاعدة البيانات."
                  : "No registrations yet. They will appear here once the form is connected to the database."}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Services({ ar, locale }: { ar: boolean; locale: Locale }) {
  return (
    <div className="grid gap-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-chrome-dim">{ar ? "خدمات HEALTH المعروضة على الموقع." : "HEALTH services shown on the site."}</p>
        <button type="button" className="rounded-lg px-4 py-2 text-sm font-semibold text-white" style={{ backgroundColor: HEALTH.accentDim }}>
          {ar ? "إضافة خدمة" : "Add service"}
        </button>
      </div>

      <div className="border-t border-hairline">
        {SERVICES.map((s) => (
          <div key={s.path} className="flex items-center justify-between border-b border-hairline py-4">
            <div>
              <p className="font-semibold text-platinum">{ar ? s.name.ar : s.name.en}</p>
              <Link href={`/${locale}/health${s.path}`} dir="ltr" className="font-mono text-[11px] text-slate transition-colors hover:text-platinum">
                /health{s.path}
              </Link>
            </div>
            <span
              className="rounded-full px-3 py-1 text-[11px] font-medium"
              style={
                s.active
                  ? { backgroundColor: `rgba(${HEALTH.rgb},0.14)`, color: HEALTH.accentDim }
                  : { backgroundColor: "var(--color-graphite-2)", color: "var(--color-slate)" }
              }
            >
              {s.active ? (ar ? "مُفعّلة" : "Active") : (ar ? "مسودّة" : "Draft")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Settings({ ar }: { ar: boolean }) {
  return (
    <div className="max-w-lg border-s-2 border-hairline-strong ps-4">
      <p className="text-sm leading-relaxed text-chrome-dim">
        {ar
          ? "الإعدادات (المستخدمون، الصلاحيات، ربط قاعدة البيانات والإشعارات) ستُضاف عند بناء الباك-إند."
          : "Settings (users, roles, database connection and notifications) will be added when the backend is built."}
      </p>
    </div>
  );
}
