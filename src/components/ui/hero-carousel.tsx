"use client";

import * as React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import { assetPath } from "@/lib/base-path";

export interface HeroSlide {
  src: string;
  label: string;
  title: string;
  caption: string;
}

interface HeroCarouselProps extends React.HTMLAttributes<HTMLDivElement> {
  slides: HeroSlide[];
  /** Milliseconds each slide stays on screen. */
  interval?: number;
  rtl?: boolean;
}

export function HeroCarousel({
  slides,
  interval = 6000,
  rtl = false,
  className,
  ...props
}: HeroCarouselProps) {
  const [index, setIndex] = React.useState(0);
  const [paused, setPaused] = React.useState(false);
  const touchStart = React.useRef<number | null>(null);

  const count = slides.length;
  const go = React.useCallback((n: number) => setIndex((n + count) % count), [count]);
  const next = React.useCallback(() => go(index + 1), [go, index]);
  const prev = React.useCallback(() => go(index - 1), [go, index]);

  // Auto-advance, paused on hover, focus, hidden tab, or reduced motion.
  React.useEffect(() => {
    if (paused || count < 2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => setIndex((i) => (i + 1) % count), interval);
    return () => clearInterval(id);
  }, [paused, count, interval]);

  React.useEffect(() => {
    const onVisibility = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowRight") rtl ? prev() : next();
    if (e.key === "ArrowLeft") rtl ? next() : prev();
  }

  return (
    <div
      role="region"
      aria-roledescription="carousel"
      aria-label={slides[index]?.label}
      tabIndex={0}
      onKeyDown={onKeyDown}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      onTouchStart={(e) => (touchStart.current = e.touches[0].clientX)}
      onTouchEnd={(e) => {
        if (touchStart.current === null) return;
        const dx = e.changedTouches[0].clientX - touchStart.current;
        if (Math.abs(dx) > 50) (dx < 0 ? (rtl ? prev : next) : (rtl ? next : prev))();
        touchStart.current = null;
      }}
      className={cn(
        "group relative aspect-[1672/941] w-full overflow-hidden outline-none",
        className
      )}
      {...props}
    >
      {slides.map((slide, i) => (
        <div
          key={slide.src}
          aria-hidden={i !== index}
          className={cn(
            "absolute inset-0 transition-opacity duration-[1200ms] ease-out motion-reduce:transition-none",
            i === index ? "opacity-100" : "opacity-0"
          )}
        >
          <Image
            src={assetPath(slide.src)}
            alt={slide.title}
            fill
            priority={i === 0}
            sizes="100vw"
            className={cn(
              "object-cover object-center",
              i === index ? "scale-[1.04]" : "scale-100",
              "transition-transform duration-[7000ms] ease-linear motion-reduce:transition-none"
            )}
          />
        </div>
      ))}

      {/* Scrims: a side wash for the copy zone, plus top and bottom fades.
          The wash follows the reading side so the copy sits in the empty area:
          left for LTR, right for RTL/Arabic. */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: `linear-gradient(${rtl ? 270 : 90}deg, rgba(11,12,14,0.92) 0%, rgba(11,12,14,0.72) 26%, rgba(11,12,14,0) 52%)`,
        }}
      />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, var(--color-void) 0%, rgba(11,12,14,0) 16%, rgba(11,12,14,0) 66%, rgba(11,12,14,0.9) 92%, var(--color-void) 100%)",
        }}
      />

      {/* Marketing copy, set in the empty (washed) half of each frame */}
      <div
        dir={rtl ? "rtl" : "ltr"}
        className={cn(
          "absolute inset-y-0 flex w-full items-end px-6 pb-16 sm:w-[52%] sm:items-center sm:px-10 sm:pb-0 lg:px-14",
          rtl ? "right-0" : "left-0"
        )}
      >
        <div key={index} className="syltra-slide-copy w-full max-w-md">
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-ion sm:text-[11px]">
            {slides[index]?.label}
          </p>
          <p className="font-display mt-2.5 text-balance text-xl font-bold leading-tight text-platinum sm:mt-3 sm:text-3xl lg:text-4xl">
            {slides[index]?.title}
          </p>
          <p className="mt-2.5 text-pretty text-[13px] leading-relaxed text-chrome-dim sm:mt-4 sm:text-base">
            {slides[index]?.caption}
          </p>

          <div className="mt-5 flex items-center gap-2 sm:mt-7">
            {slides.map((slide, i) => (
              <button
                key={slide.src}
                onClick={() => go(i)}
                aria-label={slide.title}
                aria-current={i === index}
                className={cn(
                  "h-1.5 rounded-full transition-all duration-300",
                  i === index ? "w-7 bg-ion" : "w-1.5 bg-platinum/35 hover:bg-platinum/70"
                )}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Arrows, revealed on hover for pointer users */}
      <button
        onClick={rtl ? next : prev}
        aria-label="Previous slide"
        className="absolute start-3 top-1/2 hidden h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-hairline-strong bg-void/50 text-platinum opacity-0 backdrop-blur-sm transition-opacity hover:bg-void/80 group-hover:opacity-100 sm:flex"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="rtl:rotate-180">
          <path d="M15 18l-6-6 6-6" />
        </svg>
      </button>
      <button
        onClick={rtl ? prev : next}
        aria-label="Next slide"
        className="absolute end-3 top-1/2 hidden h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-hairline-strong bg-void/50 text-platinum opacity-0 backdrop-blur-sm transition-opacity hover:bg-void/80 group-hover:opacity-100 sm:flex"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="rtl:rotate-180">
          <path d="M9 6l6 6-6 6" />
        </svg>
      </button>
    </div>
  );
}
