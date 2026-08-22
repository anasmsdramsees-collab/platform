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
    lights: true,
    curtains: true,
    locked: true,
    temperature: 22,
    camera: null,
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
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-8 sm:py-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
            {ar ? "أنت تبني" : "You are building"}
          </p>
          <h1 className="font-display text-2xl font-bold text-platinum sm:text-3xl">{copy.name}</h1>
        </div>
        <button
          onClick={() => {
            setKind(null);
            setSelectedRoom(null);
          }}
          className="rounded-lg border border-hairline px-4 py-2 text-xs text-chrome-dim hover:border-hairline-strong hover:text-platinum"
        >
          {ar ? "غيّر النوع" : "Change type"}
        </button>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_20rem]">
        {/* 3D view */}
        <div className="relative h-[26rem] overflow-hidden rounded-2xl border border-hairline bg-void sm:h-[34rem]">
          <BuilderScene
            property={property}
            locale={locale}
            chosen={chosen}
            lightsOn={state.lights}
            selectedRoom={selectedRoom}
            onSelectRoom={setSelectedRoom}
          />
          <p className="pointer-events-none absolute bottom-3 start-0 end-0 text-center font-mono text-[10px] text-slate">
            {ar ? "اسحب للدوران · اضغط أي غرفة" : "Drag to orbit · tap any room"}
          </p>
          {activeRoom && (
            <div className="absolute top-3 start-3 rounded-xl border border-hairline bg-void/90 p-3 backdrop-blur-sm">
              <p className="text-sm font-semibold text-platinum">{roomName(activeRoom, locale)}</p>
              <ul className="mt-1.5 space-y-0.5">
                {activeRoom.systems.map((s) => {
                  const on = chosen.includes(s);
                  const sys = SYSTEMS.find((x) => x.key === s)!;
                  return (
                    <li key={s} className="flex items-center gap-1.5 text-[11px]">
                      <span
                        className="size-1.5 rounded-full"
                        style={{ backgroundColor: sys.color, opacity: on ? 1 : 0.25 }}
                      />
                      <span className={on ? "text-chrome-dim" : "text-slate line-through"}>
                        {systemCopy(s, locale).name}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          <div className="rounded-2xl border border-hairline bg-graphite/70 p-4">
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
              {ar ? "اختر الأنظمة" : "Choose systems"}
            </p>
            <div className="mt-3 space-y-2">
              {SYSTEMS.map((s) => {
                const on = chosen.includes(s.key);
                const c = systemCopy(s.key, locale);
                return (
                  <button
                    key={s.key}
                    onClick={() => toggle(s.key)}
                    className={cn(
                      "flex w-full items-start gap-3 rounded-xl border p-3 text-start transition-colors",
                      on ? "border-transparent bg-white/10" : "border-hairline hover:border-hairline-strong"
                    )}
                  >
                    <span
                      className="mt-1 size-2.5 shrink-0 rounded-full transition-opacity"
                      style={{ backgroundColor: s.color, opacity: on ? 1 : 0.3 }}
                    />
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold text-platinum">{c.name}</span>
                      <span className="mt-0.5 block text-[11.5px] leading-relaxed text-slate">{c.desc}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <ControlPanel locale={locale} chosen={chosen} state={state} setState={setState} />
        </div>
      </div>

      {/* Summary and conversion */}
      <div className="mt-6 rounded-2xl border border-hairline bg-graphite/70 p-6 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-5">
          <div>
            <p className="font-display text-lg font-bold text-platinum">
              {ar ? "هذا ما بنيته" : "What you built"}
            </p>
            <p className="mt-1.5 text-sm text-chrome-dim">
              {ar
                ? `${copy.name} · ${summary.rooms} غرفة · ${chosen.length} أنظمة · نحو ${summary.points} نقطة تحكم`
                : `${copy.name} · ${summary.rooms} rooms · ${chosen.length} systems · around ${summary.points} control points`}
            </p>
            <p className="mt-2 text-[11.5px] text-slate">
              {ar
                ? "الأرقام تقديرية لغرض التجربة. المعاينة على الموقع هي التي تحدد العدد النهائي."
                : "These figures are indicative. The site survey decides the final count."}
            </p>
          </div>
          <Link
            href={`/${locale}/quote?from=builder&kind=${property.kind}&systems=${chosen.join(",")}`}
            className="rounded-lg bg-platinum px-7 py-3 text-sm font-semibold text-void transition-opacity hover:opacity-90"
          >
            {ar ? "احجز معاينة مجانية" : "Book a free survey"}
          </Link>
        </div>
      </div>
    </div>
  );
}
