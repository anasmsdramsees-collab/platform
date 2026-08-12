"use client";

import React, { useState, useRef, useLayoutEffect, cloneElement } from "react";

export type NavItem = {
  id: string | number;
  icon: React.ReactElement<React.SVGProps<SVGSVGElement>>;
  label?: string;
  href?: string;
  onClick?: () => void;
};

type LimelightNavProps = {
  items: NavItem[];
  activeIndex?: number;
  defaultActiveIndex?: number;
  onTabChange?: (index: number) => void;
  className?: string;
  limelightClassName?: string;
  iconContainerClassName?: string;
  iconClassName?: string;
};

/** An adaptive-width navigation bar with a "limelight" effect that highlights the active item. */
export function LimelightNav({
  items,
  activeIndex: controlledIndex,
  defaultActiveIndex = 0,
  onTabChange,
  className = "",
  limelightClassName = "",
  iconContainerClassName = "",
  iconClassName = "",
}: LimelightNavProps) {
  const [internalIndex, setInternalIndex] = useState(defaultActiveIndex);
  const activeIndex = controlledIndex ?? internalIndex;
  const [isReady, setIsReady] = useState(false);
  const navItemRefs = useRef<(HTMLAnchorElement | null)[]>([]);
  const limelightRef = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    if (items.length === 0) return;

    const limelight = limelightRef.current;
    const activeItem = navItemRefs.current[activeIndex];

    if (limelight && activeItem) {
      const newLeft = activeItem.offsetLeft + activeItem.offsetWidth / 2 - limelight.offsetWidth / 2;
      limelight.style.left = `${newLeft}px`;

      if (!isReady) {
        setTimeout(() => setIsReady(true), 50);
      }
    }
  }, [activeIndex, isReady, items]);

  if (items.length === 0) return null;

  const handleItemClick = (index: number, itemOnClick?: () => void) => {
    setInternalIndex(index);
    onTabChange?.(index);
    itemOnClick?.();
  };

  return (
    <nav
      className={`relative inline-flex h-16 items-center rounded-lg border border-hairline bg-void-2 px-2 text-platinum ${className}`}
    >
      {items.map(({ id, icon, label, href, onClick }, index) => (
        <a
          key={id}
          ref={(el) => {
            navItemRefs.current[index] = el;
          }}
          href={href}
          className={`relative z-20 flex h-full cursor-pointer items-center justify-center p-5 ${iconContainerClassName}`}
          onClick={(event) => {
            if (!href) event.preventDefault();
            handleItemClick(index, onClick);
          }}
          aria-label={label}
          aria-current={activeIndex === index ? "page" : undefined}
        >
          {cloneElement(icon, {
            className: `h-6 w-6 transition-opacity duration-100 ease-in-out ${
              activeIndex === index ? "opacity-100" : "opacity-40"
            } ${icon.props.className || ""} ${iconClassName}`,
          })}
        </a>
      ))}

      <div
        ref={limelightRef}
        className={`absolute top-0 z-10 h-[5px] w-11 rounded-full bg-ion shadow-[0_50px_15px_var(--color-ion)] ${
          isReady ? "transition-[left] duration-400 ease-in-out" : ""
        } ${limelightClassName}`}
        style={{ left: "-999px" }}
      >
        <div className="pointer-events-none absolute left-[-30%] top-[5px] h-14 w-[160%] bg-gradient-to-b from-ion/30 to-transparent [clip-path:polygon(5%_100%,25%_0,75%_0,95%_100%)]" />
      </div>
    </nav>
  );
}
