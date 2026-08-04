import type { Locale } from "@/lib/i18n/config";

export default function SyntraTvMockup({ locale }: { locale: Locale }) {
  const isAr = locale === "ar";
  const tabs = isAr
    ? ["الرئيسية", "تي في", "أفلام", "مسلسلات"]
    : ["Home", "TV", "Movies", "Series"];
  const apps = ["YouTube", "Netflix", "Disney+", "Prime Video", "Spotify"];
  const tiles = [
    { label: isAr ? "الإضاءة" : "Lighting", value: isAr ? "مضاءة" : "On" },
    { label: isAr ? "المناخ" : "Climate", value: "24°C" },
    { label: isAr ? "الستائر" : "Curtains", value: isAr ? "مغلقة" : "Closed" },
  ];

  return (
    <div className="flex h-full w-full flex-col bg-void" dir={isAr ? "rtl" : "ltr"}>
      <div className="flex items-center justify-between border-b border-hairline px-4 py-2.5 sm:px-5">
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-chrome-dim">
          SYNTRA TV
        </span>
        <div className="hidden items-center gap-4 font-mono text-[10px] uppercase tracking-widest sm:flex">
          {tabs.map((tab, i) => (
            <span key={tab} className={i === 0 ? "text-platinum" : "text-slate"}>
              {tab}
            </span>
          ))}
        </div>
        <span className="font-mono text-[10px] text-slate">9:41</span>
      </div>

      <div className="flex flex-1 flex-col gap-2.5 p-3 sm:gap-3 sm:p-4">
        <div
          className="relative flex flex-1 flex-col justify-end overflow-hidden rounded-md border border-hairline px-3.5 py-3"
          style={{
            background:
              "linear-gradient(135deg, rgba(76,141,255,0.16), var(--color-graphite-2) 70%)",
          }}
        >
          <p className="font-mono text-[8px] uppercase tracking-widest text-ion sm:text-[9px]">
            {isAr ? "الأكثر مشاهدة الآن" : "Trending now"}
          </p>
          <p className="mt-1 font-display text-sm font-bold text-platinum sm:text-base">
            {isAr ? "عرض مميّز" : "Featured Premiere"}
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          {apps.map((app) => (
            <span
              key={app}
              className="rounded-full border border-hairline px-2 py-0.5 font-mono text-[8px] text-chrome-dim sm:text-[9px]"
            >
              {app}
            </span>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-2.5 sm:gap-3">
          {tiles.map((tile) => (
            <div
              key={tile.label}
              className="flex flex-col justify-center rounded-md border border-hairline bg-graphite px-2 py-2 sm:px-3"
            >
              <p className="font-mono text-[8px] uppercase tracking-widest text-slate sm:text-[9px]">
                {tile.label}
              </p>
              <p className="mt-1 text-xs font-medium text-platinum sm:text-sm">{tile.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
