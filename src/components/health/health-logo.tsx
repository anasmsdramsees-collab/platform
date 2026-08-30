import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { assetPath } from "@/lib/base-path";

/** Official SYLTRA HEALTH lockup (approved compact mark + HEALTH). */
export default function HealthLogo({ locale }: { locale: Locale }) {
  return (
    <Link href={`/${locale}/health`} dir="ltr" className="inline-flex items-center" aria-label="SYLTRA HEALTH">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={assetPath("/brand/health-lockup.png")} alt="SYLTRA HEALTH" className="h-6 w-auto sm:h-7" />
    </Link>
  );
}
