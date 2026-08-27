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
        src={assetPath("/brand/syltra-one-logo.png")}
        alt="Syltra One — One Group. Connected Intelligence."
        width={667}
        height={63}
        priority
        sizes="200px"
        className="h-7 w-auto sm:h-8"
      />
    </Link>
  );
}
