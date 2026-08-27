"use client";

import { usePathname } from "next/navigation";

const LIFE_SEGMENTS = new Set([
  "life",
  "products",
  "store",
  "builder",
  "solutions",
  "services",
  "apps",
  "quote",
  "faq",
]);

/**
 * Renders its children only inside the Syltra Life world. Used to keep the Syla
 * assistant (a Life feature) off the umbrella home and the other divisions.
 */
export default function LifeOnly({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";
  const seg = pathname.replace(/^\/(en|ar)/, "").split("/").filter(Boolean)[0] || "";
  if (!LIFE_SEGMENTS.has(seg)) return null;
  return <>{children}</>;
}
