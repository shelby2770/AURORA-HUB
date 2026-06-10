import type { NextConfig } from "next";

// Static export for Capacitor: no SSR, no API routes, no server fetching.
// The app is a client-side SPA that calls the FastAPI backend.
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
