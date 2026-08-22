"use client";

import { usePathname } from "next/navigation";

/**
 * The builder is an app-like screen that must fit one viewport, so the footer
 * is dropped there. Every other route keeps it.
 */
export function HideOnBuilder({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  if (/^\/(ar|en)\/builder(\/|$)/.test(pathname)) return null;
  return <>{children}</>;
}
