"use client";

import { createContext, useContext, useEffect, useState } from "react";

type Mode = "light" | "dark" | "system";
type Ctx = { mode: Mode; setMode: (m: Mode) => void; resolved: "light" | "dark" };

const ThemeCtx = createContext<Ctx | null>(null);
const STORE_KEY = "syltra-health-theme";

export function useHealthTheme() {
  const c = useContext(ThemeCtx);
  if (!c) throw new Error("useHealthTheme must be used within HealthThemeScope");
  return c;
}

/** Wraps the HEALTH section: owns light/dark state and exposes it via context. */
export function HealthThemeScope({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<Mode>("system");
  const [systemDark, setSystemDark] = useState(true);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORE_KEY) as Mode | null;
      if (saved === "light" || saved === "dark") setModeState(saved);
    } catch {}
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    setSystemDark(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const setMode = (m: Mode) => {
    setModeState(m);
    try {
      if (m === "system") localStorage.removeItem(STORE_KEY);
      else localStorage.setItem(STORE_KEY, m);
    } catch {}
  };

  const resolved: "light" | "dark" = mode === "system" ? (systemDark ? "dark" : "light") : mode;

  return (
    <ThemeCtx.Provider value={{ mode, setMode, resolved }}>
      <div
        className="flex min-h-full flex-col health-scope"
        data-theme={mode === "system" ? undefined : mode}
      >
        {children}
      </div>
    </ThemeCtx.Provider>
  );
}

/** Light / Dark pill toggle, matching the reference theme switch. */
export function HealthThemeToggle({ compact = false }: { compact?: boolean }) {
  const { resolved, setMode } = useHealthTheme();
  const isDark = resolved === "dark";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label="Toggle light or dark theme"
      onClick={() => setMode(isDark ? "light" : "dark")}
      className={`inline-flex items-center gap-2 rounded-full border border-hairline-strong bg-void-2 ${compact ? "px-1.5 py-1" : "px-2 py-1.5"}`}
    >
      {!compact && <span className={`px-1 text-[11px] font-medium ${!isDark ? "text-platinum" : "text-slate"}`}>Light</span>}
      <span className="relative h-4 w-8 rounded-full bg-graphite-2">
        <span
          className="absolute top-0.5 h-3 w-3 rounded-full bg-platinum transition-all"
          style={{ left: isDark ? "calc(100% - 0.875rem)" : "0.125rem" }}
        />
      </span>
      {!compact && <span className={`px-1 text-[11px] font-medium ${isDark ? "text-platinum" : "text-slate"}`}>Dark</span>}
    </button>
  );
}
