import type { ReactNode } from "react";

// Real protocol marks. Bluetooth and Zigbee come from the simple-icons set;
// Matter, Thread, Z-Wave and Wi-Fi are drawn to match their official logos.
export const PROTOCOL_ICONS: Record<string, ReactNode> = {
  "Bluetooth LE": (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 0C6.76 0 3.1484 2.4895 3.1484 12S6.76 24 12 24c5.24 0 8.8516-2.4895 8.8516-12S17.24 0 12 0zm-.7773 1.6816l6.2148 6.2149L13.334 12l4.1035 4.1035-6.2148 6.2149V14.125l-3.418 3.42-1.2422-1.2442L10.8515 12l-4.289-4.3008 1.2422-1.2441 3.418 3.4199V1.6816zm1.748 4.2442v3.9687l1.9844-1.9843-1.9844-1.9844zm0 8.1816v3.9668l1.9844-1.9844-1.9844-1.9824Z" />
    </svg>
  ),
  Zigbee: (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M11.988 0a11.85 11.85 0 00-8.617 3.696c7.02-.875 11.401-.583 13.289-.34 3.752.583 3.558 3.404 3.558 3.404L8.237 19.112c2.299.22 6.897.366 13.796-.631a11.86 11.86 0 001.912-6.469C23.945 5.374 18.595 0 11.988 0zm.232 4.31c-2.451-.014-5.772.146-9.963.723C.854 7.003.055 9.41.055 12.012.055 18.626 5.38 24 11.988 24c3.63 0 6.85-1.63 9.053-4.182-7.286.948-11.813.631-13.75.388-3.775-.56-3.557-3.404-3.557-3.404L15.691 4.474a38.635 38.635 0 00-3.471-.163Z" />
    </svg>
  ),
  Matter: (
    // Three petals at 120 degrees, the CSA Matter tri-star
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" aria-hidden>
      <path d="M12 12V3.2" />
      <path d="M12 12l7.62 4.4" />
      <path d="M12 12l-7.62 4.4" />
      <circle cx="12" cy="12" r="2.1" fill="currentColor" stroke="none" />
    </svg>
  ),
  Thread: (
    // Thread Group mark: a lowercase t inside a circle
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6.5v9a2.2 2.2 0 002.2 2.2H16" strokeLinecap="round" />
      <path d="M8 10.5h8" strokeLinecap="round" />
    </svg>
  ),
  "Z-Wave": (
    // Z-Wave: the Z with radio waves
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden>
      <path d="M4 7.5h8l-8 9h8" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16.5 8a6.5 6.5 0 010 8" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M19.5 5.5a10.5 10.5 0 010 13" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  "Wi-Fi": (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
      <path d="M2.5 9a14.5 14.5 0 0119 0" />
      <path d="M5.8 12.8a10 10 0 0112.4 0" />
      <path d="M9.1 16.4a5.2 5.2 0 015.8 0" />
      <circle cx="12" cy="19.6" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  ),
};
