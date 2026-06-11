import type { CapacitorConfig } from "@capacitor/cli";
import { KeyboardResize } from "@capacitor/keyboard";

// Aurora Hub native shell. The web app is a Next.js static export (`output:'export'`),
// so Capacitor just serves the built `out/` directory inside a WebView.
// Plugin blocks below are read at runtime by their plugins (installed in Phase 1+);
// declaring them now is harmless and keeps native config in one place.
const config: CapacitorConfig = {
  appId: "com.aurorahub.app",
  appName: "Aurora Hub",
  webDir: "out",
  backgroundColor: "#0a0a0a", // matches the dark theme --background
  plugins: {
    SplashScreen: {
      backgroundColor: "#0a0a0a",
      // Phase 1 hides the splash manually once the app shell is ready.
      launchAutoHide: true,
      androidScaleType: "CENTER_CROP",
    },
    StatusBar: {
      // Overlay the WebView so content can use the notch area (rules 2–3).
      overlaysWebView: true,
      style: "DARK", // dark background → light status-bar content
      backgroundColor: "#0a0a0a",
    },
    Keyboard: {
      // Native resize so the WebView shrinks above the soft keyboard (rule 5).
      resize: KeyboardResize.Native,
    },
  },
};

export default config;
