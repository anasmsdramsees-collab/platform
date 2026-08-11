"use client";

import { useEffect, useRef } from "react";

class Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;

  constructor(x: number, y: number) {
    this.x = x;
    this.y = y;
    this.vx = (Math.random() - 0.5) * 2;
    this.vy = (Math.random() - 0.5) * 2;
    this.maxLife = 80 + Math.random() * 60;
    this.life = this.maxLife;
    this.size = 1 + Math.random() * 2;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.life -= 1;
    this.vx *= 0.98;
    this.vy *= 0.98;
  }

  draw(ctx: CanvasRenderingContext2D) {
    if (this.life <= 0) return;
    ctx.globalAlpha = this.life / this.maxLife;
    ctx.fillStyle = "rgba(76,141,255,0.85)";
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

/**
 * Animated ribbon-mesh background for the hero. Confined to its parent
 * container (not the viewport) so it can sit behind the existing hero
 * copy/CTAs/panel as a decorative layer.
 */
export default function RibbonMesh() {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx2d = canvas.getContext("2d", { alpha: false });
    if (!ctx2d) return;
    const ctx: CanvasRenderingContext2D = ctx2d;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let width = 0;
    let height = 0;
    let animationFrameId = 0;

    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const particles: Particle[] = [];
    const ripple = { x: 0, y: 0, radius: 0, maxRadius: 400, speed: 14, active: false };

    function resize() {
      if (!container || !canvas) return;
      const rect = container.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function pointerPos(e: MouseEvent | TouchEvent) {
      const rect = container!.getBoundingClientRect();
      const clientX = "touches" in e ? e.touches[0]?.clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0]?.clientY : e.clientY;
      return { x: (clientX ?? 0) - rect.left, y: (clientY ?? 0) - rect.top };
    }

    function handlePointerMove(e: MouseEvent | TouchEvent) {
      const p = pointerPos(e);
      mouse.targetX = p.x - width / 2;
      mouse.targetY = p.y - height / 2;
    }

    function handlePointerDown(e: MouseEvent | TouchEvent) {
      const p = pointerPos(e);
      if (p.x < 0 || p.y < 0 || p.x > width || p.y > height) return;
      ripple.x = p.x;
      ripple.y = p.y;
      ripple.radius = 0;
      ripple.active = true;
      for (let i = 0; i < 24; i++) particles.push(new Particle(p.x, p.y));
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);
    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("touchmove", handlePointerMove, { passive: true });
    window.addEventListener("mousedown", handlePointerDown);
    window.addEventListener("touchstart", handlePointerDown, { passive: true });

    let lastTime = performance.now();
    let time = 0;

    const noise = (x: number, t: number, o: number) =>
      (Math.sin(x * 0.0012 + t * 0.25 + o) + Math.cos(x * 0.0028 - t * 0.4 + o * 2)) / 2;

    function render(now: number) {
      const dt = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;
      time += dt * 0.85;

      const lerp = 1 - Math.exp(-9 * dt);
      mouse.x += (mouse.targetX - mouse.x) * lerp;
      mouse.y += (mouse.targetY - mouse.y) * lerp;

      ctx.fillStyle = "#0b0c0e";
      ctx.fillRect(0, 0, width, height);

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.update();
        p.draw(ctx);
        if (p.life <= 0) particles.splice(i, 1);
      }

      if (ripple.active && ripple.radius < ripple.maxRadius) {
        ripple.radius += ripple.speed;
      }

      const layers = [
        { count: 12, step: 5, offsetMod: 0, freq: 0.0035, amp: 46, speed: 1.1, primary: true },
        { count: 7, step: 7, offsetMod: 1.2, freq: 0.0075, amp: 24, speed: 0.7, primary: false },
      ];

      layers.forEach((layer) => {
        ctx.globalCompositeOperation = "source-over";
        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, `rgba(76,141,255,${layer.primary ? 0.06 : 0.02})`);
        gradient.addColorStop(0.5, `rgba(76,141,255,${layer.primary ? 0.55 : 0.22})`);
        gradient.addColorStop(1, `rgba(139,144,153,${layer.primary ? 0.08 : 0.02})`);

        for (let r = 0; r < layer.count; r++) {
          const progress = r / layer.count;
          const yOffset = height * 0.28 + r * (height * 0.05) + layer.offsetMod * 20;
          const baseAlpha = 1 - progress * 0.75;

          const rippleDistort =
            ripple.active && ripple.radius < ripple.maxRadius
              ? Math.sin((time * 2 + progress * Math.PI) * 2) *
                ((ripple.maxRadius / Math.max(ripple.radius, 1)) * 2)
              : 0;

          ctx.beginPath();
          for (let x = 0; x <= width + layer.step; x += layer.step) {
            const edge = Math.sin((x / width) * Math.PI);
            const nFreq = 1 + noise(x, time, progress) * 0.18;
            const nAmp = 1 + noise(x * 2, -time, progress * 0.5) * 0.15;

            const wave1 = Math.sin(x * (layer.freq * nFreq) + time * layer.speed + r * 0.18) * (layer.amp * edge * nAmp);
            const wave2 = Math.cos(x * 0.008 - time * 0.7 + r * 0.1) * (16 * edge);

            const cursorX = width / 2 + mouse.x;
            const distToMouse = Math.abs(x - cursorX);
            const mouseRadius = layer.primary ? 320 : 200;
            const mouseFactor = Math.exp(-Math.pow(distToMouse / mouseRadius, 2));
            const mouseDisplacement = Math.sin(x * 0.015 + time * 2.6) * (mouseFactor * (layer.primary ? 40 : 20) * edge);

            const rippleFactor = Math.exp(-Math.pow(Math.abs(distToMouse - ripple.radius) / (25 + rippleDistort), 2));
            const rippleDisplacement = ripple.active ? rippleFactor * rippleDistort * (1.6 - progress) : 0;

            const y = yOffset + wave1 + wave2 + mouseDisplacement + rippleDisplacement + mouse.y * (progress * 0.08);

            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }

          ctx.globalAlpha = baseAlpha;
          ctx.strokeStyle = gradient;
          ctx.lineWidth = (layer.primary ? 1.3 : 0.7) + (1 - progress) * 0.4;
          ctx.stroke();
        }
      });

      ctx.globalAlpha = 1;
      animationFrameId = requestAnimationFrame(render);
    }

    if (reduceMotion) {
      ctx.fillStyle = "#0b0c0e";
      ctx.fillRect(0, 0, width, height);
    } else {
      animationFrameId = requestAnimationFrame(render);
    }

    return () => {
      cancelAnimationFrame(animationFrameId);
      ro.disconnect();
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("touchmove", handlePointerMove);
      window.removeEventListener("mousedown", handlePointerDown);
      window.removeEventListener("touchstart", handlePointerDown);
    };
  }, []);

  return (
    <div ref={containerRef} className="pointer-events-none absolute inset-0">
      <canvas ref={canvasRef} aria-hidden="true" className="block" />
    </div>
  );
}
