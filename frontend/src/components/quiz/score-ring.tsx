"use client";

import { useEffect, useState } from "react";

// Animated circular score gauge. Mirrors the Aurora design mockup: a track ring
// plus an accent-gradient progress arc that sweeps to `pct` on mount.
export function ScoreRing({ pct }: { pct: number }) {
  const r = 86;
  const c = 2 * Math.PI * r;
  const [draw, setDraw] = useState(0);

  useEffect(() => {
    const id = requestAnimationFrame(() => setDraw(pct));
    return () => cancelAnimationFrame(id);
  }, [pct]);

  const offset = c - (draw / 100) * c;

  return (
    <div className="ring-wrap">
      <svg viewBox="0 0 200 200" className="score-ring">
        <defs>
          <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--accent-light)" />
            <stop offset="100%" stopColor="var(--accent)" />
          </linearGradient>
        </defs>
        <circle cx="100" cy="100" r={r} className="ring-track" />
        <circle
          cx="100"
          cy="100"
          r={r}
          className="ring-prog"
          style={{ strokeDasharray: c, strokeDashoffset: offset }}
        />
      </svg>
      <div className="ring-center">
        <div className="ring-pct">
          {Math.round(pct)}
          <span>%</span>
        </div>
        <div className="ring-sub">correct</div>
      </div>
    </div>
  );
}
