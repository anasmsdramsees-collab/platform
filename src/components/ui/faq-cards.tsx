import Link from "next/link";
import { InfoCard } from "./info-card";

export interface FaqItem {
  q: string;
  a: string;
}

export function FaqCards({
  items,
  footerLabel,
  footerCta,
  footerHref,
}: {
  items: FaqItem[];
  footerLabel?: string;
  footerCta?: string;
  footerHref?: string;
}) {
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        {items.map((item) => (
          <InfoCard key={item.q}>
            <p className="font-semibold leading-snug text-platinum">{item.q}</p>
            <p className="mt-2.5 text-sm leading-relaxed text-chrome-dim">{item.a}</p>
          </InfoCard>
        ))}
      </div>

      {footerLabel && footerCta && footerHref && (
        <p className="mt-10 text-center text-sm text-slate">
          {footerLabel}{" "}
          <Link href={footerHref} className="text-ion underline-offset-4 hover:underline">
            {footerCta}
          </Link>
        </p>
      )}
    </>
  );
}
