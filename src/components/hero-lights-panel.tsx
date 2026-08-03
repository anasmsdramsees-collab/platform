"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import type { Dictionary } from "@/lib/i18n/dictionary";
import type { Locale } from "@/lib/i18n/config";
import { useSpeechRecognition } from "@/lib/hooks/use-speech-recognition";
import { useHomeControls } from "@/lib/home-controls-context";
import { parseVoiceCommand } from "@/lib/voice-commands";
import { assetPath } from "@/lib/base-path";

function useClock() {
  const [time, setTime] = useState("");
  useEffect(() => {
    const format = () =>
      setTime(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    format();
    const id = setInterval(format, 30_000);
    return () => clearInterval(id);
  }, []);
  return time;
}

export default function HeroLightsPanel({
  dict,
  locale,
}: {
  dict: Dictionary["lightsPanel"];
  locale: Locale;
}) {
  const { lightsOn, climateOn, curtainsOpen, setLightsOn, setClimateOn, setCurtainsOpen, applyAction } =
    useHomeControls();
  const time = useClock();
  const router = useRouter();
  const speechLang = locale === "ar" ? "ar-SA" : "en-US";
  const speech = useSpeechRecognition(speechLang);

  const handleVoiceResult = useCallback(
    (transcript: string) => {
      const action = parseVoiceCommand(transcript);
      if (!action) return;
      if (action.kind === "navigate") {
        const path = action.path === "home" ? `/${locale}` : `/${locale}/${action.path}`;
        router.push(path);
        return;
      }
      applyAction(action);
    },
    [applyAction, router, locale]
  );

  function handleMicClick() {
    if (speech.listening) {
      speech.stop();
      return;
    }
    speech.start(handleVoiceResult);
  }

  return (
    <>
      {/* Device bezel */}
      <div className="mx-auto w-full max-w-[240px] rounded-[22px] border border-hairline-strong bg-[#0a0b0d] p-2 shadow-2xl">
        {/* Screen */}
        <div className="rounded-2xl bg-gradient-to-b from-graphite to-void-2 p-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-semibold text-platinum">{time || "—:—"}</p>
              <p className="font-mono text-[9px] text-slate">{dict.room}</p>
            </div>
            <div className="flex items-center gap-1.5">
              {speech.supported && (
                <button
                  onClick={handleMicClick}
                  aria-label={dict.voiceHint}
                  className={`rounded-full p-1 transition-colors ${
                    speech.listening ? "bg-ion text-void" : "text-slate hover:text-platinum"
                  }`}
                >
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="9" y="2" width="6" height="11" rx="3" />
                    <path d="M5 10v1a7 7 0 0 0 14 0v-1M12 18v3" />
                  </svg>
                </button>
              )}
              <p className="font-mono text-[11px] text-chrome-dim">24°C</p>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-3 gap-1.5">
            <button
              onClick={() => setLightsOn(!lightsOn)}
              aria-pressed={!lightsOn}
              className="flex flex-col items-center gap-1 rounded-lg bg-void-2 py-2.5 transition-colors hover:bg-void"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke={lightsOn ? "#f2b84b" : "var(--color-slate)"}
                strokeWidth="1.8"
              >
                <path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.4.3.6.8.6 1.2v.5h6v-.5c0-.4.2-.9.6-1.2A6 6 0 0 0 12 3Z" />
              </svg>
              <span className="font-mono text-[8.5px] text-chrome-dim">{dict.tileLighting}</span>
              <span className={`text-[9px] font-medium ${lightsOn ? "text-platinum" : "text-slate"}`}>
                {lightsOn ? dict.on : dict.off}
              </span>
            </button>

            <button
              onClick={() => setClimateOn(!climateOn)}
              aria-pressed={!climateOn}
              className="flex flex-col items-center gap-1 rounded-lg bg-void-2 py-2.5 transition-colors hover:bg-void"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke={climateOn ? "#5bc4d9" : "var(--color-slate)"}
                strokeWidth="1.8"
              >
                <path d="M12 2v20M4.9 4.9l14.2 14.2M19.1 4.9 4.9 19.1M2 12h20" />
              </svg>
              <span className="font-mono text-[8.5px] text-chrome-dim">{dict.tileClimate}</span>
              <span className={`text-[9px] font-medium ${climateOn ? "text-platinum" : "text-slate"}`}>
                {climateOn ? "24°C" : dict.off}
              </span>
            </button>

            <button
              onClick={() => setCurtainsOpen(!curtainsOpen)}
              aria-pressed={!curtainsOpen}
              className="flex flex-col items-center gap-1 rounded-lg bg-void-2 py-2.5 transition-colors hover:bg-void"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke={curtainsOpen ? "#7c9cf2" : "var(--color-slate)"}
                strokeWidth="1.8"
              >
                <path d="M4 4h16M4 4v16M20 4v9M8 4v13M8 17h8" />
              </svg>
              <span className="font-mono text-[8.5px] text-chrome-dim">{dict.tileCurtains}</span>
              <span className={`text-[9px] font-medium ${curtainsOpen ? "text-platinum" : "text-slate"}`}>
                {curtainsOpen ? dict.curtainsOpen : dict.curtainsClosed}
              </span>
            </button>
          </div>
        </div>

        {/* Bezel wordmark */}
        <div className="flex justify-center pt-2 pb-1">
          <Image src={assetPath("/brand/logo.png")} alt="SYNTRA" width={1349} height={503} className="h-2.5 w-auto opacity-70" />
        </div>
      </div>

      <p className="mx-auto mt-2 max-w-[260px] text-center font-mono text-[10px] leading-snug text-slate">
        {speech.listening ? dict.voiceHint : dict.hint}
      </p>

      {!lightsOn && (
        <div
          onClick={() => setLightsOn(true)}
          className="fixed inset-0 z-40 flex cursor-pointer flex-col items-center justify-center gap-3 bg-black/97 backdrop-blur-sm transition-opacity"
        >
          <p className="font-display text-2xl font-bold text-chrome-dim">{dict.offMessage}</p>
          <p className="font-mono text-xs text-slate">{dict.tapToTurnOn}</p>
        </div>
      )}
    </>
  );
}
