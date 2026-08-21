import type { CSSProperties } from "react";
import ParticleSphere from "./particle-sphere";
import { PROTOCOL_ICONS, PROTOCOL_COLORS } from "./protocol-icons";

interface ProtocolItem {
  name: string;
}

const RINGS: { size: string; duration: number }[] = [
  { size: "w-40 h-40 sm:w-72 sm:h-72", duration: 22 },
  { size: "w-[15rem] h-[15rem] sm:w-[22rem] sm:h-[22rem]", duration: 32 },
];

export default function ProtocolOrbit({ items, coreLabel }: { items: ProtocolItem[]; coreLabel: string }) {
  const ring1 = items.slice(0, 4);
  const ring2 = items.slice(4, 8);
  const rings = [ring1, ring2];

  return (
    <div className="relative mx-auto flex h-[23rem] w-full max-w-lg items-center justify-center overflow-hidden sm:h-[32rem]">
      <div className="pointer-events-none absolute left-1/2 top-1/2 aspect-square w-24 -translate-x-1/2 -translate-y-1/2 sm:w-44">
        <ParticleSphere />
        <div className="absolute left-1/2 top-full -mt-4 -translate-x-1/2 text-center sm:-mt-8">
          <p
            className="whitespace-nowrap font-display text-[11px] font-bold tracking-wide text-ion sm:text-base"
            style={{ textShadow: "0 0 14px rgba(76,141,255,.9), 0 0 34px rgba(76,141,255,.5)" }}
          >
            {coreLabel}
          </p>
        </div>
      </div>

      {rings.map((ringItems, ringIndex) => {
        const orbit = RINGS[ringIndex];
        const isCW = ringIndex % 2 === 0;
        const orbitAnim = isCW ? "orbit-cw" : "orbit-ccw";
        const counterAnim = isCW ? "counter-cw" : "counter-ccw";
        const step = 360 / ringItems.length;

        return (
          <div
            key={ringIndex}
            className={`orbit-ring absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-hairline ${orbit.size}`}
          >
            {ringItems.map((item, i) => {
              const angle = i * step;
              return (
                <div
                  key={item.name}
                  className="absolute top-0 left-1/2 h-1/2 -ml-8 flex origin-bottom flex-col items-center justify-start sm:-ml-10"
                  style={
                    {
                      "--start-angle": `${angle}deg`,
                      animation: `${orbitAnim} ${orbit.duration}s linear infinite`,
                    } as CSSProperties
                  }
                >
                  <div
                    className="orbit-badge relative z-10 -mt-4 rounded-full border border-hairline-strong bg-graphite px-2.5 py-1 shadow-lg sm:-mt-6 sm:px-3 sm:py-1.5"
                    style={
                      {
                        "--counter-offset": `${-angle}deg`,
                        animation: `${counterAnim} ${orbit.duration}s linear infinite`,
                      } as CSSProperties
                    }
                  >
                    <span className="flex items-center gap-1 whitespace-nowrap font-mono text-[9.5px] text-white sm:gap-1.5 sm:text-[11px]">
                      {PROTOCOL_ICONS[item.name] && (
                        <span className="h-3.5 w-3.5 shrink-0 sm:h-4 sm:w-4 [&>svg]:h-full [&>svg]:w-full" style={{ color: PROTOCOL_COLORS[item.name] ?? "#fff" }}>
                          {PROTOCOL_ICONS[item.name]}
                        </span>
                      )}
                      {item.name}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
