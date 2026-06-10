"use client";

import { useEffect, useRef, useState } from "react";

// Recomputes remaining time from absolute start + duration on every tick, so a
// dropped/backgrounded interval can't drift the clock (it self-corrects on the
// next tick). Calls onExpire exactly once when time runs out.
export function useExamTimer(
  startedAtMs: number | null,
  durationSeconds: number | null,
  onExpire: () => void,
): number | null {
  const [remaining, setRemaining] = useState<number | null>(null);
  const firedRef = useRef(false);
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  useEffect(() => {
    if (startedAtMs == null || durationSeconds == null) {
      setRemaining(null);
      return;
    }
    firedRef.current = false;

    const compute = () => {
      const elapsed = (Date.now() - startedAtMs) / 1000;
      const left = Math.max(0, Math.ceil(durationSeconds - elapsed));
      setRemaining(left);
      if (left <= 0 && !firedRef.current) {
        firedRef.current = true;
        onExpireRef.current();
      }
    };

    compute();
    const id = setInterval(compute, 500);
    return () => clearInterval(id);
  }, [startedAtMs, durationSeconds]);

  return remaining;
}

export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}
