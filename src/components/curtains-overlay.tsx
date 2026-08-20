"use client";

import { useEffect } from "react";
import { useHomeControls } from "@/lib/home-controls-context";
import type { Dictionary } from "@/lib/i18n/dictionary";

export default function CurtainsOverlay({ dict }: { dict: Dictionary["lightsPanel"] }) {
  const { curtainsOpen, setCurtainsOpen } = useHomeControls();

  useEffect(() => {
    if (!curtainsOpen) {
      document.documentElement.style.overflow = "hidden";
    } else {
      document.documentElement.style.overflow = "";
    }
    return () => {
      document.documentElement.style.overflow = "";
    };
  }, [curtainsOpen]);

  return (
    <div
      className={`pointer-events-none fixed inset-0 z-30 overflow-hidden ${
        curtainsOpen ? "" : "pointer-events-auto"
      }`}
      aria-hidden={curtainsOpen}
    >
      {/* Left panel */}
      <button
        onClick={() => setCurtainsOpen(true)}
        aria-hidden={curtainsOpen}
        tabIndex={curtainsOpen ? -1 : 0}
        className="absolute inset-y-0 left-0 w-1/2 border-e border-white/10 backdrop-blur-xl transition-transform duration-[900ms] ease-[cubic-bezier(.22,1,.36,1)]"
        style={{
          transform: curtainsOpen ? "translateX(-100%)" : "translateX(0)",
          background:
            "linear-gradient(115deg, rgba(199,204,211,0.16), rgba(76,141,255,0.05) 40%, rgba(199,204,211,0.10))",
        }}
      />
      {/* Right panel */}
      <button
        onClick={() => setCurtainsOpen(true)}
        aria-hidden={curtainsOpen}
        tabIndex={curtainsOpen ? -1 : 0}
        className="absolute inset-y-0 right-0 w-1/2 border-s border-white/10 backdrop-blur-xl transition-transform duration-[900ms] ease-[cubic-bezier(.22,1,.36,1)]"
        style={{
          transform: curtainsOpen ? "translateX(100%)" : "translateX(0)",
          background:
            "linear-gradient(245deg, rgba(199,204,211,0.16), rgba(76,141,255,0.05) 40%, rgba(199,204,211,0.10))",
        }}
      />

      {/* Instructional message */}
      <div
        className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-4 transition-opacity duration-300"
        style={{ opacity: curtainsOpen ? 0 : 1 }}
      >
        <p className="font-display text-xl font-bold text-chrome-dim sm:text-2xl">
          {dict.curtainsOverlayMessage}
        </p>
        <button
          onClick={() => setCurtainsOpen(true)}
          tabIndex={curtainsOpen ? -1 : 0}
          className={`rounded-lg bg-platinum px-8 py-3.5 text-sm font-bold text-void shadow-2xl transition-transform hover:scale-105 ${
            curtainsOpen ? "pointer-events-none" : "pointer-events-auto"
          }`}
        >
          {dict.curtainsOverlayOpen}
        </button>
        <p className="font-mono text-xs text-slate">{dict.curtainsOverlayHint}</p>
      </div>
    </div>
  );
}
