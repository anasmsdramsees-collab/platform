import type { Locale } from "@/lib/i18n/config";
import { HEALTH, ECOSYSTEMS } from "@/lib/health-content";

/** The four target ecosystems, editorial hairline matrix + status + disclosure. */
export default function IntegrationsGrid({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  return (
    <section id="ecosystems" className="border-b border-hairline">
      <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8 sm:py-24">
        <p className="font-mono text-[12px] uppercase tracking-[0.14em]" style={{ color: HEALTH.accent }}>
          {ar ? "منظومات مستهدفة" : "Target ecosystems"}
        </p>
        <h2 className="font-display mt-3 max-w-2xl text-balance text-3xl font-bold text-platinum sm:text-4xl">
          {ar ? "مصممة للربط مع الأنظمة التي تستخدمها بالفعل." : "Designed to connect with the ecosystems you already use."}
        </h2>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-chrome-dim sm:text-base">
          {ar
            ? "تستهدف سيلترا هيلث التكامل مع أبرز منظومات الصحة والأجهزة القابلة للارتداء، لتقليل تشتت البيانات ومنح المستخدم رؤية واحدة بعد موافقته."
            : "SYLTRA HEALTH is targeting integration with leading health and wearable ecosystems to reduce fragmented data and give users one view after permission is granted."}
        </p>

        <div className="mt-10 grid grid-cols-1 border-s border-t border-hairline sm:grid-cols-2">
          {ECOSYSTEMS.map((e) => (
            <div key={e.key} className="border-b border-e border-hairline p-6 sm:p-8">
              <div className="flex items-center gap-3">
                <span
                  className="inline-block h-2.5 w-2.5 flex-none rounded-full"
                  style={{ backgroundColor: HEALTH.accent }}
                  aria-hidden
                />
                <h3 className="font-display text-lg font-bold text-platinum" dir="ltr">
                  {e.name}
                </h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-chrome-dim">
                {ar ? e.ar : e.en}
              </p>
              <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.12em] text-slate">
                {ar ? "الحالة" : "Status"} · {locale === "ar" ? e.status.ar : e.status.en}
              </p>
            </div>
          ))}
        </div>

        <p className="mt-6 max-w-3xl text-[12.5px] leading-relaxed text-slate">
          {ar
            ? "ظهور الاسم أو الشعار يوضح التكامل التقني المستهدف ولا يعني وجود شراكة أو اعتماد من الشركة المالكة ما لم يُعلن ذلك رسمياً."
            : "Displaying a name or logo describes a targeted technical integration and does not imply a partnership or endorsement unless formally announced."}
        </p>
      </div>
    </section>
  );
}
