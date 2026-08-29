import { assetPath } from "@/lib/base-path";
import { HEALTH, HERO_NODES } from "@/lib/health-content";

/**
 * The "connected view" hero graphic: a central SYLTRA mark tile linked by
 * glowing green paths to six glassy ecosystem tiles. Built with HTML + CSS so
 * the glass surfaces and the central mark adapt to the light/dark theme; only
 * the connecting lines are SVG. The central mark uses a CSS mask so it inherits
 * the theme's foreground colour (dark on light, light on dark).
 */
const NODES = [
  { x: 50, y: 6 },
  { x: 85, y: 27 },
  { x: 85, y: 69 },
  { x: 50, y: 92 },
  { x: 15, y: 69 },
  { x: 15, y: 27 },
].map((p, i) => ({ ...p, ...HERO_NODES[i] }));

const CX = 50;
const CY = 48;

export default function HealthHeroGraphic({ className = "" }: { className?: string }) {
  const a = HEALTH.accent;
  return (
    <div className={`relative aspect-square w-full ${className}`}>
      {/* ambient glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: `radial-gradient(45% 45% at ${CX}% ${CY}%, rgba(${HEALTH.rgb},0.16), transparent 70%)` }}
        aria-hidden
      />

      {/* connecting lines */}
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden>
        <defs>
          <filter id="hfglow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="0.6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {NODES.map((n, i) => {
          const d = `M ${n.x} ${n.y} Q ${(n.x + CX) / 2} ${(n.y + CY) / 2 + (n.y < CY ? 6 : -6)} ${CX} ${CY}`;
          return (
            <g key={i}>
              <path d={d} fill="none" stroke={a} strokeOpacity="0.28" strokeWidth="0.5" />
              <path d={d} fill="none" stroke={a} strokeWidth="0.5" filter="url(#hfglow)" className="health-node-dot" style={{ animationDelay: `${i * 0.4}s` }} />
            </g>
          );
        })}
      </svg>

      {/* ecosystem tiles */}
      {NODES.map((n, i) => (
        <div
          key={i}
          className="absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${n.x}%`, top: `${n.y}%` }}
        >
          <div
            className="flex w-[92px] flex-col items-center gap-2 rounded-2xl border border-hairline-strong bg-void-2/80 p-3 backdrop-blur sm:w-[108px]"
            style={{ boxShadow: `0 10px 30px -12px rgba(${HEALTH.rgb},0.35)` }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetPath(n.icon)} alt={n.label} className="h-9 w-9 sm:h-10 sm:w-10" />
            <span className="text-center font-mono text-[9.5px] leading-tight text-chrome sm:text-[10.5px]" dir="ltr">
              {n.label}
            </span>
          </div>
        </div>
      ))}

      {/* central SYLTRA mark tile */}
      <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${CX}%`, top: `${CY}%` }}>
        <div
          className="grid h-[104px] w-[104px] place-items-center rounded-[26px] border bg-void-2/90 backdrop-blur sm:h-[120px] sm:w-[120px]"
          style={{ borderColor: `rgba(${HEALTH.rgb},0.5)`, boxShadow: `0 0 0 6px rgba(${HEALTH.rgb},0.10), 0 16px 40px -12px rgba(${HEALTH.rgb},0.5)` }}
        >
          <span
            className="block h-14 w-14 sm:h-16 sm:w-16"
            style={{
              backgroundColor: "var(--color-platinum)",
              WebkitMaskImage: `url(${assetPath("/brand/health-icons/syltra-mark-white.png")})`,
              maskImage: `url(${assetPath("/brand/health-icons/syltra-mark-white.png")})`,
              WebkitMaskSize: "contain",
              maskSize: "contain",
              WebkitMaskRepeat: "no-repeat",
              maskRepeat: "no-repeat",
              WebkitMaskPosition: "center",
              maskPosition: "center",
            }}
            aria-hidden
          />
        </div>
      </div>
    </div>
  );
}
