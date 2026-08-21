"use client";

import { useState } from "react";
import { assetPath } from "@/lib/base-path";

export default function ProductSlides({ images, alt }: { images: string[]; alt: string }) {
  const [i, setI] = useState(0);
  if (images.length === 0) return null;
  const prev = () => setI((v) => (v - 1 + images.length) % images.length);
  const next = () => setI((v) => (v + 1) % images.length);

  return (
    <div className="group relative overflow-hidden rounded-lg border border-hairline bg-void-2">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={assetPath(images[i])}
        alt={alt}
        className="aspect-square w-full object-cover"
        loading="lazy"
      />
      {images.length > 1 && (
        <>
          <button
            type="button"
            onClick={prev}
            aria-label="previous"
            className="absolute start-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-void/60 text-platinum opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="rtl:rotate-180">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <button
            type="button"
            onClick={next}
            aria-label="next"
            className="absolute end-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-void/60 text-platinum opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="rtl:rotate-180">
              <path d="M9 6l6 6-6 6" />
            </svg>
          </button>
          <div className="absolute bottom-2 start-0 end-0 flex justify-center gap-1.5">
            {images.map((_, d) => (
              <button
                key={d}
                type="button"
                onClick={() => setI(d)}
                aria-label={`slide ${d + 1}`}
                className={`h-1.5 rounded-full transition-all ${d === i ? "w-5 bg-ion" : "w-1.5 bg-platinum/40"}`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
