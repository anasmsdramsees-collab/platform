"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { Locale } from "@/lib/i18n/config";
import { useHomeControls } from "@/lib/home-controls-context";
import { parseVoiceCommand } from "@/lib/voice-commands";
import { applySylaVoice, normalizeForSpeech } from "@/lib/tts-voice";

type Phase = "off" | "passive" | "listening" | "thinking" | "speaking";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Recognition = any;

const WAKE_WORDS = [
  "سيلا",
  "سيله",
  "سيلة",
  "يا سيلا",
  "هاي سيلا",
  "syla",
  "sila",
  "hey syla",
  "hey sila",
  "cela",
  "sella",
  // Frequent mishearings of the name by the speech recognizer
  "سيري",
  "سيرى",
  "سيلى",
  "siri",
  "seela",
  "sela",
  "cila",
];

const STORAGE_KEY = "syla_wake_enabled";

function stripWakeWord(text: string): { woke: boolean; query: string } {
  const lower = text.toLowerCase().trim();
  for (const w of WAKE_WORDS) {
    const idx = lower.indexOf(w);
    if (idx !== -1) {
      return { woke: true, query: text.slice(idx + w.length).trim() };
    }
  }
  return { woke: false, query: "" };
}

export default function SylaWake({ locale }: { locale: Locale }) {
  const [supported, setSupported] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [phase, setPhase] = useState<Phase>("off");
  const [transcript, setTranscript] = useState("");
  const [reply, setReply] = useState("");

  const recRef = useRef<Recognition | null>(null);
  const phaseRef = useRef<Phase>("off");
  const enabledRef = useRef(false);
  const silenceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const router = useRouter();
  const { applyAction } = useHomeControls();
  const lang = locale === "ar" ? "ar-SA" : "en-US";

  const t = {
    listening: locale === "ar" ? "سيلا تسمعك.." : "Syla is listening..",
    thinking: locale === "ar" ? "لحظة.." : "One moment..",
    enable: locale === "ar" ? "تفعيل النداء الصوتي (سيلا)" : 'Enable wake word ("Hey Syla")',
    disable: locale === "ar" ? "إيقاف النداء الصوتي" : "Disable wake word",
    done: locale === "ar" ? "تم." : "Done.",
    error: locale === "ar" ? "حصل خطأ، جرب تاني." : "Something went wrong, try again.",
  };

  phaseRef.current = phase;
  enabledRef.current = enabled;

  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      if (!("speechSynthesis" in window)) {
        onEnd?.();
        return;
      }
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(normalizeForSpeech(text, lang));
      applySylaVoice(u, lang);
      u.onend = () => onEnd?.();
      u.onerror = () => onEnd?.();
      window.speechSynthesis.speak(u);
    },
    [lang]
  );

  const backToPassive = useCallback(() => {
    setTranscript("");
    setReply("");
    setPhase(enabledRef.current ? "passive" : "off");
    try {
      recRef.current?.start();
    } catch {
      /* already started */
    }
  }, []);

  const processQuery = useCallback(
    async (query: string) => {
      if (silenceTimer.current) clearTimeout(silenceTimer.current);
      const text = query.trim();
      if (!text) {
        backToPassive();
        return;
      }
      setTranscript(text);

      const action = parseVoiceCommand(text);
      if (action) {
        if (action.kind === "navigate") {
          const path = action.path === "home" ? `/${locale}` : `/${locale}/${action.path}`;
          router.push(path);
        } else {
          applyAction(action);
        }
        setPhase("speaking");
        setReply(t.done);
        speak(t.done, backToPassive);
        return;
      }

      setPhase("thinking");
      try {
        const res = await fetch("/api/sina", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ messages: [{ role: "user", content: text }] }),
        });
        const data = await res.json();
        const answer: string = res.ok && data.reply ? data.reply : t.error;
        setPhase("speaking");
        setReply(answer);
        speak(answer, backToPassive);
      } catch {
        setPhase("speaking");
        setReply(t.error);
        speak(t.error, backToPassive);
      }
    },
    [applyAction, backToPassive, locale, router, speak, t.done, t.error]
  );

  // Build the continuous recognizer once enabled.
  useEffect(() => {
    const SR =
      typeof window !== "undefined" &&
      ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
    setSupported(Boolean(SR));
    if (!SR) return;

    const saved = localStorage.getItem(STORAGE_KEY) === "1";
    if (saved) setEnabled(true);
  }, []);

  useEffect(() => {
    if (!supported) return;
    localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0");

    if (!enabled) {
      recRef.current?.stop?.();
      recRef.current = null;
      setPhase("off");
      return;
    }

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const rec: Recognition = new SR();
    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true;

    rec.onresult = (event: any) => {
      let finalText = "";
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const chunk = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += chunk;
        else interimText += chunk;
      }
      const current = phaseRef.current;

      if (current === "passive") {
        const probe = stripWakeWord(finalText || interimText);
        if (probe.woke) {
          setPhase("listening");
          setTranscript(probe.query);
          if (probe.query && finalText) {
            processQuery(probe.query);
            return;
          }
          // wait for the actual question
          if (silenceTimer.current) clearTimeout(silenceTimer.current);
          silenceTimer.current = setTimeout(() => backToPassive(), 8000);
        }
        return;
      }

      if (current === "listening") {
        if (interimText) setTranscript(interimText);
        if (finalText) processQuery(stripWakeWord(finalText).query || finalText);
      }
    };

    rec.onend = () => {
      // Chrome stops after silence; keep the ear open unless we're mid-reply.
      const current = phaseRef.current;
      if (enabledRef.current && (current === "passive" || current === "listening")) {
        try {
          rec.start();
        } catch {
          /* ignore */
        }
      }
    };
    rec.onerror = () => {
      /* onend will handle restart */
    };

    recRef.current = rec;
    setPhase("passive");
    try {
      rec.start();
    } catch {
      /* ignore */
    }

    return () => {
      rec.onend = null;
      rec.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, supported, lang]);

  if (!supported) return null;

  const active = phase === "listening" || phase === "thinking" || phase === "speaking";

  return (
    <>
      {/* Toggle button, sits left of the chat launcher */}
      <button
        onClick={() => setEnabled((v) => !v)}
        aria-label={enabled ? t.disable : t.enable}
        title={enabled ? t.disable : t.enable}
        className={`fixed bottom-5 end-24 z-50 flex h-12 w-12 items-center justify-center rounded-full border transition-colors ${
          enabled
            ? "border-ion bg-ion/15 text-ion"
            : "border-hairline-strong bg-graphite text-slate hover:text-platinum"
        }`}
      >
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <rect x="9" y="2" width="6" height="11" rx="3" />
          <path d="M5 10v1a7 7 0 0 0 14 0v-1M12 18v3" />
        </svg>
        {enabled && phase === "passive" && (
          <span className="absolute -top-0.5 -end-0.5 flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-ion opacity-60" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-ion" />
          </span>
        )}
      </button>

      {/* Siri-style overlay */}
      {active && (
        <div className="pointer-events-none fixed inset-0 z-[70] flex flex-col items-center justify-end pb-16">
          <div className="absolute inset-0 bg-void/40 backdrop-blur-[2px]" />
          <div className="relative flex max-w-lg flex-col items-center gap-5 px-6 text-center">
            {transcript && (
              <p className="font-display text-lg font-bold text-platinum drop-shadow-lg sm:text-xl">
                {transcript}
              </p>
            )}
            {phase === "speaking" && reply && (
              <p className="max-h-40 overflow-hidden text-sm leading-relaxed text-chrome-dim">
                {reply}
              </p>
            )}
            {phase === "thinking" && (
              <p className="font-mono text-xs text-slate">{t.thinking}</p>
            )}
            {phase === "listening" && !transcript && (
              <p className="font-mono text-xs text-slate">{t.listening}</p>
            )}

            {/* Animated wave */}
            <div className="syla-wave flex h-14 items-center gap-1.5">
              {[0, 1, 2, 3, 4, 5, 6].map((i) => (
                <span
                  key={i}
                  className={phase === "thinking" ? "syla-bar syla-bar-slow" : "syla-bar"}
                  style={{ animationDelay: `${i * 0.11}s` }}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
