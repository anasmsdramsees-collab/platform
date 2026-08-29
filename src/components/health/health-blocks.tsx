import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { assetPath } from "@/lib/base-path";
import { HEALTH } from "@/lib/health-content";
import type { Block, HButton } from "@/lib/health-pages";
import HealthHeroGraphic from "./health-hero-graphic";
import IntegrationsGrid from "./integrations-grid";

function href(locale: Locale, h: string) {
  return h.startsWith("#") ? h : `/${locale}${h}`;
}

function Buttons({ locale, buttons, center }: { locale: Locale; buttons: HButton[]; center?: boolean }) {
  return (
    <div className={`mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 ${center ? "justify-center" : ""}`}>
      {buttons.map((b, i) =>
        b.primary ? (
          <Link
            key={i}
            href={href(locale, b.href)}
            className="inline-flex items-center rounded-full px-6 py-3 text-sm font-semibold text-void transition-transform hover:scale-[1.02]"
            style={{ backgroundColor: HEALTH.accent }}
          >
            {locale === "ar" ? b.label.ar : b.label.en}
          </Link>
        ) : (
          <Link
            key={i}
            href={href(locale, b.href)}
            className="group inline-flex items-center gap-2 text-sm font-semibold text-platinum"
          >
            {locale === "ar" ? b.label.ar : b.label.en}
            <span
              className="h-px w-6 transition-all group-hover:w-10"
              style={{ backgroundColor: HEALTH.accent }}
            />
          </Link>
        )
      )}
    </div>
  );
}

export default function HealthBlocks({ blocks, locale }: { blocks: Block[]; locale: Locale }) {
  const ar = locale === "ar";
  const t = (v: { ar: string; en: string }) => (ar ? v.ar : v.en);

  return (
    <>
      {blocks.map((block, i) => {
        switch (block.kind) {
          // ---------------------------------------------------------- HERO
          case "hero": {
            const withGraphic = block.graphic === "connect" || block.graphic === "ring";
            if (block.graphic === "scene") {
              return (
                <section key={i} className="relative overflow-hidden border-b border-hairline">
                  <div
                    className="pointer-events-none absolute inset-0"
                    style={{ background: `radial-gradient(60% 70% at 50% 0%, rgba(${HEALTH.rgb},0.10), transparent 65%)` }}
                    aria-hidden
                  />
                  <div className="relative mx-auto max-w-4xl px-5 pt-16 text-center sm:px-8 sm:pt-24">
                    {block.eyebrow && (
                      <p className="font-mono text-[12px] uppercase tracking-[0.16em]" style={{ color: HEALTH.accent }}>
                        {t(block.eyebrow)}
                      </p>
                    )}
                    <h1 className="font-display mx-auto mt-4 max-w-3xl text-balance text-4xl font-bold leading-[1.05] text-platinum sm:text-5xl lg:text-6xl">
                      {t(block.headline)}
                    </h1>
                    <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-chrome-dim sm:text-lg">
                      {t(block.body)}
                    </p>
                    {block.buttons && (
                      <div className="flex justify-center">
                        <Buttons locale={locale} buttons={block.buttons} center />
                      </div>
                    )}
                  </div>
                  <div className="relative mx-auto mt-12 max-w-6xl px-5 pb-16 sm:px-8 sm:pb-24">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={assetPath("/brand/health-hero.jpg")}
                      alt={ar ? "لوحة سيلترا هيلث على الحائط مع الساعات والأجهزة القابلة للارتداء في منزل ذكي" : "SYLTRA HEALTH wall dashboard with watches and wearables in a connected smart home"}
                      className="w-full rounded-2xl border border-hairline shadow-2xl"
                    />
                    <p className="mt-5 flex items-center justify-center gap-2 font-mono text-[12px] text-slate">
                      <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: HEALTH.accent }} aria-hidden />
                      {ar ? "تكامل مستهدف · قيد التطوير" : "Target integrations · In development"}
                    </p>
                  </div>
                </section>
              );
            }
            return (
              <section key={i} className="relative overflow-hidden border-b border-hairline">
                <div
                  className="pointer-events-none absolute inset-0"
                  style={{ background: `radial-gradient(60% 90% at ${ar ? "80%" : "20%"} 0%, rgba(${HEALTH.rgb},0.10), transparent 60%)` }}
                  aria-hidden
                />
                <div className={`relative mx-auto grid max-w-6xl items-center gap-10 px-5 py-16 sm:px-8 sm:py-24 ${withGraphic ? "lg:grid-cols-2 lg:gap-8" : ""}`}>
                  <div>
                    {block.eyebrow && (
                      <p className="font-mono text-[12px] uppercase tracking-[0.16em]" style={{ color: HEALTH.accent }}>
                        {t(block.eyebrow)}
                      </p>
                    )}
                    <h1 className="font-display mt-4 text-balance text-4xl font-bold leading-[1.05] text-platinum sm:text-5xl lg:text-6xl">
                      {t(block.headline)}
                    </h1>
                    <p className="mt-6 max-w-xl text-base leading-relaxed text-chrome-dim sm:text-lg">
                      {t(block.body)}
                    </p>
                    {block.buttons && <Buttons locale={locale} buttons={block.buttons} />}
                    {withGraphic && (
                      <p className="mt-8 flex items-center gap-2 font-mono text-[12px] text-slate">
                        <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: HEALTH.accent }} aria-hidden />
                        {ar ? "تكامل مستهدف · قيد التطوير" : "Target integrations · In development"}
                      </p>
                    )}
                  </div>
                  {withGraphic && (
                    <div className="relative">
                      <HealthHeroGraphic className="mx-auto w-full max-w-[560px]" />
                    </div>
                  )}
                </div>
              </section>
            );
          }

          // ------------------------------------------------------- SECTION
          case "section":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-4xl px-5 py-14 sm:px-8 sm:py-20">
                  {block.eyebrow && (
                    <p className="font-mono text-[12px] uppercase tracking-[0.14em]" style={{ color: HEALTH.accent }}>
                      {t(block.eyebrow)}
                    </p>
                  )}
                  <div className="mt-4 h-px w-8" style={{ backgroundColor: HEALTH.accent }} />
                  {block.headline && (
                    <h2 className="font-display mt-6 text-balance text-3xl font-bold text-platinum sm:text-4xl">
                      {t(block.headline)}
                    </h2>
                  )}
                  {block.body && (
                    <p className="mt-5 max-w-2xl text-base leading-relaxed text-chrome-dim">{t(block.body)}</p>
                  )}
                </div>
              </section>
            );

          // --------------------------------------------------------- CARDS
          case "cards":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8 sm:py-24">
                  {block.headline && (
                    <h2 className="font-display max-w-2xl text-balance text-3xl font-bold text-platinum sm:text-4xl">
                      {t(block.headline)}
                    </h2>
                  )}
                  {block.body && (
                    <p className="mt-4 max-w-2xl text-sm leading-relaxed text-chrome-dim sm:text-base">{t(block.body)}</p>
                  )}
                  <div className="mt-10 grid grid-cols-1 border-s border-t border-hairline sm:grid-cols-2 lg:grid-cols-3">
                    {block.items.map((it, k) => (
                      <div key={k} className="border-b border-e border-hairline p-6 sm:p-8">
                        <div className="h-px w-8" style={{ backgroundColor: HEALTH.accent }} />
                        <h3 className="font-display mt-5 text-lg font-bold text-platinum">{t(it.title)}</h3>
                        <p className="mt-3 text-sm leading-relaxed text-chrome-dim">{t(it.body)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            );

          // ---------------------------------------------------------- LIST
          case "list":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-4xl px-5 py-14 sm:px-8 sm:py-20">
                  {block.headline && (
                    <h2 className="font-display text-balance text-2xl font-bold text-platinum sm:text-3xl">{t(block.headline)}</h2>
                  )}
                  {block.body && <p className="mt-4 max-w-2xl text-sm leading-relaxed text-chrome-dim">{t(block.body)}</p>}
                  <ul className="mt-8 border-t border-hairline">
                    {block.items.map((it, k) => (
                      <li key={k} className="flex items-start gap-4 border-b border-hairline py-4">
                        <span className="mt-2 h-px w-6 flex-none" style={{ backgroundColor: HEALTH.accent }} aria-hidden />
                        <span className="text-[15px] leading-relaxed text-chrome">{t(it)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </section>
            );

          // ------------------------------------------------------- JOURNEY
          case "journey":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8 sm:py-24">
                  {block.headline && (
                    <h2 className="font-display max-w-2xl text-balance text-3xl font-bold text-platinum sm:text-4xl">{t(block.headline)}</h2>
                  )}
                  {block.body && <p className="mt-4 max-w-2xl text-sm leading-relaxed text-chrome-dim sm:text-base">{t(block.body)}</p>}
                  <ol className="mt-10 grid grid-cols-1 gap-px border border-hairline bg-hairline sm:grid-cols-2 lg:grid-cols-4">
                    {block.steps.map((s, k) => (
                      <li key={k} className="bg-void p-6 sm:p-7">
                        <span className="font-mono text-sm" style={{ color: HEALTH.accent }}>{String(k + 1).padStart(2, "0")}</span>
                        <h3 className="font-display mt-3 text-base font-bold text-platinum">{t(s.label)}</h3>
                        <p className="mt-2 text-sm leading-relaxed text-chrome-dim">{t(s.body)}</p>
                      </li>
                    ))}
                  </ol>
                </div>
              </section>
            );

          // --------------------------------------------------------- STEPS
          case "steps":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-5xl px-5 py-14 sm:px-8 sm:py-24">
                  <div className="border-t border-hairline">
                    {block.steps.map((s, k) => (
                      <div key={k} className="grid grid-cols-[auto_1fr] gap-x-6 border-b border-hairline py-8 sm:grid-cols-[120px_1fr]">
                        <span className="font-mono text-2xl font-bold" style={{ color: HEALTH.accent }}>{String(k + 1).padStart(2, "0")}</span>
                        <div>
                          <h3 className="font-display text-xl font-bold text-platinum">{t(s.title)}</h3>
                          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-chrome-dim sm:text-base">{t(s.body)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            );

          // -------------------------------------------------------- SAFETY
          case "safety":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-4xl px-5 py-10 sm:px-8">
                  <div
                    className="border-s-2 p-6"
                    style={{ borderColor: HEALTH.accent, background: `rgba(${HEALTH.rgb},0.05)` }}
                  >
                    <p className="font-mono text-[11px] uppercase tracking-[0.14em]" style={{ color: HEALTH.accent }}>
                      {ar ? "ملاحظة سلامة" : "Safety note"}
                    </p>
                    <p className="mt-3 text-sm leading-relaxed text-chrome">{t(block.text)}</p>
                  </div>
                </div>
              </section>
            );

          // --------------------------------------------------------- LINKS
          case "links":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-4xl px-5 py-12 sm:px-8">
                  {block.headline && (
                    <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{t(block.headline)}</p>
                  )}
                  <div className="mt-5 flex flex-wrap gap-3">
                    {block.items.map((it, k) => (
                      <Link
                        key={k}
                        href={href(locale, it.href)}
                        className="inline-flex items-center gap-2 rounded-full border border-hairline-strong px-5 py-2.5 text-sm text-platinum transition-colors hover:text-platinum"
                      >
                        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: HEALTH.accent }} aria-hidden />
                        {t(it.label)}
                      </Link>
                    ))}
                  </div>
                </div>
              </section>
            );

          // -------------------------------------------------- INTEGRATIONS
          case "integrations":
            return <IntegrationsGrid key={i} locale={locale} />;

          // ----------------------------------------------------------- CTA
          case "cta":
            return (
              <section key={i} className="border-b border-hairline">
                <div className="mx-auto max-w-5xl px-5 py-16 text-center sm:px-8 sm:py-24">
                  <h2 className="font-display mx-auto max-w-2xl text-balance text-3xl font-bold text-platinum sm:text-4xl">
                    {t(block.headline)}
                  </h2>
                  {block.body && (
                    <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-chrome-dim">{t(block.body)}</p>
                  )}
                  <Buttons locale={locale} buttons={block.buttons} center />
                </div>
              </section>
            );
        }
      })}
    </>
  );
}
