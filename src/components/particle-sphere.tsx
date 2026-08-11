"use client";

import { useEffect, useRef } from "react";

interface Point {
  theta: number;
  phi: number;
}

export default function ParticleSphere() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const points: Point[] = [];
    const count = 260;
    for (let i = 0; i < count; i++) {
      const theta = Math.acos(1 - (2 * (i + 0.5)) / count);
      const phi = Math.PI * (1 + Math.sqrt(5)) * i;
      points.push({ theta, phi });
    }

    let frame = 0;
    let raf = 0;

    function resize() {
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
    }
    resize();
    window.addEventListener("resize", resize);

    function draw() {
      if (!canvas || !ctx) return;
      const w = canvas.width;
      const h = canvas.height;
      const r = Math.min(w, h) * 0.42;
      const cx = w / 2;
      const cy = h / 2;
      const rotation = frame * 0.0032;

      ctx.clearRect(0, 0, w, h);

      const projected = points.map((p) => {
        const x0 = Math.sin(p.theta) * Math.cos(p.phi + rotation);
        const y0 = Math.cos(p.theta);
        const z0 = Math.sin(p.theta) * Math.sin(p.phi + rotation);
        const scale = 1 / (2 - z0);
        return {
          x: cx + x0 * r * scale,
          y: cy + y0 * r * scale,
          z: z0,
          scale,
        };
      });

      projected.sort((a, b) => a.z - b.z);

      for (const p of projected) {
        const depth = (p.z + 1) / 2;
        const alpha = 0.15 + depth * 0.65;
        const size = (0.6 + depth * 1.6) * dpr;
        ctx.beginPath();
        ctx.fillStyle = `rgba(76,141,255,${alpha})`;
        ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
        ctx.fill();
      }

      frame += 1;
      if (!reduceMotion) raf = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      window.removeEventListener("resize", resize);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return <canvas ref={canvasRef} className="h-full w-full" aria-hidden="true" />;
}
