import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";
import { PlatformClass } from "@/components/mobile/platform-class";
import { NativeBootstrap } from "@/components/mobile/native-bootstrap";
import { VisitTracker } from "@/components/analytics/visit-tracker";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Aurora Hub",
  description: "CS MCQ practice for Dhaka University MSc admission prep",
  applicationName: "Aurora Hub",
  appleWebApp: {
    capable: true,
    title: "Aurora Hub",
    statusBarStyle: "black-translucent",
  },
  // favicon.ico, icon.svg and apple-icon.png in this directory are auto-detected
  // by Next's file conventions; manifest.ts supplies the PWA icons.
};

// viewportFit:"cover" is required for Capacitor safe-area insets (see MOBILE.md).
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
  themeColor: "#0a0a0a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <PlatformClass />
        <NativeBootstrap />
        <VisitTracker />
        <Providers>{children}</Providers>
        <Toaster
          position="top-center"
          richColors
          closeButton
          duration={3500}
        />
      </body>
    </html>
  );
}
