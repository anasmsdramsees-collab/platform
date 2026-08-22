"use client";

import { cn } from "@/lib/utils";
import { assetPath } from "@/lib/base-path";
import type { Locale } from "@/lib/i18n/config";
import type { SystemKey } from "@/lib/builder-data";

export interface HomeState {
  lights: boolean;
  curtains: boolean;
  locked: boolean;
  temperature: number;
  camera: number | null;
}

/** Stills stand in for live feeds; the panel labels them as a simulation. */
const FEEDS = [
  { src: "/store/cctv-bullet-3.jpg", ar: "المدخل", en: "Entrance" },
  { src: "/store/cctv-dome-3.jpg", ar: "الصالة", en: "Living room" },
  { src: "/store/cctv-ptz-3.jpg", ar: "الحوش", en: "Yard" },
  { src: "/store/doorbell-3.jpg", ar: "الباب", en: "Front door" },
];

function Tile({
  label,
  value,
  active,
  color,
  onClick,
  disabled,
}: {
  label: string;
  value: string;
  active: boolean;
  color: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "rounded-xl border p-3 text-start transition-colors disabled:cursor-not-allowed disabled:opacity-35",
        active ? "border-transparent bg-white/10" : "border-hairline bg-void-2 hover:border-hairline-strong"
      )}
    >
      <span className="flex items-center gap-2">
        <span
          className="size-2 rounded-full transition-opacity"
          style={{ backgroundColor: color, opacity: active ? 1 : 0.3 }}
        />
        <span className="text-[11px] text-slate">{label}</span>
      </span>
      <span className="mt-1.5 block text-sm font-semibold text-platinum">{value}</span>
    </button>
  );
}

export function ControlPanel({
  locale,
  chosen,
  state,
  setState,
}: {
  locale: Locale;
  chosen: SystemKey[];
  state: HomeState;
  setState: (updater: (prev: HomeState) => HomeState) => void;
}) {
  const ar = locale === "ar";
  const has = (k: SystemKey) => chosen.includes(k);

  return (
    <div className="rounded-2xl border border-hairline bg-graphite/70 p-4">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
          {ar ? "لوحة التحكم" : "Control panel"}
        </p>
        <span className="flex items-center gap-1.5 font-mono text-[10px] text-ion">
          <span className="relative flex size-1.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-ion opacity-70" />
            <span className="relative inline-flex size-1.5 rounded-full bg-ion" />
          </span>
          {ar ? "محاكاة" : "Simulation"}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2.5">
        <Tile
          label={ar ? "الإضاءة" : "Lighting"}
          value={state.lights ? (ar ? "مضاءة" : "On") : ar ? "مطفأة" : "Off"}
          active={state.lights}
          color="#f5c451"
          disabled={!has("lighting")}
          onClick={() => setState((s) => ({ ...s, lights: !s.lights }))}
        />
        <Tile
          label={ar ? "الستائر" : "Curtains"}
          value={state.curtains ? (ar ? "مفتوحة" : "Open") : ar ? "مغلقة" : "Closed"}
          active={state.curtains}
          color="#8ab4ff"
          disabled={!has("curtains")}
          onClick={() => setState((s) => ({ ...s, curtains: !s.curtains }))}
        />
        <Tile
          label={ar ? "الباب" : "Door"}
          value={state.locked ? (ar ? "مقفل" : "Locked") : ar ? "مفتوح" : "Unlocked"}
          active={!state.locked}
          color="#ff6b6b"
          disabled={!has("security")}
          onClick={() => setState((s) => ({ ...s, locked: !s.locked }))}
        />
        <div
          className={cn(
            "rounded-xl border p-3",
            has("climate") ? "border-hairline bg-void-2" : "border-hairline bg-void-2 opacity-35"
          )}
        >
          <span className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-[#5ed4d0]" />
            <span className="text-[11px] text-slate">{ar ? "التكييف" : "Climate"}</span>
          </span>
          <div className="mt-1.5 flex items-center justify-between">
            <button
              disabled={!has("climate")}
              onClick={() => setState((s) => ({ ...s, temperature: Math.max(16, s.temperature - 1) }))}
              className="size-6 rounded-md bg-white/10 text-sm font-bold text-platinum disabled:opacity-40"
            >
              −
            </button>
            <span className="font-mono text-sm font-semibold text-platinum">{state.temperature}°</span>
            <button
              disabled={!has("climate")}
              onClick={() => setState((s) => ({ ...s, temperature: Math.min(30, s.temperature + 1) }))}
              className="size-6 rounded-md bg-white/10 text-sm font-bold text-platinum disabled:opacity-40"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* Camera feeds */}
      <div className="mt-4">
        <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
          {ar ? "الكاميرات" : "Cameras"}
        </p>
        {has("cameras") ? (
          <>
            <div className="mt-2.5 grid grid-cols-4 gap-1.5">
              {FEEDS.map((feed, i) => (
                <button
                  key={feed.src}
                  onClick={() => setState((s) => ({ ...s, camera: s.camera === i ? null : i }))}
                  className={cn(
                    "relative aspect-[4/3] overflow-hidden rounded-md border transition-colors",
                    state.camera === i ? "border-ion" : "border-hairline hover:border-hairline-strong"
                  )}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={assetPath(feed.src)} alt="" className="size-full object-cover opacity-80" />
                </button>
              ))}
            </div>

            {state.camera !== null && (
              <div className="relative mt-2.5 overflow-hidden rounded-lg border border-hairline">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={assetPath(FEEDS[state.camera].src)}
                  alt=""
                  className="aspect-video w-full object-cover"
                />
                <div className="pointer-events-none absolute inset-0 bg-[repeating-linear-gradient(0deg,rgba(255,255,255,0.04)_0px,rgba(255,255,255,0.04)_1px,transparent_1px,transparent_3px)]" />
                <span className="absolute top-2 start-2 flex items-center gap-1.5 rounded bg-black/70 px-2 py-0.5 font-mono text-[10px] text-white">
                  <span className="size-1.5 animate-pulse rounded-full bg-red-500" />
                  {ar ? FEEDS[state.camera].ar : FEEDS[state.camera].en}
                </span>
              </div>
            )}
          </>
        ) : (
          <p className="mt-2 text-xs text-slate">
            {ar ? "أضف الكاميرات لتشوف البث." : "Add cameras to see the feeds."}
          </p>
        )}
      </div>
    </div>
  );
}
