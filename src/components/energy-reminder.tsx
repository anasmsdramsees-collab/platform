"use client";

import { useEffect, useState } from "react";
import { useHomeControls } from "@/lib/home-controls-context";
import type { Dictionary } from "@/lib/i18n/dictionary";

const REMINDER_DELAY_MS = 3 * 60 * 1000;

export default function EnergyReminder({ dict }: { dict: Dictionary["energyReminder"] }) {
  const { lightsOn, curtainsOpen } = useHomeControls();
  const [elapsed, setElapsed] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setElapsed(true), REMINDER_DELAY_MS);
    return () => clearTimeout(timer);
  }, []);

  const shouldShow = elapsed && !dismissed && (lightsOn || curtainsOpen);
  if (!shouldShow) return null;

  return (
    <div className="fixed bottom-5 start-5 z-50 max-w-xs rounded-lg border border-hairline-strong bg-graphite p-4 shadow-2xl">
      <p className="text-sm text-platinum">{dict.message}</p>
      <button
        onClick={() => setDismissed(true)}
        className="mt-3 font-mono text-xs text-ion transition-opacity hover:opacity-80"
      >
        {dict.dismiss}
      </button>
    </div>
  );
}
