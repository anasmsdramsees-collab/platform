"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { assetPath } from "@/lib/base-path";

interface Social {
  name: string;
  image: string;
  href?: string;
}

interface SocialLinksProps extends React.HTMLAttributes<HTMLDivElement> {
  socials: Social[];
}

export function SocialLinks({ socials, className, ...props }: SocialLinksProps) {
  const [hoveredSocial, setHoveredSocial] = React.useState<string | null>(null);
  const [rotation, setRotation] = React.useState<number>(0);
  const [clicked, setClicked] = React.useState<boolean>(false);
  const prefersReduced = React.useRef(false);

  React.useEffect(() => {
    prefersReduced.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  const animation = {
    scale: clicked ? [1, 1.3, 1] : 1,
    transition: { duration: 0.3 },
  };

  React.useEffect(() => {
    if (!clicked) return;
    const t = setTimeout(() => setClicked(false), 200);
    return () => clearTimeout(t);
  }, [clicked]);

  return (
    <div
      className={cn("flex flex-wrap items-center justify-center gap-0", className)}
      {...props}
    >
      {socials.map((social) => {
        const isHovered = hoveredSocial === social.name;
        const Tag = social.href ? "a" : "div";
        return (
          <Tag
            key={social.name}
            {...(social.href
              ? {
                  href: social.href,
                  target: social.href.startsWith("http") ? "_blank" : undefined,
                  rel: social.href.startsWith("http") ? "noopener noreferrer" : undefined,
                }
              : {})}
            className={cn(
              "relative cursor-pointer rounded-md px-5 py-2 transition-opacity duration-200",
              "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ion",
              hoveredSocial && !isHovered ? "opacity-50" : "opacity-100"
            )}
            onMouseEnter={() => {
              setHoveredSocial(social.name);
              setRotation(Math.random() * 20 - 10);
            }}
            onMouseLeave={() => setHoveredSocial(null)}
            onFocus={() => setHoveredSocial(social.name)}
            onBlur={() => setHoveredSocial(null)}
            onClick={() => setClicked(true)}
          >
            <span className="block text-lg font-medium text-platinum">{social.name}</span>
            <AnimatePresence>
              {isHovered && !prefersReduced.current && (
                <motion.div
                  className="pointer-events-none absolute bottom-0 left-0 right-0 flex h-full w-full items-center justify-center"
                  animate={animation}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <motion.img
                    key={social.name}
                    src={assetPath(social.image)}
                    alt=""
                    aria-hidden
                    className="size-16 drop-shadow-[0_10px_30px_rgba(0,0,0,0.55)]"
                    initial={{ y: -40, rotate: rotation, opacity: 0, filter: "blur(2px)" }}
                    animate={{ y: -50, opacity: 1, filter: "blur(0px)" }}
                    exit={{ y: -40, opacity: 0, filter: "blur(2px)" }}
                    transition={{ duration: 0.2 }}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </Tag>
        );
      })}
    </div>
  );
}
