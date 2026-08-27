"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { assetPath } from "@/lib/base-path";

// Official horizontal lockups (icon + SYLTRA + suffix). The suffix is "ONE" for
// the group and the division name (in its colour) on each division.
const LOCKUPS: Record<string, { src: string; w: number; h: number; label: string }> = {
  one: { src: "/brand/lockups/one.png", w: 3000, h: 438, label: "Syltra One" },
  life: { src: "/brand/lockups/life.png", w: 3000, h: 434, label: "Syltra Life" },
  climate: { src: "/brand/lockups/climate.png", w: 3000, h: 374, label: "Syltra Climate" },
  glide: { src: "/brand/lockups/glide.png", w: 3000, h: 409, label: "Syltra Glide" },
  shield: { src: "/brand/lockups/shield.png", w: 3000, h: 392, label: "Syltra Shield" },
  os: { src: "/brand/lockups/os.png", w: 3000, h: 462, label: "Syltra OS" },
};

const DIVISION_SEGMENTS = new Set(["climate", "glide", "shield", "os"]);

export default function Logo({ locale, className = "" }: { locale: Locale; className?: string }) {
  const pathname = usePathname() || `/${locale}`;
  const seg = pathname.replace(/^\/(en|ar)/, "").split("/").filter(Boolean)[0] || "";

  // Each division page carries its own lockup; /life carries Life; everything
  // else (the umbrella and its pages) carries ONE.
  const key = DIVISION_SEGMENTS.has(seg) ? seg : seg === "life" ? "life" : "one";
  const lk = LOCKUPS[key];
  // A division lockup links to its own page; the umbrella logo links home.
  const href = key === "one" ? `/${locale}` : `/${locale}/${key}`;

  return (
    <Link href={href} aria-label={lk.label} className={`block ${className}`}>
      <Image
        src={assetPath(lk.src)}
        alt={lk.label}
        width={lk.w}
        height={lk.h}
        priority
        sizes="220px"
        className="h-8 w-auto sm:h-9"
      />
    </Link>
  );
}
