import type { Locale } from "@/lib/i18n/config";
import { assetPath } from "@/lib/base-path";

/**
 * Prominent "Aligned with Saudi Vision 2030" band, flanked by the official
 * portraits of the King and the Crown Prince. Center band + side portraits.
 */
export default function VisionBand({ locale }: { locale: Locale }) {
  const ar = locale === "ar";

  const fade =
    "linear-gradient(to bottom, transparent 0%, #000 14%, #000 68%, transparent 100%)";

  const Portrait = ({
    src,
    name,
    title,
  }: {
    src: string;
    name: string;
    title: string;
  }) => (
    <figure className="w-[46%] max-w-[300px] lg:w-[300px]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={assetPath(src)}
        alt={name}
        className="mx-auto aspect-[3/4] w-full object-cover object-top"
        style={{ maskImage: fade, WebkitMaskImage: fade }}
      />
      <figcaption className="-mt-6 text-center">
        <p className="text-[13px] font-semibold text-platinum sm:text-sm">{name}</p>
        <p className="mt-0.5 font-mono text-[10.5px] text-slate">{title}</p>
      </figcaption>
    </figure>
  );

  return (
    <section className="relative overflow-hidden border-b border-hairline">
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: "radial-gradient(70% 120% at 50% 0%, rgba(191,198,208,0.10), transparent 62%)" }}
        aria-hidden
      />
      <div className="relative mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-8 px-5 py-20 sm:py-24 lg:flex-nowrap lg:gap-10 lg:px-8">
        <div className="order-2 flex w-[42%] justify-center lg:order-1 lg:w-auto">
          <Portrait
            src="/brand/king.jpg"
            name={ar ? "الملك سلمان بن عبدالعزيز آل سعود" : "King Salman bin Abdulaziz Al Saud"}
            title={ar ? "خادم الحرمين الشريفين — حفظه الله" : "Custodian of the Two Holy Mosques"}
          />
        </div>

        <div className="order-1 w-full max-w-xl text-center lg:order-2 lg:w-auto">
          <p className="font-mono text-[12px] uppercase tracking-[0.14em]" style={{ color: "#BFC6D0" }}>
            {ar ? "التزام وطني" : "National commitment"}
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={assetPath("/brand/vision-2030.png")}
            alt={ar ? "رؤية المملكة العربية السعودية 2030" : "Saudi Vision 2030"}
            className="mx-auto mt-6 h-20 w-auto sm:h-28"
          />
          <h2 className="font-display mt-8 text-balance text-2xl font-bold leading-tight text-platinum sm:text-4xl">
            {ar ? "داعمون لرؤية المملكة العربية السعودية 2030" : "Proud supporters of Saudi Vision 2030"}
          </h2>
          <p className="mx-auto mt-4 max-w-md text-balance text-sm text-chrome-dim sm:text-base">
            {ar
              ? "نبني تقنية وطنية تخدم أهداف التحوّل الرقمي وجودة الحياة والاقتصاد المتنوّع في المملكة."
              : "Building national technology that serves the Kingdom's digital-transformation, quality-of-life and diversified-economy goals."}
          </p>
        </div>

        <div className="order-3 flex w-[42%] justify-center lg:w-auto">
          <Portrait
            src="/brand/crown-prince.jpg"
            name={ar ? "الأمير محمد بن سلمان بن عبدالعزيز" : "Prince Mohammed bin Salman"}
            title={ar ? "ولي العهد رئيس مجلس الوزراء — حفظه الله" : "Crown Prince & Prime Minister"}
          />
        </div>
      </div>
    </section>
  );
}
