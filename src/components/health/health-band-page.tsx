import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { HEALTH } from "@/lib/health-content";
import { assetPath } from "@/lib/base-path";

type L = { ar: string; en: string };

const P = "/brand/band/posters";

/** The 16 signals the band surfaces, each with its poster. */
const SIGNALS: { img: string; title: L; note: L }[] = [
  { img: `${P}/01-ecg.png`, title: { ar: "تخطيط القلب", en: "ECG" }, note: { ar: "قراءة إيقاع قلبك بلمسة", en: "Read your heart's rhythm" } },
  { img: `${P}/02-heart-hrv.png`, title: { ar: "النبض وتغيّره", en: "Heart rate & HRV" }, note: { ar: "كل نبضة تحمل معنى", en: "Every beat tells a story" } },
  { img: `${P}/03-spo2.png`, title: { ar: "الأكسجين", en: "Blood oxygen" }, note: { ar: "نَفَسك بلقطة أوضح", en: "Your breath at a glance" } },
  { img: `${P}/04-blood-pressure.png`, title: { ar: "ضغط الدم", en: "Blood pressure" }, note: { ar: "الاتجاه لا اللحظة", en: "The trend, not the moment" } },
  { img: `${P}/05-skin-temperature.png`, title: { ar: "حرارة الجلد", en: "Skin temperature" }, note: { ar: "تغيّرات صغيرة، سياق أوضح", en: "Small shifts, clearer context" } },
  { img: `${P}/06-sleep.png`, title: { ar: "النوم", en: "Sleep" }, note: { ar: "افهم ليلتك، عِش يومك", en: "Understand your night" } },
  { img: `${P}/07-recovery-readiness.png`, title: { ar: "التعافي والجاهزية", en: "Recovery & readiness" }, note: { ar: "اعرف طاقتك قبل أن تبدأ", en: "Know your readiness" } },
  { img: `${P}/08-stress.png`, title: { ar: "التوتر", en: "Stress" }, note: { ar: "لحظة اللَّهفة، ولحظة الهدوء", en: "Tension, and calm" } },
  { img: `${P}/09-activity-calories.png`, title: { ar: "النشاط والسعرات", en: "Activity & calories" }, note: { ar: "كل حركة تُحتسب", en: "Every move counts" } },
  { img: `${P}/10-body-composition.png`, title: { ar: "تكوين الجسم", en: "Body composition" }, note: { ar: "تابع التغيّر عبر الوقت", en: "Track change over time" } },
  { img: `${P}/11-uric-acid.png`, title: { ar: "حمض اليوريك", en: "Uric acid" }, note: { ar: "مؤشر يتصل بمنحنى زمني", en: "A signal over time" } },
  { img: `${P}/12-lipid-trends.png`, title: { ar: "اتجاهات الدهون", en: "Lipid trends" }, note: { ar: "الكوليسترول والدهون عبر الأسابيع", en: "Cholesterol over weeks" } },
  { img: `${P}/13-womens-health.png`, title: { ar: "صحة المرأة", en: "Women's health" }, note: { ar: "من الدورة إلى رحلة الحمل", en: "From cycle to pregnancy" } },
  { img: `${P}/14-ai-health-analysis.png`, title: { ar: "التحليل الذكي", en: "AI analysis" }, note: { ar: "بياناتك في ملخّص مفهوم", en: "Your data, made clear" } },
  { img: `${P}/15-home-sila-integration.png`, title: { ar: "من جسمك إلى بيتك", en: "From body to home" }, note: { ar: "صحتك وبيئة منزلك في نظام واحد", en: "Body and home in one system" } },
  { img: `${P}/16-battery-water.png`, title: { ar: "طاقة تدوم", en: "Lasting energy" }, note: { ar: "مصمّم للحياة اليومية والماء", en: "Built for daily life & water" } },
];

export default function HealthBandPage({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const t = (v: L) => (ar ? v.ar : v.en);
  const contact = `/${locale}/health/contact`;

  return (
    <div dir={ar ? "rtl" : "ltr"}>
      {/* ---------------------------------------------------------- HERO */}
      <section className="w-full border-b border-hairline">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 py-14 sm:px-8 sm:py-20 lg:grid-cols-2 lg:gap-8">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] sm:text-[12px]" style={{ color: HEALTH.accent }}>
              {ar ? "سيلترا هيلث · السوار" : "SYLTRA HEALTH · The Band"}
            </p>
            <h1 className="font-display mt-4 text-balance text-4xl font-extrabold leading-[0.98] text-platinum sm:text-6xl lg:text-7xl">
              {ar ? "سوار يقرأ إشاراتك. بهدوء." : "A band that reads your signals. Quietly."}
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-chrome-dim sm:text-lg">
              {ar
                ? "بلا شاشة تشدّك، وبلا ضجيج. سوار سيلترا يجمع مؤشرات قلبك وأكسجينك ونومك ونشاطك وتعافيك في صورة واحدة واضحة، ويبقى معك طوال اليوم."
                : "No screen pulling at you, no noise. The SYLTRA band brings your heart, oxygen, sleep, activity and recovery into one clear picture, and stays with you all day."}
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href={contact} className="rounded-full px-7 py-3 text-sm font-bold text-white transition-opacity hover:opacity-90" style={{ backgroundColor: HEALTH.accentDim }}>
                {ar ? "سجّل اهتمامك" : "Register interest"}
              </Link>
              <a href="#signals" className="rounded-full border border-hairline-strong px-7 py-3 text-sm font-semibold text-platinum transition-colors hover:border-platinum">
                {ar ? "شاهد المؤشرات" : "See the signals"}
              </a>
            </div>
            <p className="mt-5 font-mono text-[11px] uppercase tracking-widest" style={{ color: HEALTH.accent }}>
              {ar ? "قريباً" : "Coming soon"}
            </p>
          </div>
          <div className="mx-auto w-full max-w-[460px] overflow-hidden rounded-[2rem] border border-hairline shadow-[0_30px_70px_rgba(12,30,22,0.12)]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath("/brand/band/product-hero.png")} alt={ar ? "سوار سيلترا هيلث" : "SYLTRA HEALTH band"} className="block h-auto w-full" />
          </div>
        </div>
      </section>

      {/* -------------------------------------------------- STATEMENT LINE */}
      <section className="w-full border-b border-hairline" style={{ backgroundColor: "#ffffff" }}>
        <div className="mx-auto max-w-4xl px-5 py-16 text-center sm:px-8 sm:py-24">
          <h2 className="font-display text-balance text-3xl font-bold leading-tight text-platinum sm:text-5xl">
            {ar ? "جسمك يرسل إشارات طوال اليوم." : "Your body sends signals all day."}
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-chrome-dim sm:text-lg">
            {ar
              ? "السوار يترجمها بلطف إلى فهم: ماذا يحدث الآن، وما الاتجاه عبر الوقت، ومتى يستحق الأمر انتباهك."
              : "The band turns them gently into understanding: what is happening now, the trend over time, and when something deserves your attention."}
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------- SIGNALS */}
      <section id="signals" className="w-full scroll-mt-20 border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-24">
          <div className="max-w-2xl">
            <p className="font-mono text-[12px] uppercase tracking-[0.16em]" style={{ color: HEALTH.accent }}>
              {ar ? "المؤشرات" : "The signals"}
            </p>
            <h2 className="font-display mt-4 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {ar ? "كل ما يقوله جسمك، في مكان واحد." : "Everything your body says, in one place."}
            </h2>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-x-7 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
            {SIGNALS.map((s) => (
              <div key={s.title.en} className="group">
                <div className="overflow-hidden rounded-2xl border border-hairline" style={{ aspectRatio: "4 / 5", backgroundColor: "#fff" }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={assetPath(s.img)} alt={t(s.title)} className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.03]" />
                </div>
                <div className="mt-4">
                  <span className="block h-px w-8" style={{ background: HEALTH.accent }} aria-hidden />
                  <p className="font-display mt-3 text-lg font-bold text-platinum">{t(s.title)}</p>
                  <p className="mt-1 text-sm leading-relaxed text-chrome-dim">{t(s.note)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------- DESIGN */}
      <section className="w-full border-b border-hairline" style={{ backgroundColor: "#ffffff" }}>
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-2">
          <div className="overflow-hidden rounded-[2rem] border border-hairline">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath(`${P}/16-battery-water.png`)} alt={ar ? "تصميم السوار" : "Band design"} className="block h-auto w-full" />
          </div>
          <div>
            <p className="font-mono text-[12px] uppercase tracking-[0.16em]" style={{ color: HEALTH.accent }}>
              {ar ? "التصميم" : "Design"}
            </p>
            <h2 className="font-display mt-4 text-balance text-3xl font-bold text-platinum sm:text-4xl">
              {ar ? "سوار بلا شاشة، معك بهدوء." : "Screenless. Present, never loud."}
            </h2>
            <p className="mt-5 text-base leading-relaxed text-chrome-dim sm:text-lg">
              {ar
                ? "نسيج أسود مريح يقسم وحدة معدنية واحدة إلى سكّتين فضيتين، والمستشعر البصري خلف الوحدة على الجلد. خفيف على المعصم، مصمّم للحياة اليومية، ويقاوم رذاذ الماء."
                : "A comfortable black weave divides a single metal chassis into two silver rails, with the optical sensor on the back against the skin. Light on the wrist, built for daily life, and water-resistant to splashes."}
            </p>
            <ul className="mt-6 space-y-3">
              {[
                { ar: "بلا شاشة تشتّت — البيانات في تطبيقك", en: "No distracting screen — data lives in your app" },
                { ar: "طاقة تدوم على مدار اليوم", en: "Energy that lasts through the day" },
                { ar: "مريح أثناء النوم والحركة", en: "Comfortable through sleep and movement" },
              ].map((li) => (
                <li key={li.en} className="flex items-start gap-3 text-sm text-chrome">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full" style={{ background: HEALTH.accent }} aria-hidden />
                  {t(li)}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------- WOMEN + HOME */}
      <section className="w-full border-b border-hairline">
        <div className="mx-auto grid max-w-6xl gap-5 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-2">
          {[
            { img: `${P}/13-womens-health.png`, eyebrow: { ar: "لصحة المرأة", en: "For women" }, h: { ar: "من الدورة إلى رحلة الحمل.", en: "From cycle to pregnancy." }, b: { ar: "يربط تغيّرات الدورة وحرارة الجلد بنافذة الخصوبة ورحلة الحمل، بهدوء وخصوصية.", en: "Connects cycle changes and skin temperature to the fertility window and pregnancy, calmly and privately." } },
            { img: `${P}/15-home-sila-integration.png`, eyebrow: { ar: "متصل بالمنزل", en: "Connected home" }, h: { ar: "صحتك وبيئة منزلك في نظام واحد.", en: "Your health and home, one system." }, b: { ar: "عند اتصاله بمنظومة سيلترا، تلتقي إشارات جسمك مع حرارة المنزل وهوائه، ومع مساعِدتك سيلا.", en: "Connected to SYLTRA, your body's signals meet your home's air and climate, and your assistant SILA." } },
          ].map((c) => (
            <div key={c.h.en} className="overflow-hidden rounded-3xl border border-hairline" style={{ backgroundColor: "#fff" }}>
              <div className="overflow-hidden" style={{ aspectRatio: "4 / 3" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={assetPath(c.img)} alt={t(c.h)} className="h-full w-full object-cover" />
              </div>
              <div className="p-6 sm:p-8">
                <p className="font-mono text-[11px] uppercase tracking-[0.16em]" style={{ color: HEALTH.accent }}>{t(c.eyebrow)}</p>
                <h3 className="font-display mt-3 text-balance text-2xl font-bold text-platinum">{t(c.h)}</h3>
                <p className="mt-3 text-sm leading-relaxed text-chrome-dim">{t(c.b)}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* -------------------------------------------------------- SAFETY */}
      <section className="w-full border-b border-hairline" style={{ backgroundColor: `rgba(${HEALTH.rgb},0.06)` }}>
        <div className="mx-auto max-w-3xl px-5 py-12 text-center sm:px-8">
          <p className="text-sm leading-relaxed text-slate">
            {ar
              ? "سوار سيلترا أداة لدعم الفهم والمتابعة، وليس جهازاً تشخيصياً ولا بديلاً عن التقييم أو الرعاية الطبية. عند أي عرض عاجل اتصل بالإسعاف 997."
              : "The SYLTRA band supports understanding and follow-up. It is not a diagnostic device and does not replace medical evaluation or care. For any urgent symptom, call emergency services (997)."}
          </p>
        </div>
      </section>

      {/* ----------------------------------------------------------- CTA */}
      <section className="w-full">
        <div className="mx-auto max-w-4xl px-5 py-20 text-center sm:px-8 sm:py-28">
          <h2 className="font-display text-balance text-3xl font-extrabold text-platinum sm:text-5xl">
            {ar ? "كن أول من يجرّب السوار." : "Be first to try the band."}
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base text-chrome-dim sm:text-lg">
            {ar ? "سجّل اهتمامك ونصلك عند فتح التجربة المبكرة." : "Register your interest and we'll reach out when early access opens."}
          </p>
          <div className="mt-8 flex justify-center">
            <Link href={contact} className="rounded-full px-8 py-3.5 text-sm font-bold text-white transition-opacity hover:opacity-90" style={{ backgroundColor: HEALTH.accentDim }}>
              {ar ? "سجّل اهتمامك" : "Register interest"}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
