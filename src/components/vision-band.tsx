import type { Locale } from "@/lib/i18n/config";
import { assetPath } from "@/lib/base-path";

/**
 * Prominent "Aligned with Saudi Vision 2030" band. Large official emblem +
 * headline. Uses the Syltra One silver accent.
 */
export default function VisionBand({ locale }: { locale: Locale }) {
  return (
    <section className="relative overflow-hidden border-b border-hairline">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(70% 120% at 50% 0%, rgba(191,198,208,0.10), transparent 62%)",
        }}
        aria-hidden
      />
      <div className="relative mx-auto max-w-4xl px-5 py-24 text-center sm:px-8 sm:py-28">
        <p className="font-mono text-[12px] uppercase tracking-[0.14em]" style={{ color: "#BFC6D0" }}>
          {locale === "ar" ? "التزام وطني" : "National commitment"}
        </p>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={assetPath("/brand/vision-2030.png")}
          alt={locale === "ar" ? "رؤية المملكة العربية السعودية 2030" : "Saudi Vision 2030"}
          className="mx-auto mt-8 h-24 w-auto sm:h-36"
        />
        <h2 className="font-display mt-10 text-balance text-3xl font-bold leading-tight text-platinum sm:text-5xl">
          {locale === "ar"
            ? "داعمون لرؤية المملكة العربية السعودية 2030"
            : "Proud supporters of Saudi Vision 2030"}
        </h2>
        <p className="mx-auto mt-5 max-w-2xl text-balance text-base text-chrome-dim sm:text-lg">
          {locale === "ar"
            ? "نبني تقنية وطنية تخدم أهداف التحوّل الرقمي وجودة الحياة والاقتصاد المتنوّع في المملكة."
            : "Building national technology that serves the Kingdom's digital-transformation, quality-of-life and diversified-economy goals."}
        </p>
      </div>
    </section>
  );
}
