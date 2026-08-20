import Image from "next/image";
import Link from "next/link";
import type { Locale } from "@/lib/i18n/config";
import { assetPath } from "@/lib/base-path";

export default function Logo({ locale, className = "" }: { locale: Locale; className?: string }) {
  return (
    <Link
      href={`/${locale}`}
      aria-label="Syltra One"
      className={`block ${className}`}
    >
      <Image
        src={assetPath("/brand/logo.png")}
        alt="Syltra — Smart Living. Seamlessly Connected."
        width={1349}
        height={503}
        priority
        sizes="160px"
        className="h-8 w-auto"
      />
    </Link>
  );
}
