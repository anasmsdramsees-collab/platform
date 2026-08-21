"use client";

import * as React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import { assetPath } from "@/lib/base-path";

interface ImageSliderProps extends React.HTMLAttributes<HTMLDivElement> {
  images: string[];
  alt: string;
  /** Milliseconds each frame stays on screen. */
  interval?: number;
  /** Delay before the first advance, so sibling sliders do not flip in lockstep. */
  offset?: number;
}

export function ImageSlider({
  images,
  alt,
  interval = 5000,
  offset = 0,
  className,
  ...props
}: ImageSliderProps) {
  const [index, setIndex] = React.useState(0);
  const [paused, setPaused] = React.useState(false);
  const count = images.length;

  React.useEffect(() => {
    if (paused || count < 2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let id: ReturnType<typeof setInterval>;
    const start = setTimeout(() => {
      setIndex((i) => (i + 1) % count);
      id = setInterval(() => setIndex((i) => (i + 1) % count), interval);
    }, offset + interval);
    return () => {
      clearTimeout(start);
      clearInterval(id);
    };
  }, [paused, count, interval, offset]);

  React.useEffect(() => {
    const onVisibility = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  return (
    <div
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      className={cn("relative h-full w-full overflow-hidden", className)}
      {...props}
    >
      {images.map((src, i) => (
        <Image
          key={src}
          src={assetPath(src)}
          alt={i === 0 ? alt : ""}
          fill
          sizes="(min-width: 640px) 50vw, 100vw"
          className={cn(
            "object-cover object-center transition-opacity duration-1000 ease-out motion-reduce:transition-none",
            i === index ? "opacity-100" : "opacity-0"
          )}
        />
      ))}

      {count > 1 && (
        <div className="absolute inset-x-0 bottom-3 flex items-center justify-center gap-1.5">
          {images.map((src, i) => (
            <button
              key={src}
              onClick={() => setIndex(i)}
              aria-label={`${alt} ${i + 1}`}
              aria-current={i === index}
              className={cn(
                "h-1 rounded-full transition-all duration-300",
                i === index ? "w-5 bg-ion" : "w-1 bg-platinum/40 hover:bg-platinum/75"
              )}
            />
          ))}
        </div>
      )}
    </div>
  );
}
