"use client";

import { useEffect } from "react";
import { Capacitor } from "@capacitor/core";
import type { PluginListenerHandle } from "@capacitor/core";

// One global, native-guarded bootstrap mounted once in layout.tsx. Wires the
// status bar, splash screen, the SINGLE soft-keyboard listener (rule 5), and
// the Android hardware back button (rule 9). All plugins are dynamically
// imported so the web bundle never pulls native code, and every effect no-ops
// off-device. Renders nothing.
export function NativeBootstrap() {
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;

    const handles: PluginListenerHandle[] = [];
    let cancelled = false;
    const track = (h: PluginListenerHandle) => {
      if (cancelled) void h.remove();
      else handles.push(h);
    };

    (async () => {
      // Status bar: overlay the WebView (so content reaches the notch) with
      // light icons for our dark background.
      try {
        const { StatusBar, Style } = await import("@capacitor/status-bar");
        await StatusBar.setOverlaysWebView({ overlay: true });
        await StatusBar.setStyle({ style: Style.Dark }); // light text on dark bg
      } catch {
        /* status-bar unavailable (e.g. iOS-only edge) — non-fatal */
      }

      // Soft keyboard (rule 5): toggle a body class so fixed bottom bars hide
      // instead of floating above the keyboard. Mount ONE listener here.
      try {
        const { Keyboard } = await import("@capacitor/keyboard");
        track(
          await Keyboard.addListener("keyboardWillShow", () =>
            document.body.classList.add("keyboard-open"),
          ),
        );
        track(
          await Keyboard.addListener("keyboardWillHide", () =>
            document.body.classList.remove("keyboard-open"),
          ),
        );
      } catch {
        /* keyboard plugin unavailable — non-fatal */
      }

      // Android hardware back (rule 9): step back through in-app history, or
      // exit at the root. No-ops on iOS (no hardware back button).
      try {
        const { App } = await import("@capacitor/app");
        track(
          await App.addListener("backButton", ({ canGoBack }) => {
            if (canGoBack) window.history.back();
            else void App.exitApp();
          }),
        );
      } catch {
        /* app plugin unavailable — non-fatal */
      }

      // Hide the splash once the shell is mounted and wired.
      try {
        const { SplashScreen } = await import("@capacitor/splash-screen");
        await SplashScreen.hide();
      } catch {
        /* splash plugin unavailable — non-fatal */
      }
    })();

    return () => {
      cancelled = true;
      for (const h of handles) void h.remove();
      document.body.classList.remove("keyboard-open");
    };
  }, []);

  return null;
}
