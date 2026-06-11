"use client";

import { useEffect } from "react";
import { Capacitor } from "@capacitor/core";

// Rule 3: Android WebView reports env(safe-area-inset-top)=0 even with
// viewport-fit cover + overlay status bar. We tag <html> with `.native-app`
// so CSS can apply a native-only inset floor (a floor on mobile-web would add
// dead space). Renders nothing.
export function PlatformClass() {
  useEffect(() => {
    if (Capacitor.isNativePlatform()) {
      const el = document.documentElement;
      el.classList.add("native-app");
      el.classList.add(`platform-${Capacitor.getPlatform()}`);
    }
  }, []);
  return null;
}
