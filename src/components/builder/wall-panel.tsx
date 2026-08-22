"use client";

import { cn } from "@/lib/utils";
import { assetPath } from "@/lib/base-path";
import type { Locale } from "@/lib/i18n/config";
import { type ClimateKind, type PropertyDef, type SystemKey, roomName } from "@/lib/builder-data";
import { playCurtain, playLock, playUnlock } from "@/lib/sound";
import type { HomeState } from "./control-panel";

/** Scenes set several systems at once, the way the real panel does. */
const SCENES = [
  { id: "morning", ar: "صباح الخير", en: "Good morning", icon: "☼" },
  { id: "movie", ar: "ليلة فيلم", en: "Movie night", icon: "▶" },
  { id: "away", ar: "خروج", en: "Leave home", icon: "→" },
  { id: "night", ar: "تصبح على خير", en: "Good night", icon: "☾" },
] as const;

type SceneId = (typeof SCENES)[number]["id"];

const FEEDS = [
  { src: "/store/cctv-bullet-3.jpg", ar: "المدخل", en: "Entrance" },
  { src: "/store/cctv-dome-3.jpg", ar: "الصالة", en: "Living" },
  { src: "/store/cctv-ptz-3.jpg", ar: "الحوش", en: "Yard" },
  { src: "/store/cctv-solar-3.jpg", ar: "السور", en: "Perimeter" },
];

export function WallPanel({
  locale,
  property,
  chosen,
  climate,
  state,
  setState,
}: {
  locale: Locale;
  property: PropertyDef;
  chosen: SystemKey[];
  climate: ClimateKind;
  state: HomeState;
  setState: (updater: (prev: HomeState) => HomeState) => void;
}) {
  const ar = locale === "ar";
  const has = (k: SystemKey) => chosen.includes(k);

  function runScene(id: SceneId) {
    setState((s) => {
      switch (id) {
        case "morning":
          if (has("curtains")) playCurtain();
          return { ...s, brightness: 45, curtains: 100, temperature: 23, locked: true };
        case "movie":
          if (has("curtains")) playCurtain();
          return { ...s, brightness: 12, curtains: 0, temperature: 21, locked: true };
        case "away":
          if (has("security") && !s.locked) playLock();
          return { ...s, brightness: 0, curtains: 0, temperature: 27, locked: true, camera: 0 };
        case "night":
          if (has("curtains")) playCurtain();
          return { ...s, brightness: 0, curtains: 0, temperature: 20, locked: true };
      }
    });
  }

  const rooms = property.rooms.filter((r) => r.level === 0).slice(0, 4);

  return (
    <section className="mx-auto max-w-5xl px-3 pb-16 sm:px-5">
      <div className="text-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-slate">
          {ar ? "شاشة التحكم" : "Wall panel"}
        </p>
        <h2 className="font-display mt-2 text-balance text-2xl font-bold text-platinum sm:text-3xl">
          {ar ? "نفس البيت، من شاشة الحائط." : "The same home, from the wall panel."}
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-chrome-dim">
          {ar
            ? "هذه واجهة شاشة سيلترا مقاس 11 إنش. جرّبها، وستتغير الغرف في المجسم بالأعلى فورًا."
            : "This is the Syltra 11-inch panel interface. Use it, and the rooms above change with you."}
        </p>
      </div>

      {/* Bezel */}
      <div className="mt-8 rounded-[1.6rem] border border-hairline-strong bg-[#0a0c11] p-2.5 shadow-2xl shadow-black/60 sm:p-3.5">
        <div className="overflow-hidden rounded-[1.1rem] bg-gradient-to-br from-[#0d1524] via-[#0b1119] to-[#0a0e16]">
          {/* Panel top bar */}
          <div className="flex items-center justify-between border-b border-white/5 px-4 py-2.5 sm:px-5">
            <div className="flex items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={assetPath("/brand/logo.png")} alt="" className="h-4 w-auto opacity-80" />
              <span className="font-mono text-[10px] text-slate">SYLTRA</span>
            </div>
            <div className="flex items-center gap-3 font-mono text-[10.5px] text-chrome-dim">
              <span>{state.temperature}°</span>
              <span className="text-slate">·</span>
              <span>{ar ? "متصل" : "Online"}</span>
              <span className="size-1.5 rounded-full bg-[#7ee08a]" />
            </div>
          </div>

          <div className="grid gap-4 p-4 sm:p-5 lg:grid-cols-[1fr_15rem]">
            <div className="space-y-4">
              {/* Scenes */}
              <div>
                <p className="font-mono text-[10px] uppercase tracking-widest text-slate">
                  {ar ? "المشاهد" : "Scenes"}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {SCENES.map((sc) => (
                    <button
                      key={sc.id}
                      onClick={() => runScene(sc.id)}
                      className="rounded-xl border border-white/8 bg-white/[0.04] px-3 py-3 text-start transition-colors hover:border-ion/50 hover:bg-white/[0.08]"
                    >
                      <span className="text-base text-ion">{sc.icon}</span>
                      <span className="mt-1 block text-[12px] font-semibold text-platinum">
                        {ar ? sc.ar : sc.en}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Room tiles */}
              <div>
                <p className="font-mono text-[10px] uppercase tracking-widest text-slate">
                  {ar ? "الغرف" : "Rooms"}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {rooms.map((room) => {
                    const active = room.systems.filter((s) => chosen.includes(s));
                    return (
                      <div
                        key={room.id}
                        className="rounded-xl border border-white/8 bg-white/[0.03] p-3"
                      >
                        <p className="truncate text-[12px] font-semibold text-platinum">
                          {roomName(room, locale)}
                        </p>
                        <p className="mt-1 font-mono text-[10px] text-slate">
                          {active.length} {ar ? "نظام" : "systems"}
                        </p>
                        <div className="mt-2 flex gap-1">
                          {active.slice(0, 5).map((s) => (
                            <span
                              key={s}
                              className="h-1 flex-1 rounded-full"
                              style={{
                                backgroundColor:
                                  s === "lighting"
                                    ? "#f5c451"
                                    : s === "curtains"
                                    ? "#8ab4ff"
                                    : s === "climate"
                                    ? "#5ed4d0"
                                    : s === "cameras"
                                    ? "#c78bff"
                                    : s === "health"
                                    ? "#63d3a6"
                                    : "#ff8787",
                              }}
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Big controls */}
              <div className="grid gap-2 sm:grid-cols-3">
                {/* Lighting */}
                <div
                  className={cn(
                    "rounded-xl border border-white/8 bg-white/[0.03] p-3.5",
                    !has("lighting") && "opacity-35"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate">{ar ? "الإضاءة" : "Lighting"}</span>
                    <span className="font-mono text-sm font-semibold text-platinum">
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
                    onChange={(e) =>
                      setState((s) => ({ ...s, brightness: Number(e.target.value) }))
                    }
                    className="mt-3 w-full accent-[#f5c451] disabled:cursor-not-allowed"
                  />
                </div>

                {/* Curtains */}
                <div
                  className={cn(
                    "rounded-xl border border-white/8 bg-white/[0.03] p-3.5",
                    !has("curtains") && "opacity-35"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate">{ar ? "الستائر" : "Curtains"}</span>
                    <span className="font-mono text-sm font-semibold text-platinum">
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
                    className="mt-3 w-full accent-[#8ab4ff] disabled:cursor-not-allowed"
                  />
                </div>

                {/* Climate */}
                <div
                  className={cn(
                    "rounded-xl border border-white/8 bg-white/[0.03] p-3.5",
                    !has("climate") && "opacity-35"
                  )}
                >
                  <span className="text-[11px] text-slate">
                    {ar ? (climate === "central" ? "مركزي" : "سبليت") : climate === "central" ? "Central" : "Split"}
                  </span>
                  <div className="mt-2.5 flex items-center justify-between">
                    <button
                      disabled={!has("climate")}
                      onClick={() =>
                        setState((s) => ({ ...s, temperature: Math.max(16, s.temperature - 1) }))
                      }
                      className="size-8 rounded-lg bg-white/8 text-base font-bold text-platinum disabled:opacity-40"
                    >
                      −
                    </button>
                    <span className="font-mono text-xl font-semibold text-platinum">
                      {state.temperature}°
                    </span>
                    <button
                      disabled={!has("climate")}
                      onClick={() =>
                        setState((s) => ({ ...s, temperature: Math.min(30, s.temperature + 1) }))
                      }
                      className="size-8 rounded-lg bg-white/8 text-base font-bold text-platinum disabled:opacity-40"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Right column: door and cameras */}
            <div className="space-y-3">
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
                  "w-full rounded-xl border p-4 text-start transition-colors disabled:cursor-not-allowed disabled:opacity-35",
                  state.locked
                    ? "border-white/8 bg-white/[0.03] hover:border-white/20"
                    : "border-[#7ee08a]/40 bg-[#7ee08a]/10"
                )}
              >
                <span className="text-[11px] text-slate">{ar ? "الباب الرئيسي" : "Front door"}</span>
                <span className="mt-1 block text-base font-semibold text-platinum">
                  {state.locked ? (ar ? "مقفل" : "Locked") : ar ? "مفتوح" : "Unlocked"}
                </span>
                <span className="mt-1 block font-mono text-[10px] text-slate">
                  {ar ? "اضغط للتبديل" : "Tap to toggle"}
                </span>
              </button>

              <div className={cn("rounded-xl border border-white/8 bg-white/[0.03] p-3", !has("cameras") && "opacity-35")}>
                <p className="font-mono text-[10px] uppercase tracking-widest text-slate">
                  {ar ? "الكاميرات" : "Cameras"}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-1.5">
                  {FEEDS.map((feed, i) => (
                    <button
                      key={feed.src}
                      disabled={!has("cameras")}
                      onClick={() => setState((s) => ({ ...s, camera: s.camera === i ? null : i }))}
                      className={cn(
                        "relative aspect-[4/3] overflow-hidden rounded-md border transition-colors disabled:cursor-not-allowed",
                        state.camera === i ? "border-ion" : "border-white/10 hover:border-white/25"
                      )}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={assetPath(feed.src)} alt="" className="size-full object-cover opacity-85" />
                      <span className="absolute bottom-0 start-0 end-0 bg-black/60 py-0.5 text-center text-[9px] text-white">
                        {ar ? feed.ar : feed.en}
                      </span>
                    </button>
                  ))}
                </div>
                {state.camera !== null && has("cameras") && (
                  <div className="relative mt-2 overflow-hidden rounded-lg border border-white/10">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={assetPath(FEEDS[state.camera].src)}
                      alt=""
                      className="aspect-video w-full object-cover"
                    />
                    <span className="absolute top-1.5 start-1.5 flex items-center gap-1 rounded bg-black/70 px-1.5 py-0.5 font-mono text-[9px] text-white">
                      <span className="size-1 animate-pulse rounded-full bg-red-500" />
                      {ar ? FEEDS[state.camera].ar : FEEDS[state.camera].en}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <p className="mt-4 text-center font-mono text-[10.5px] text-slate">
        {ar
          ? "محاكاة لواجهة شاشة سيلترا 11 إنش"
          : "A simulation of the Syltra 11-inch panel interface"}
      </p>
    </section>
  );
}
