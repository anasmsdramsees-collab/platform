export default function ProductImagePlaceholder({ label }: { label: string }) {
  return (
    <div className="relative flex aspect-square w-full items-center justify-center overflow-hidden rounded-lg border border-dashed border-hairline-strong bg-graphite">
      <div className="pointer-events-none absolute inset-0 opacity-40" aria-hidden="true">
        <svg viewBox="0 0 200 200" className="h-full w-full">
          <line x1="0" y1="0" x2="200" y2="200" stroke="var(--color-hairline)" strokeWidth="1" />
          <line x1="200" y1="0" x2="0" y2="200" stroke="var(--color-hairline)" strokeWidth="1" />
        </svg>
      </div>
      <div className="relative flex flex-col items-center gap-3 px-6 text-center">
        <svg
          width="36"
          height="36"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--color-slate)"
          strokeWidth="1.5"
          aria-hidden="true"
        >
          <rect x="3" y="5" width="18" height="14" rx="2" />
          <circle cx="9" cy="10.5" r="1.75" />
          <path d="M21 16l-5.5-5-9.5 8" />
        </svg>
        <p className="font-mono text-[11px] uppercase tracking-widest text-slate">{label}</p>
      </div>
    </div>
  );
}
