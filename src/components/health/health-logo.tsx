import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { assetPath } from "@/lib/base-path";
import { HEALTH } from "@/lib/health-content";

/**
 * SYLTRA HEALTH lockup: the SYLTRA wordmark + a green HEALTH wordmark, split by
 * a hairline. The SYLTRA mark is drawn as a theme-coloured CSS mask (from the
 * white logo asset) so it stays visible on both light and dark backgrounds.
 * Always LTR so the lockup never reverses under RTL.
 */
export default function HealthLogo({ locale }: { locale: Locale }) {
  const mask = assetPath("/brand/logo.png");
  return (
    <Link
      href={`/${locale}/health`}
      dir="ltr"
      className="group inline-flex items-center gap-2.5"
      aria-label="SYLTRA HEALTH"
    >
      <span
        className="block h-[26px] w-[71px]"
        style={{
          backgroundColor: "var(--color-platinum)",
          WebkitMaskImage: `url(${mask})`,
          maskImage: `url(${mask})`,
          WebkitMaskSize: "contain",
          maskSize: "contain",
          WebkitMaskRepeat: "no-repeat",
          maskRepeat: "no-repeat",
          WebkitMaskPosition: "center",
          maskPosition: "center",
        }}
        aria-hidden
      />
      <span className="h-4 w-px bg-hairline-strong" aria-hidden />
      <span
        className="font-display text-[15px] font-bold tracking-[0.22em] sm:text-base"
        style={{ color: HEALTH.accent }}
      >
        HEALTH
      </span>
    </Link>
  );
}
