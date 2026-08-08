import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { assetPath } from "@/lib/base-path";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return { title: dict.meta.titleSyntraTv, description: dict.syntraTvPage.hero.subtitle };
}

export default async function SyntraTvPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  const t = dict.syntraTvPage;
  const c = dict.common;

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mx-auto max-w-6xl px-5 pt-8 sm:px-8">
        <Link href={`/${locale}/apps`} className="font-mono text-xs text-slate hover:text-platinum">
          ← {c.backToApps}
        </Link>
      </div>

      {/* Hero */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-16 text-center sm:px-8 sm:py-20">
          <Image
            src={assetPath("/brand/app-icon-tv.png")}
            alt="Syltra TV"
            width={410}
            height={410}
            className="mx-auto h-14 w-auto rounded-xl sm:h-16"
          />
          <p className="mt-6 font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {t.hero.eyebrow}
          </p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {t.hero.title}
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-chrome-dim">{t.hero.subtitle}</p>

          <div className="mt-8 flex flex-col items-center gap-3">
            <a
              href={assetPath("/app/syntra-tv/index.html")}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-md bg-platinum px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-ion" />
              {c.openAppButton}
            </a>
            <p className="max-w-sm font-mono text-[11px] text-slate">
              {c.livePreviewLabel} — {c.livePreviewNote}
            </p>
          </div>

          <p className="mt-10 font-mono text-[11px] uppercase tracking-widest text-slate">
            {c.specsLabel}
          </p>
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
            {t.specs.map((s) => (
              <span
                key={s}
                className="rounded-full border border-hairline px-2.5 py-1 font-mono text-[10.5px] text-chrome-dim"
              >
                {s}
              </span>
            ))}
          </div>

          <p className="mt-8 font-mono text-[11px] uppercase tracking-widest text-slate">
            {c.appsLabel}
          </p>
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
            {t.apps.map((a) => (
              <span
                key={a}
                className="rounded-full border border-hairline px-2.5 py-1 font-mono text-[10.5px] text-chrome-dim"
              >
                {a}
              </span>
            ))}
          </div>

          <p className="mt-8 font-mono text-[11px] uppercase tracking-widest text-slate">
            {c.platformsLabel}
          </p>
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
            {t.platforms.map((p) => (
              <span
                key={p}
                className="rounded-full border border-hairline px-2.5 py-1 font-mono text-[10.5px] text-chrome-dim"
              >
                {p}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="grid grid-cols-1 gap-px overflow-hidden bg-hairline sm:grid-cols-2 lg:grid-cols-3">
            {t.features.map((f, i) => (
              <div key={f.name} className="bg-void p-6">
                <p className="font-mono text-xs text-ion">{String(i + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-semibold text-platinum">{f.name}</p>
                <p className="mt-2 text-sm text-chrome-dim">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* On screen */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 sm:px-8">
          <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {t.screen.eyebrow}
          </p>
          <h2 className="font-display mt-3 text-3xl font-bold text-platinum sm:text-4xl">
            {t.screen.title}
          </h2>
          <div className="mt-10 divide-y divide-hairline border-y border-hairline">
            {t.screen.items.map((item) => (
              <div key={item.name} className="flex flex-col gap-1 py-5 sm:flex-row sm:items-baseline sm:justify-between">
                <p className="font-mono text-sm text-platinum">{item.name}</p>
                <p className="text-sm text-chrome-dim sm:max-w-md sm:text-end">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-b border-hairline">
        <div className="mx-auto max-w-4xl px-5 py-20 sm:px-8">
          <p className="text-center font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
            {c.howItWorksLabel}
          </p>
          <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-3">
            {t.howItWorks.map((step) => (
              <div key={step.step}>
                <p className="font-mono text-sm text-ion">{step.step}</p>
                <p className="mt-3 font-semibold text-platinum">{step.title}</p>
                <p className="mt-2 text-sm text-chrome-dim">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Status / CTA */}
      <section>
        <div className="mx-auto max-w-3xl px-5 py-24 text-center sm:px-8">
          <p className="font-mono text-xs text-slate">{t.status}</p>
          <h2 className="font-display mt-4 text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {c.notifyTitle}
          </h2>
          <p className="mt-4 text-chrome-dim">{c.notifySubtitle}</p>
          <Link
            href={`/${locale}/contact`}
            className="mt-8 inline-block rounded-md bg-platinum px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
          >
            {c.notifyButton}
          </Link>
        </div>
      </section>
    </div>
  );
}
