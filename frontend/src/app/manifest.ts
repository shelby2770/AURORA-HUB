import type { MetadataRoute } from "next";

// Required so the manifest is emitted as a static file under `output: export`.
export const dynamic = "force-static";

// PWA manifest. Emitted as /manifest.webmanifest by the static export and
// auto-linked into <head> by Next. Icons live in /public.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Aurora Hub",
    short_name: "Aurora Hub",
    description: "CS MCQ practice for Dhaka University MSc admission prep",
    start_url: "/",
    display: "standalone",
    background_color: "#0a0a0a",
    theme_color: "#0a0a0a",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
