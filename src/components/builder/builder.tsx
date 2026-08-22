"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n/config";
import {
  PROPERTIES,
  SYSTEMS,
  type PropertyKind,
  type SystemKey,
  propertyCopy,
  roomName,
  systemCopy,
} from "@/lib/builder-data";
import { ControlPanel, type HomeState } from "./control-panel";

// The 3D canvas is heavy and browser-only; keep it out of the first payload.
const BuilderScene = dynamic(() => import("./scene").then((m) => m.BuilderScene), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center">
      <span className="font-mono text-xs text-slate">...</span>
    </div>
  ),
});

const KINDS: PropertyKind[] = ["villa", "apartment", "office"];

export function Builder({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const [kind, setKind] = useState<PropertyKind | null>(null);
  const [chosen, setChosen] = useState<SystemKey[]>(["lighting"]);
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);
  const [state, setState] = useState<HomeState>({
    brightness: 70,
    curtains: 100,
    locked: true,
    temperature: 22,
    camera: null,
    intercom: false,
  });

  const property = kind ? PROPERTIES[kind] : null;

  // A rough device count so the visitor sees their choices add up to something real.
  const summary = useMemo(() => {
    if (!property) return { rooms: 0, points: 0 };
    let points = 0;
    for (const room of property.rooms) {
      points += room.systems.filter((s) => chosen.includes(s)).length;
    }
    return { rooms: property.rooms.length, points };
  }, [property, chosen]);

  function toggle(key: SystemKey) {
    setChosen((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }

  /* ---------- step 1: pick the property ---------- */
  if (!property) {
    return (
      <div className="mx-auto max-w-5xl px-5 py-20 sm:px-8">
        <div className="text-center">
          <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">
            {ar ? "جرّب بنفسك" : "Try it yourself"}
          </p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {ar ? "ابنِ بيتك الذكي بيدك." : "Build your smart home."}
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-chrome-dim">
            {ar
              ? "اختر نوع المكان، ركّب الأنظمة اللي تحبها، وشغّلها من لوحة تحكم حقيقية. تجربة كاملة في دقيقتين."
              : "Pick the kind of space, add the systems you want, then run them from a working control panel. Two minutes, start to finish."}
          </p>
        </div>

        <div className="mt-14 grid gap-4 sm:grid-cols-3">
          {KINDS.map((k) => {
            const def = PROPERTIES[k];
            const copy = propertyCopy(def, locale);
            return (
              <button
                key={k}
                onClick={() => setKind(k)}
                className="group rounded-2xl border border-hairline bg-graphite/70 p-7 text-start transition-colors hover:border-ion"
              >
                <span className="font-display text-2xl font-bold text-platinum">{copy.name}</span>
                <span className="mt-2 block text-sm leading-relaxed text-chrome-dim">{copy.blurb}</span>
                <span className="mt-5 block font-mono text-[11px] text-ion opacity-0 transition-opacity group-hover:opacity-100">
                  {ar ? "ابدأ ←" : "Start →"}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  /* ---------- step 2: build and control ---------- */
  const copy = propertyCopy(property, locale);
  const activeRoom = property.rooms.find((r) => `${r.level}-${r.id}` === selectedRoom);

  return (
    // Fills the viewport under the header so nothing needs scrolling on desktop.
    <div className="flex flex-col gap-3 px-3 py-3 sm:px-5 lg:h-[calc(100dvh-4.5rem)]">
      {/* Compact header row */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-2">
        <div className="flex items-baseline gap-3">
          <h1 className="font-display text-lg font-bold text-platinum sm:text-xl">{copy.name}</h1>
          <p className="text-[11.5px] text-slate">
            {ar
              ? `${summary.rooms} غرفة · ${chosen.length} أنظمة · نحو ${summary.points} نقطة`
              : `${summary.rooms} rooms · ${chosen.length} systems · ~${summary.points} points`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setKind(null);
              setSelectedRoom(null);
            }}
            className="rounded-lg border border-hairline px-3 py-1.5 text-[11px] text-chrome-dim hover:border-hairline-strong hover:text-platinum"
          >
            {ar ? "غيّر النوع" : "Change type"}
          </button>
          <Link
            href={`/${locale}/quote?from=builder&kind=${property.kind}&systems=${chosen.join(",")}`}
            className="rounded-lg bg-platinum px-4 py-1.5 text-[11.5px] font-semibold text-void transition-opacity hover:opacity-90"
          >
            {ar ? "احجز معاينة" : "Book a survey"}
          </Link>
        </div>
      </div>

      {/* Main area: systems rail, 3D stage, control rail */}
      <div className="grid min-h-0 flex-1 gap-3 lg:grid-cols-[15rem_1fr_19rem]">
        {/* Systems */}
        <div className="order-2 min-h-0 overflow-y-auto rounded-2xl border border-hairline bg-graphite/70 p-3 lg:order-1">
          <p className="font-mono text-[10.5px] uppercase tracking-widest text-slate">
            {ar ? "الأنظمة" : "Systems"}
          </p>
          <div className="mt-2.5 grid grid-cols-2 gap-1.5 lg:grid-cols-1">
            {SYSTEMS.map((s) => {
              const on = chosen.includes(s.key);
              const c = systemCopy(s.key, locale);
              return (
                <button
                  key={s.key}
                  onClick={() => toggle(s.key)}
                  title={c.desc}
                  className={cn(
                    "flex items-center gap-2 rounded-lg border px-2.5 py-2 text-start transition-colors",
                    on ? "border-transparent bg-white/10" : "border-hairline hover:border-hairline-strong"
                  )}
                >
                  <span
                    className="size-2 shrink-0 rounded-full transition-opacity"
                    style={{ backgroundColor: s.color, opacity: on ? 1 : 0.3 }}
                  />
                  <span className="truncate text-[12px] font-medium text-platinum">{c.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3D stage */}
        <div className="relative order-1 min-h-[20rem] overflow-hidden rounded-2xl border border-hairline bg-void lg:order-2 lg:min-h-0">
          <BuilderScene
            property={property}
            locale={locale}
            chosen={chosen}
            brightness={state.brightness / 100}
            curtainsOpen={state.curtains / 100}
            locked={state.locked}
            acOn={chosen.includes("climate")}
            selectedRoom={selectedRoom}
            onSelectRoom={setSelectedRoom}
          />
          <p className="pointer-events-none absolute bottom-2 start-0 end-0 text-center font-mono text-[10px] text-slate">
            {ar ? "اسحب للدوران · اضغط أي غرفة" : "Drag to orbit · tap any room"}
          </p>
          {activeRoom && (
            <div className="absolute top-2.5 start-2.5 rounded-xl border border-hairline bg-void/90 p-2.5 backdrop-blur-sm">
              <p className="text-[12.5px] font-semibold text-platinum">{roomName(activeRoom, locale)}</p>
              <ul className="mt-1 space-y-0.5">
                {activeRoom.systems.map((sk) => {
                  const on = chosen.includes(sk);
                  const sys = SYSTEMS.find((x) => x.key === sk)!;
                  return (
                    <li key={sk} className="flex items-center gap-1.5 text-[10.5px]">
                      <span
                        className="size-1.5 rounded-full"
                        style={{ backgroundColor: sys.color, opacity: on ? 1 : 0.25 }}
                      />
                      <span className={on ? "text-chrome-dim" : "text-slate line-through"}>
                        {systemCopy(sk, locale).name}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>

        {/* Control panel */}
        <div className="order-3 min-h-0 overflow-y-auto">
          <ControlPanel
            locale={locale}
            chosen={chosen}
            climate={property.climate}
            state={state}
            setState={setState}
          />
        </div>
      </div>
    </div>
  );
}
