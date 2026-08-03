import type { Locale } from "@/lib/i18n/config";

export default function SyntraTvMockup({ locale }: { locale: Locale }) {
  const isAr = locale === "ar";
  const tabs = isAr
    ? ["الرئيسية", "الكاميرات", "الغرف", "الإشعارات"]
    : ["Home", "Cameras", "Rooms", "Notifications"];
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

      <div className="grid flex-1 grid-cols-5 gap-2.5 p-3 sm:gap-3 sm:p-4">
        <div className="col-span-3 flex flex-col gap-2.5 sm:gap-3">
          <div className="rounded-md border border-hairline bg-graphite px-3.5 py-3">
            <p className="font-mono text-[9px] uppercase tracking-widest text-slate">
              {isAr ? "طاقة اليوم" : "Today's energy"}
            </p>
            <p className="mt-1 font-mono text-xl font-semibold text-ion sm:text-2xl">
              2.4 <span className="text-xs text-chrome-dim">kWh</span>
            </p>
          </div>
          <div className="grid flex-1 grid-cols-3 gap-2.5 sm:gap-3">
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

        <div className="col-span-2 flex flex-col gap-1.5 sm:gap-2">
          <p className="font-mono text-[9px] uppercase tracking-widest text-slate">
            {isAr ? "الكاميرات المباشرة" : "Live cameras"}
          </p>
          <div className="grid flex-1 grid-cols-2 gap-1.5 sm:gap-2">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="relative overflow-hidden rounded-md border border-hairline"
                style={{
                  background:
                    "linear-gradient(135deg, var(--color-graphite-2), var(--color-void-2))",
                }}
              >
                <span className="absolute start-1 top-1 rounded-sm bg-void/80 px-1 font-mono text-[7px] tracking-wider text-ion">
                  LIVE
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
