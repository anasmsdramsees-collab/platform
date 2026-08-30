"use client";

import { useState } from "react";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH, HEALTH_BRAND } from "@/lib/health-content";
import { registerInterest } from "@/lib/health-api";

const USER_TYPES: { ar: string; en: string }[] = [
  { ar: "فرد", en: "Individual" },
  { ar: "أحد أفراد الأسرة", en: "Family Member" },
  { ar: "مقدم رعاية", en: "Care Provider" },
  { ar: "عيادة أو مؤسسة", en: "Clinic or Organization" },
  { ar: "شريك تقني", en: "Technology Partner" },
];
const INTERESTS: { ar: string; en: string }[] = [
  { ar: "الصحة اليومية والرياضة واللياقة", en: "Everyday Wellness, Sport & Fitness" },
  { ar: "كبار السن", en: "Older Adults" },
  { ar: "الأمراض المزمنة (السكري، الضغط، القلب)", en: "Chronic Conditions (diabetes, blood pressure, heart)" },
  { ar: "أصحاب الهمم", en: "People of Determination" },
  { ar: "النوم والتعافي", en: "Sleep and Recovery" },
  { ar: "صحة المنزل", en: "Home Wellness" },
  { ar: "شراكة مؤسسية", en: "Institutional Partnership" },
];

export default function ContactForm({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const [sent, setSent] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "", type: "", interest: "", message: "" });

  const label = (v: { ar: string; en: string }) => (ar ? v.ar : v.en);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    // Prefer the API; fall back to a prefilled email if it is not configured.
    let ok = false;
    try {
      ok = await registerInterest(form);
    } catch {
      ok = false;
    }
    if (!ok) {
      const subject = encodeURIComponent(`SYLTRA HEALTH, Early Access, ${form.name || "Interest"}`);
      const bodyLines = [
        `Name: ${form.name}`,
        `Email: ${form.email}`,
        `Phone: ${form.phone}`,
        `User Type: ${form.type}`,
        `Area of Interest: ${form.interest}`,
        "",
        form.message,
      ];
      window.location.href = `mailto:info@syltraone.com?subject=${subject}&body=${encodeURIComponent(bodyLines.join("\n"))}`;
    }
    setBusy(false);
    setSent(true);
  };

  const field = "w-full rounded-lg border border-hairline-strong bg-void-2 px-4 py-3 text-sm text-platinum outline-none transition-colors focus:border-transparent";
  const focusStyle = { boxShadow: `0 0 0 1px ${HEALTH.accent}` };

  if (sent) {
    return (
      <div className="border-s-2 border-hairline-strong ps-5 py-1">
        <p className="font-mono text-[12px] uppercase tracking-widest text-slate">
          {ar ? "تم الاستلام" : "Received"}
        </p>
        <p className="mt-3 text-[15px] leading-relaxed text-chrome">
          {ar
            ? "وصلنا اهتمامك. سنتواصل معك عند توفر المرحلة المناسبة للتجربة أو الشراكة."
            : "We have received your interest. We will contact you when a suitable early-access or partnership stage becomes available."}
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-5">
      <div className="border-s-2 border-hairline-strong ps-4 py-1 text-sm text-chrome">
        {ar ? "لا تكتب أي تشخيص أو قراءة صحية أو تقرير طبي داخل هذا النموذج." : "Do not enter a diagnosis, health reading or medical report in this form."}
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <label className="grid gap-2">
          <span className="text-[13px] text-chrome-dim">{ar ? "الاسم" : "Name"}</span>
          <input required value={form.name} onChange={set("name")} className={field} onFocus={(e) => Object.assign(e.target.style, focusStyle)} onBlur={(e) => (e.target.style.boxShadow = "")} />
        </label>
        <label className="grid gap-2">
          <span className="text-[13px] text-chrome-dim">{ar ? "البريد الإلكتروني" : "Email"}</span>
          <input required type="email" value={form.email} onChange={set("email")} className={field} dir="ltr" onFocus={(e) => Object.assign(e.target.style, focusStyle)} onBlur={(e) => (e.target.style.boxShadow = "")} />
        </label>
        <label className="grid gap-2">
          <span className="text-[13px] text-chrome-dim">{ar ? "رقم الهاتف (اختياري)" : "Phone (optional)"}</span>
          <input value={form.phone} onChange={set("phone")} className={field} dir="ltr" onFocus={(e) => Object.assign(e.target.style, focusStyle)} onBlur={(e) => (e.target.style.boxShadow = "")} />
        </label>
        <label className="grid gap-2">
          <span className="text-[13px] text-chrome-dim">{ar ? "نوع المستخدم" : "User Type"}</span>
          <select required value={form.type} onChange={set("type")} className={field}>
            <option value="">{ar ? "اختر…" : "Choose…"}</option>
            {USER_TYPES.map((o) => <option key={o.en} value={o.en}>{label(o)}</option>)}
          </select>
        </label>
        <label className="grid gap-2 sm:col-span-2">
          <span className="text-[13px] text-chrome-dim">{ar ? "مجال الاهتمام" : "Area of Interest"}</span>
          <select required value={form.interest} onChange={set("interest")} className={field}>
            <option value="">{ar ? "اختر…" : "Choose…"}</option>
            {INTERESTS.map((o) => <option key={o.en} value={o.en}>{label(o)}</option>)}
          </select>
        </label>
        <label className="grid gap-2 sm:col-span-2">
          <span className="text-[13px] text-chrome-dim">{ar ? "الرسالة" : "Message"}</span>
          <textarea rows={4} value={form.message} onChange={set("message")} className={field} onFocus={(e) => Object.assign(e.target.style, focusStyle)} onBlur={(e) => (e.target.style.boxShadow = "")} />
        </label>
      </div>

      <button
        type="submit"
        disabled={busy}
        className="mt-2 inline-flex w-fit items-center rounded-full px-7 py-3 text-sm font-semibold text-void transition-transform hover:scale-[1.02] disabled:opacity-60"
        style={{ backgroundColor: HEALTH.accent }}
      >
        {busy ? (ar ? "جارٍ الإرسال…" : "Sending…") : ar ? "أرسل اهتمامك" : "Submit interest"}
      </button>

      <p className="font-mono text-[11px] text-slate">
        {ar ? HEALTH_BRAND.trustLine.ar : HEALTH_BRAND.trustLine.en}
      </p>
    </form>
  );
}
