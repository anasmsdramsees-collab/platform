import Image from "next/image";
import { ImageSlider } from "@/components/ui/image-slider";
import type { Metadata } from "next";
import { isLocale, type Locale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { assetPath } from "@/lib/base-path";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  return { title: dict.meta.titleApps, description: dict.meta.description };
}

export default async function AppsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const dict = getDictionary(locale);
  const a = dict.appsPage;

  return (
    <section>
      <div className="mx-auto max-w-4xl px-5 py-20 text-center sm:px-8">
        <p className="font-mono text-[12px] tracking-[0.14em] text-slate uppercase">
          {a.eyebrow}
        </p>
        <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
          {a.title}
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-chrome-dim">{a.subtitle}</p>
      </div>

      <div className="mx-auto max-w-6xl px-5 pb-24 sm:px-8">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {a.cards.map((card) => (
            <div
              key={card.slug}
              className="overflow-hidden border border-hairline bg-void"
            >
              <div className="relative aspect-video overflow-hidden border-b border-hairline">
                <ImageSlider
                  images={
                    card.slug === "home-assistant"
                      ? ["/hero/home-dashboard.jpg", "/hero/home-arrive.jpg", "/hero/home-remote.jpg"]
                      : ["/hero/tv-interface.jpg", "/hero/tv-family.jpg"]
                  }
                  alt={card.name}
                  offset={card.slug === "home-assistant" ? 0 : 2200}
                />
              </div>
              <div className="p-8 sm:p-10">
                <p className="font-mono text-[11px] uppercase tracking-widest text-slate">
                  {card.status}
                </p>
                <div className="mt-4 flex items-center gap-3">
                  <Image
                    src={assetPath(
                      card.slug === "home-assistant"
                        ? "/brand/app-icon-home.png"
                        : "/brand/app-icon-tv.png"
                    )}
                    alt=""
                    width={64}
                    height={64}
                    className="h-8 w-8 rounded-md"
                  />
                  <p className="font-display text-2xl font-bold text-platinum">{card.name}</p>
                </div>
                <p className="mt-3 text-chrome-dim">{card.tagline}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
