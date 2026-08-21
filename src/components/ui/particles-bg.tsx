"use client";

import { useEffect, useCallback } from "react";

// Interactive particle network background (particles.js via CDN).
// Adapted for Syltra One: the site is dark-only, so the palette is fixed to the
// brand blue and the container is transparent so it sits on the page's bg-void.
export default function ParticlesComponent() {
  const initParticles = useCallback((isDark: boolean) => {
    const oldCanvas = document.querySelector("#particles-js canvas");
    if (oldCanvas) oldCanvas.remove();

    // @ts-ignore
    if (window.pJSDom?.length > 0) {
      // @ts-ignore
      window.pJSDom.forEach((p) => p.pJS.fn.vendors.destroypJS());
      // @ts-ignore
      window.pJSDom = [];
    }

    const colors = isDark
      ? { particles: "#6f97d6", lines: "#4a6b9c", accent: "#6f97d6" }
      : { particles: "#0277bd", lines: "#0288d1", accent: "#039be5" };

    // @ts-ignore
    window.particlesJS("particles-js", {
      particles: {
        number: { value: 120, density: { enable: true, value_area: 900 } },
        color: { value: colors.particles },
        shape: { type: "circle", stroke: { width: 0.5, color: colors.accent } },
        opacity: { value: 0.6, random: true, anim: { enable: true, speed: 1, opacity_min: 0.25 } },
        size: { value: 2.6, random: true, anim: { enable: true, speed: 2, size_min: 1 } },
        line_linked: { enable: true, distance: 160, color: colors.lines, opacity: 0.42, width: 1 },
        move: { enable: true, speed: 1.4, random: true, out_mode: "bounce" },
      },
      interactivity: {
        detect_on: "window",
        events: {
          onhover: { enable: true, mode: "grab" },
          onclick: { enable: false, mode: "push" },
          resize: true,
        },
        modes: {
          grab: { distance: 210, line_linked: { opacity: 0.75 } },
          push: { particles_nb: 4 },
          repulse: { distance: 180, duration: 0.4 },
        },
      },
      retina_detect: true,
    });
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const html = document.documentElement;
    // Syltra One is a dark-only site; fall back to dark unless explicitly light.
    const detectDark = () => html.getAttribute("data-theme") !== "light";

    let observer: MutationObserver | undefined;
    const boot = () => {
      initParticles(detectDark());
      observer = new MutationObserver(() => initParticles(detectDark()));
      observer.observe(html, { attributes: true, attributeFilter: ["class", "data-theme"] });
    };

    // @ts-ignore
    if (window.particlesJS) {
      boot();
      return () => observer?.disconnect();
    }

    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js";
    script.async = true;
    script.onload = boot;
    document.body.appendChild(script);

    return () => {
      observer?.disconnect();
      if (script.parentNode) script.parentNode.removeChild(script);
    };
  }, [initParticles]);

  return (
    <div
      id="particles-js"
      aria-hidden
      className="absolute inset-0 h-full w-full bg-transparent"
    />
  );
}
