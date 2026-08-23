"use client";

import { cn } from "@/lib/utils";
import { assetPath } from "@/lib/base-path";
import type { Locale } from "@/lib/i18n/config";
import type { ClimateKind, SystemKey } from "@/lib/builder-data";
import { playCurtain, playLock, playUnlock } from "@/lib/sound";

export interface HomeState {
  /** 0 to 100; drives the pendant glow in the 3D scene. */
  brightness: number;
  /** 0 = shut, 100 = fully drawn back. */
  curtains: number;
  locked: boolean;
  temperature: number;
  camera: number | null;
  intercom: boolean;
}

const SCENES = [
  { id: "morning", ar: "صباح الخير", en: "Morning", icon: "☼" },
  { id: "movie", ar: "ليلة فيلم", en: "Movie", icon: "▶" },
  { id: "away", ar: "خروج", en: "Away", icon: "→" },
  { id: "night", ar: "تصبح على خير", en: "Night", icon: "☾" },
] as const;

type SceneId = (typeof SCENES)[number]["id"];

const FEEDS = [
  { src: "/store/cctv-bullet-3.jpg", ar: "المدخل", en: "Entrance" },
  { src: "/store/cctv-dome-3.jpg", ar: "الصالة", en: "Living" },
  { src: "/store/cctv-ptz-3.jpg", ar: "الحوش", en: "Yard" },
  { src: "/store/cctv-solar-3.jpg", ar: "السور", en: "Perimeter" },
];

const INTERCOM_FEED = "/store/doorbell-3.jpg";

/**
 * The Syltra 11-inch wall panel, laid out as a horizontal strip so the whole
 * builder fits one screen: scenes, the big controls, the door and the cameras.
 */
export function WallPanel({
  locale,
  chosen,
  climate,
  state,
  setState,
  scopeLabel,
  scoped,
}: {
  locale: Locale;
  chosen: SystemKey[];
  climate: ClimateKind;
  state: HomeState;
  setState: (updater: (prev: HomeState) => HomeState) => void;
  /** Room name when a room is in focus, otherwise the whole-home label. */
  scopeLabel: string;
  /** True when a single room is selected. */
  scoped: boolean;
}) {
  const ar = locale === "ar";
  const has = (k: SystemKey) => chosen.includes(k);

  function runScene(id: SceneId) {
    setState((s) => {
      if (has("curtains")) playCurtain();
      switch (id) {
        case "morning":
          return { ...s, brightness: 45, curtains: 100, temperature: 23, locked: true };
        case "movie":
          return { ...s, brightness: 10, curtains: 0, temperature: 21, locked: true };
        case "away":
          if (has("security") && !s.locked) playLock();
          return { ...s, brightness: 0, curtains: 0, temperature: 27, locked: true, camera: 0 };
        case "night":
          return { ...s, brightness: 0, curtains: 0, temperature: 20, locked: true };
      }
    });
  }

  const card = "rounded-xl border border-white/8 bg-white/[0.035] p-2.5";

  return (
    <div className="rounded-2xl border border-hairline-strong bg-[#0a0c11] p-1.5">
      <div className="rounded-xl bg-gradient-to-br from-[#0d1524] via-[#0b1119] to-[#0a0e16] p-2.5">
        {/* Panel chrome */}
        <div className="flex items-center justify-between px-1 pb-2">
          <span className="flex items-center gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath("/brand/logo.png")} alt="" className="h-3 w-auto opacity-70" />
            <span className="font-mono text-[9px] tracking-widest text-slate">
              {ar ? "شاشة سيلترا 11″" : "SYLTRA PANEL 11″"}
            </span>
            {/* Which space the controls below are acting on. */}
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[9.5px] font-medium",
                scoped ? "bg-ion/20 text-ion" : "bg-white/10 text-slate"
              )}
            >
              {scoped ? "◉ " : ""}
              {ar ? "تحكّم: " : "Controlling: "}
              {scopeLabel}
            </span>
          </span>
          <span className="flex items-center gap-2 font-mono text-[9.5px] text-slate">
            {state.temperature}°
            <span className="size-1.5 rounded-full bg-[#7ee08a]" />
          </span>
        </div>

        <div className="grid gap-2 lg:grid-cols-[10rem_1fr_1fr_9rem_10rem]">
          {/* Scenes */}
          <div className={card}>
            <p className="font-mono text-[9px] uppercase tracking-widest text-slate">
              {ar ? "المشاهد" : "Scenes"}
            </p>
            <div className="mt-1.5 grid grid-cols-2 gap-1">
              {SCENES.map((sc) => (
                <button
                  key={sc.id}
                  onClick={() => runScene(sc.id)}
                  className="rounded-lg bg-white/[0.05] px-1.5 py-1.5 text-center transition-colors hover:bg-white/[0.12]"
                >
                  <span className="block text-[13px] leading-none text-ion">{sc.icon}</span>
                  <span className="mt-1 block truncate text-[9.5px] text-platinum">
                    {ar ? sc.ar : sc.en}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Lighting */}
          <div className={cn(card, !has("lighting") && "opacity-35")}>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[10.5px] text-slate">
                <span
                  className="size-1.5 rounded-full bg-[#f5c451]"
                  style={{ opacity: 0.3 + (state.brightness / 100) * 0.7 }}
                />
                {ar ? "الإضاءة" : "Lighting"}
              </span>
              <span className="font-mono text-[12px] font-semibold text-platinum">
                {state.brightness}%
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={state.brightness}
              disabled={!has("lighting")}
              onChange={(e) => setState((s) => ({ ...s, brightness: Number(e.target.value) }))}
              aria-label={ar ? "شدة الإضاءة" : "Brightness"}
              className="mt-2 w-full accent-[#f5c451] disabled:cursor-not-allowed"
            />
            <div className="mt-1.5 flex gap-1">
              {[0, 30, 60, 100].map((v) => (
                <button
                  key={v}
                  disabled={!has("lighting")}
                  onClick={() => setState((s) => ({ ...s, brightness: v }))}
                  className={cn(
                    "flex-1 rounded py-0.5 text-[9px] transition-colors disabled:cursor-not-allowed",
                    state.brightness === v ? "bg-white/15 text-platinum" : "bg-white/5 text-slate"
                  )}
                >
                  {v === 0 ? (ar ? "إطفاء" : "Off") : v === 100 ? (ar ? "كامل" : "Full") : `${v}%`}
                </button>
              ))}
            </div>
          </div>

          {/* Curtains */}
          <div className={cn(card, !has("curtains") && "opacity-35")}>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[10.5px] text-slate">
                <span
                  className="size-1.5 rounded-full bg-[#8ab4ff]"
                  style={{ opacity: 0.3 + (state.curtains / 100) * 0.7 }}
                />
                {ar ? "الستائر" : "Curtains"}
              </span>
              <span className="font-mono text-[12px] font-semibold text-platinum">
                {state.curtains}%
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={state.curtains}
              disabled={!has("curtains")}
              onChange={(e) => setState((s) => ({ ...s, curtains: Number(e.target.value) }))}
              onPointerUp={() => has("curtains") && playCurtain()}
              aria-label={ar ? "فتح الستائر" : "Curtain opening"}
              className="mt-2 w-full accent-[#8ab4ff] disabled:cursor-not-allowed"
            />
            <div className="mt-1.5 flex gap-1">
              {[
                { v: 0, ar: "مغلقة", en: "Shut" },
                { v: 25, ar: "ربع", en: "¼" },
                { v: 50, ar: "نص", en: "½" },
                { v: 100, ar: "كاملة", en: "Full" },
              ].map((o) => (
                <button
                  key={o.v}
                  disabled={!has("curtains")}
                  onClick={() => {
                    playCurtain();
                    setState((s) => ({ ...s, curtains: o.v }));
                  }}
                  className={cn(
                    "flex-1 rounded py-0.5 text-[9px] transition-colors disabled:cursor-not-allowed",
                    state.curtains === o.v ? "bg-white/15 text-platinum" : "bg-white/5 text-slate"
                  )}
                >
                  {ar ? o.ar : o.en}
                </button>
              ))}
            </div>
          </div>

          {/* Climate and door */}
          <div className="space-y-2">
            <div className={cn(card, !has("climate") && "opacity-35")}>
              <span className="text-[10.5px] text-slate">
                {ar ? (climate === "central" ? "مركزي" : "سبليت") : climate === "central" ? "Central" : "Split"}
              </span>
              <div className="mt-1 flex items-center justify-between">
                <button
                  disabled={!has("climate")}
                  onClick={() => setState((s) => ({ ...s, temperature: Math.max(16, s.temperature - 1) }))}
                  className="size-6 rounded bg-white/10 text-sm font-bold text-platinum disabled:opacity-40"
                >
                  −
                </button>
                <span className="font-mono text-base font-semibold text-platinum">
                  {state.temperature}°
                </span>
                <button
                  disabled={!has("climate")}
                  onClick={() => setState((s) => ({ ...s, temperature: Math.min(30, s.temperature + 1) }))}
                  className="size-6 rounded bg-white/10 text-sm font-bold text-platinum disabled:opacity-40"
                >
                  +
                </button>
              </div>
            </div>

            <button
              disabled={!has("security")}
              onClick={() =>
                setState((s) => {
                  if (s.locked) playUnlock();
                  else playLock();
                  return { ...s, locked: !s.locked };
                })
              }
              className={cn(
                "w-full rounded-xl border p-2.5 text-start transition-colors disabled:cursor-not-allowed disabled:opacity-35",
                state.locked
                  ? "border-white/8 bg-white/[0.035] hover:border-white/20"
                  : "border-[#7ee08a]/40 bg-[#7ee08a]/10"
              )}
            >
              <span className="text-[10.5px] text-slate">{ar ? "الباب" : "Door"}</span>
              <span className="mt-0.5 block text-[13px] font-semibold text-platinum">
                {state.locked ? (ar ? "مقفل" : "Locked") : ar ? "مفتوح" : "Unlocked"}
              </span>
            </button>
          </div>

          {/* Cameras and intercom */}
          <div className={cn(card, !has("cameras") && !has("security") && "opacity-35")}>
            <div className="flex items-center justify-between">
              <p className="font-mono text-[9px] uppercase tracking-widest text-slate">
                {ar ? "الكاميرات" : "Cameras"}
              </p>
              {has("security") && (
                <button
                  onClick={() => setState((s) => ({ ...s, intercom: !s.intercom }))}
                  className={cn(
                    "rounded px-1.5 py-0.5 text-[9px] transition-colors",
                    state.intercom ? "bg-ion text-void" : "bg-white/10 text-slate hover:text-platinum"
                  )}
                >
                  {ar ? "الإنتركم" : "Intercom"}
                </button>
              )}
            </div>

            {state.intercom && has("security") ? (
              <div className="relative mt-1.5 overflow-hidden rounded-lg border border-ion/40">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={assetPath(INTERCOM_FEED)} alt="" className="aspect-[4/3] w-full object-cover" />
                <span className="absolute top-1 start-1 rounded bg-black/70 px-1 py-0.5 font-mono text-[8px] text-white">
                  {ar ? "زائر بالباب" : "Visitor"}
                </span>
                <button
                  onClick={() => {
                    playUnlock();
                    setState((s) => ({ ...s, locked: false, intercom: false }));
                  }}
                  className="absolute bottom-1 start-1 end-1 rounded bg-[#7ee08a] py-1 text-[9.5px] font-bold text-void"
                >
                  {ar ? "افتح" : "Unlock"}
                </button>
              </div>
            ) : (
              <>
                <div className="mt-1.5 grid grid-cols-2 gap-1">
                  {FEEDS.map((feed, i) => (
                    <button
                      key={feed.src}
                      disabled={!has("cameras")}
                      onClick={() => setState((s) => ({ ...s, camera: s.camera === i ? null : i }))}
                      className={cn(
                        "relative aspect-[4/3] overflow-hidden rounded border transition-colors disabled:cursor-not-allowed",
                        state.camera === i ? "border-ion" : "border-white/10 hover:border-white/25"
                      )}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={assetPath(feed.src)} alt="" className="size-full object-cover opacity-85" />
                    </button>
                  ))}
                </div>
                {state.camera !== null && has("cameras") && (
                  <div className="relative mt-1.5 overflow-hidden rounded border border-white/10">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={assetPath(FEEDS[state.camera].src)}
                      alt=""
                      className="aspect-video w-full object-cover"
                    />
                    <span className="absolute top-1 start-1 flex items-center gap-1 rounded bg-black/70 px-1 py-0.5 font-mono text-[8px] text-white">
                      <span className="size-1 animate-pulse rounded-full bg-red-500" />
                      {ar ? FEEDS[state.camera].ar : FEEDS[state.camera].en}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
