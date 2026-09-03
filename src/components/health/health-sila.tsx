"use client";

import { useState, useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH } from "@/lib/health-content";
import { assetPath } from "@/lib/base-path";

type State = "01_welcome" | "03_following" | "04_understood" | "06_serious" | "11_concerned" | "12_reassuring";
type Msg = { role: "user" | "sila"; text: string; state?: State };

/**
 * SILA Health Provider assistant for the /health section (white/green identity).
 * A calm front-of-house helper: it organises readings, reminders and summaries,
 * never diagnoses or changes doses, and always routes urgent symptoms to care.
 * Live answers run through the clinical rules engine + backend; this is the UI.
 */
export default function HealthSila({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const pathname = usePathname() || "";
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, loading]);

  if (pathname.includes("/health/admin")) return null;

  const t = (a: string, e: string) => (ar ? a : e);

  const prompts: { q: [string, string]; a: [string, string]; state: State }[] = [
    {
      q: ["قراءتي الأخيرة", "My latest reading"],
      a: [
        "أقدر أعرض قراءاتك مع القيمة والوحدة والمصدر والوقت عند ربط أجهزتك. لا أفسّرها كتشخيص.",
        "I can show your readings with value, unit, source and time once your devices are linked. I do not interpret them as a diagnosis.",
      ],
      state: "04_understood",
    },
    {
      q: ["تذكير دوائي", "Medication reminder"],
      a: [
        "أذكّرك بدوائك المسجّل باسمه وجرعته كما في وصفتك. لا أبدأ دواءً ولا أغيّر جرعة.",
        "I remind you of your recorded medication by its name and dose as in your prescription. I do not start medication or change a dose.",
      ],
      state: "06_serious",
    },
    {
      q: ["جهّز ملخصاً لطبيبي", "Prepare a summary for my doctor"],
      a: [
        "أجهّز ملخصاً بقراءاتك وأعراضك لإرساله لمقدّم رعايتك، بموافقتك.",
        "I prepare a summary of your readings and symptoms to send to your care provider, with your consent.",
      ],
      state: "12_reassuring",
    },
    {
      q: ["مواعيدي", "My appointments"],
      a: [
        "أذكّرك بمواعيدك وأساعدك تجهّز أسئلتك قبل الزيارة.",
        "I remind you of your appointments and help you prepare your questions before the visit.",
      ],
      state: "04_understood",
    },
  ];

  function reply(userText: string, a: string, state: State) {
    setMsgs((m) => [...m, { role: "user", text: userText }]);
    setLoading(true);
    setTimeout(() => {
      setMsgs((m) => [...m, { role: "sila", text: a, state }]);
      setLoading(false);
    }, 480);
  }

  function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    reply(
      text,
      t(
        "أنا هنا لأساعدك في تنظيم معلوماتك الصحية ومتابعتها وتجهيز ملخص لطبيبك. هذه معلومات عامة، لا تشخيص ولا علاج. عند أي عرض عاجل اتصل بالإسعاف 997.",
        "I am here to help you organise and follow your health information and prepare a summary for your doctor. This is general information, not a diagnosis or treatment. For any urgent symptom, call the ambulance on 997.",
      ),
      "04_understood",
    );
  }

  const last = msgs[msgs.length - 1];
  const expr: State = loading ? "03_following" : last?.role === "sila" && last.state ? last.state : "01_welcome";
  const face = (s: State, size: string, pos = "50% 12%") => (
    <span className={`${size} overflow-hidden rounded-full border border-hairline-strong`} style={{ backgroundColor: "#eef1f0" }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={assetPath(`/brand/sila-health/${s}.png`)} alt="" className="h-full w-full object-cover" style={{ objectPosition: pos }} />
    </span>
  );

  return (
    <div className="fixed bottom-5 end-5 z-50" dir={ar ? "rtl" : "ltr"}>
      {open && (
        <div className="mb-3 flex h-[540px] w-[366px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-2xl border border-hairline-strong shadow-2xl" style={{ backgroundColor: "#ffffff" }}>
          {/* Header */}
          <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
            <div className="flex items-center gap-2.5">
              <span className="relative">
                {face(expr, "flex h-9 w-9")}
                <span className="absolute bottom-0 end-0 h-2.5 w-2.5 rounded-full border-2 border-white" style={{ backgroundColor: HEALTH.accentDim }} />
              </span>
              <div>
                <p className="font-display text-sm font-bold text-platinum">{t("سيلا هيلث", "SILA Health")}</p>
                <p className="text-[10.5px] text-slate">{t("مساعِدة رعاية · لا تشخّص", "Care assistant · does not diagnose")}</p>
              </div>
            </div>
            <button onClick={() => setOpen(false)} aria-label={t("إغلاق", "Close")} className="rounded-md p-1.5 text-slate transition-colors hover:text-platinum">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12" /></svg>
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {msgs.length === 0 && (
              <div className="flex flex-col items-center gap-3 pb-1">
                {face("01_welcome", "h-20 w-20", "50% 10%")}
                <p className="max-w-[90%] text-center text-sm leading-relaxed text-chrome-dim">
                  {t("أهلاً، كيف أقدر أساعدك اليوم؟ أنظّم قراءاتك، أذكّرك بدوائك، وأجهّز ملخصاً لطبيبك.", "Hello, how can I help today? I organise your readings, remind you of your medication, and prepare a summary for your doctor.")}
                </p>
                <div className="flex flex-wrap justify-center gap-2 pt-1">
                  {prompts.map((p) => (
                    <button
                      key={p.q[1]}
                      onClick={() => reply(t(...p.q), t(...p.a), p.state)}
                      className="rounded-full border border-hairline-strong px-3 py-1.5 text-[13px] font-semibold text-chrome transition-colors"
                      style={{ backgroundColor: `rgba(${HEALTH.rgb},0.06)` }}
                    >
                      {t(...p.q)}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <p
                  className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm leading-relaxed ${m.role === "user" ? "rounded-ee-sm text-white" : "rounded-ss-sm text-platinum"}`}
                  style={{ backgroundColor: m.role === "user" ? HEALTH.accentDim : "#eef1f0" }}
                >
                  {m.text}
                </p>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <p className="rounded-2xl rounded-ss-sm px-3 py-2 text-xs text-slate" style={{ backgroundColor: "#eef1f0" }}>{t("سيلا تكتب…", "SILA is typing…")}</p>
              </div>
            )}
          </div>

          {/* Safety strip */}
          <div className="flex items-center justify-between gap-2 border-t border-hairline px-3 py-2" style={{ backgroundColor: `rgba(${HEALTH.rgb},0.05)` }}>
            <p className="text-[10.5px] leading-snug text-slate">{t("معلومات عامة، لا تشخيص. للاستشارة 937 · للطوارئ 997", "General info, not a diagnosis. Advice 937 · Emergency 997")}</p>
            <a href="tel:997" className="shrink-0 rounded-full px-3 py-1 text-[12px] font-bold text-white" style={{ backgroundColor: "#c0392b" }}>997</a>
          </div>

          {/* Input */}
          <div className="border-t border-hairline p-3">
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder={t("اكتب سؤالك…", "Type your question…")}
                className="flex-1 rounded-lg border border-hairline bg-white px-3 py-2 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none"
              />
              <button onClick={send} disabled={!input.trim()} aria-label={t("إرسال", "Send")} className="rounded-lg p-2 text-white transition-opacity disabled:opacity-40" style={{ backgroundColor: HEALTH.accentDim }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Launcher */}
      <div className="flex flex-col items-center gap-2">
        {!open && (
          <span className="rounded-full border px-3.5 py-1.5 text-[11px] font-semibold backdrop-blur-sm" style={{ borderColor: `rgba(${HEALTH.rgb},0.4)`, color: HEALTH.accentDim, backgroundColor: "rgba(255,255,255,0.8)" }}>
            {t("اسأل سيلا", "Ask SILA")}
          </span>
        )}
        <button onClick={() => setOpen((v) => !v)} aria-label={t("مساعِدة سيلا هيلث", "SILA Health assistant")} className="relative flex h-16 w-16 items-center justify-center rounded-full shadow-lg transition-transform hover:scale-105" style={{ backgroundColor: "#fff", border: `1px solid rgba(${HEALTH.rgb},0.35)` }}>
          {open ? (
            <span className="flex h-14 w-14 items-center justify-center rounded-full text-platinum" style={{ backgroundColor: "#eef1f0" }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12" /></svg>
            </span>
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={assetPath("/brand/sila-health/01_welcome.png")} alt="" className="h-16 w-16 rounded-full object-cover" style={{ objectPosition: "50% 10%" }} />
          )}
        </button>
      </div>
    </div>
  );
}
