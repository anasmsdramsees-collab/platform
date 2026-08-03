"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { HomeAction } from "@/lib/voice-commands";

interface HomeControlsValue {
  lightsOn: boolean;
  climateOn: boolean;
  curtainsOpen: boolean;
  setLightsOn: (v: boolean) => void;
  setClimateOn: (v: boolean) => void;
  setCurtainsOpen: (v: boolean) => void;
  applyAction: (action: HomeAction) => void;
}

const HomeControlsContext = createContext<HomeControlsValue | null>(null);

export function HomeControlsProvider({ children }: { children: ReactNode }) {
  const [lightsOn, setLightsOn] = useState(true);
  const [climateOn, setClimateOn] = useState(true);
  const [curtainsOpen, setCurtainsOpen] = useState(false);

  function applyAction(action: HomeAction) {
    if (action.kind === "lights") setLightsOn(action.value);
    if (action.kind === "climate") setClimateOn(action.value);
    if (action.kind === "curtains") setCurtainsOpen(action.value);
  }

  return (
    <HomeControlsContext.Provider
      value={{ lightsOn, climateOn, curtainsOpen, setLightsOn, setClimateOn, setCurtainsOpen, applyAction }}
    >
      {children}
    </HomeControlsContext.Provider>
  );
}

export function useHomeControls(): HomeControlsValue {
  const ctx = useContext(HomeControlsContext);
  if (!ctx) throw new Error("useHomeControls must be used within HomeControlsProvider");
  return ctx;
}
