"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { Dictionary } from "@/lib/i18n/dictionary";
import type { Locale } from "@/lib/i18n/config";
import { useSpeechRecognition } from "@/lib/hooks/use-speech-recognition";
import { useSpeechSynthesis } from "@/lib/hooks/use-speech-synthesis";
import { useHomeControls } from "@/lib/home-controls-context";
import { parseVoiceCommand } from "@/lib/voice-commands";
import { assetPath } from "@/lib/base-path";

interface Message {
  role: "user" | "assistant";
  content: string;
  isError?: boolean;
}

export default function SinaWidget({ dict, locale }: { dict: Dictionary["sina"]; locale: Locale }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceReplies, setVoiceReplies] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const router = useRouter();
  const { applyAction } = useHomeControls();
  const speechLang = locale === "ar" ? "ar-SA" : "en-US";
  const speech = useSpeechRecognition(speechLang);
  const tts = useSpeechSynthesis(speechLang);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(override?: string) {
    const text = (override ?? input).trim();
    if (!text || loading) return;

    const next: Message[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/sina", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          messages: next.map(({ role, content }) => ({ role, content })),
        }),
      });
      const data = await res.json();

      if (!res.ok) {
        const message = data?.error === "not_configured" ? dict.unavailable : dict.error;
        setMessages((m) => [...m, { role: "assistant", content: message, isError: true }]);
        return;
      }

      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
      if (voiceReplies && tts.supported) {
        tts.speak(data.reply);
      }
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: dict.error, isError: true }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      send();
    }
  }

  function handleMicClick() {
    if (speech.listening) {
      speech.stop();
      return;
    }
    speech.start((transcript) => {
      if (!transcript) return;
      const action = parseVoiceCommand(transcript);
      if (action?.kind === "navigate") {
        const path = action.path === "home" ? `/${locale}` : `/${locale}/${action.path}`;
        router.push(path);
      } else if (action) {
        applyAction(action);
      }
      send(transcript);
    });
  }

  return (
    <div className="fixed bottom-5 end-5 z-50">
      {open && (
        <div className="mb-3 flex h-[520px] w-[360px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-lg border border-hairline-strong bg-graphite shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-ion opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-ion" />
              </span>
              <div>
                <p className="font-display text-sm font-bold text-platinum">{dict.title}</p>
                <p className="font-mono text-[10.5px] text-slate">{dict.subtitle}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {tts.supported && (
                <button
                  onClick={() => {
                    if (tts.speaking) tts.stop();
                    setVoiceReplies((v) => !v);
                  }}
                  aria-label={dict.voiceReplies}
                  aria-pressed={voiceReplies}
                  className={`rounded-md p-1.5 transition-colors ${
                    voiceReplies ? "text-ion" : "text-slate hover:text-platinum"
                  }`}
                >
                  {voiceReplies ? (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 5 6 9H3v6h3l5 4V5Z" />
                      <path d="M15.5 8.5a5 5 0 0 1 0 7" />
                    </svg>
                  ) : (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 5 6 9H3v6h3l5 4V5Z" />
                      <path d="M23 9l-6 6M17 9l6 6" />
                    </svg>
                  )}
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                aria-label={dict.close}
                className="rounded-md p-1.5 text-slate transition-colors hover:bg-void-2 hover:text-platinum"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            <div className="flex justify-start">
              <p className="max-w-[85%] rounded-lg rounded-ss-sm bg-void-2 px-3 py-2 text-sm text-platinum">
                {dict.greeting}
              </p>
            </div>
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <p
                  className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                    m.role === "user"
                      ? "rounded-ee-sm bg-ion text-void"
                      : `rounded-ss-sm bg-void-2 ${m.isError ? "text-chrome-dim" : "text-platinum"}`
                  }`}
                >
                  {m.content}
                </p>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <p className="rounded-lg rounded-ss-sm bg-void-2 px-3 py-2 font-mono text-xs text-slate">
                  {dict.thinking}
                </p>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-hairline p-3">
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={speech.listening ? dict.listening : dict.placeholder}
                disabled={loading}
                className="flex-1 rounded-md border border-hairline bg-void-2 px-3 py-2 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none"
              />
              {speech.supported && (
                <button
                  onClick={handleMicClick}
                  disabled={loading}
                  aria-label={dict.mic}
                  className={`rounded-md p-2 transition-colors disabled:opacity-40 ${
                    speech.listening
                      ? "bg-ion text-void"
                      : "border border-hairline text-chrome-dim hover:text-platinum"
                  }`}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="9" y="2" width="6" height="11" rx="3" />
                    <path d="M5 10v1a7 7 0 0 0 14 0v-1M12 18v3" />
                  </svg>
                </button>
              )}
              <button
                onClick={() => send()}
                disabled={loading || !input.trim()}
                aria-label={dict.send}
                className="rounded-md bg-platinum p-2 text-void transition-opacity hover:opacity-90 disabled:opacity-40"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </button>
            </div>
            <p className="mt-2 font-mono text-[10px] leading-snug text-slate">{dict.disclaimer}</p>
          </div>
        </div>
      )}

      {/* Launcher */}
      <div className="flex flex-col items-center gap-2">
        {!open && (
          <span className="syla-try rounded-full border border-ion/40 bg-void/80 px-3.5 py-1.5 font-mono text-[11px] font-semibold text-ion backdrop-blur-sm">
            {locale === "ar" ? "جرب سيلا" : "Try Syla"}
          </span>
        )}
        <button
          onClick={() => setOpen((v) => !v)}
          aria-label={dict.launcherLabel}
          className={`syla-launcher relative flex h-16 w-16 items-center justify-center rounded-full transition-transform hover:scale-105 ${
            open ? "syla-launcher-open" : ""
          }`}
        >
          {open ? (
            <span className="flex h-14 w-14 items-center justify-center rounded-full border border-hairline-strong bg-graphite text-platinum">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </span>
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={assetPath("/brand/syla-icon.png?v=2")}
              alt=""
              className="h-16 w-16 rounded-full"
            />
          )}
        </button>
      </div>
    </div>
  );
}
