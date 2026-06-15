"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { trackVisit } from "@/lib/api";

/**
 * Records a visit once per page load (and on client-side route changes).
 * Fire-and-forget — failures are swallowed in `trackVisit`, so this never
 * affects the UI.
 */
export function VisitTracker() {
  const pathname = usePathname();

  useEffect(() => {
    trackVisit(pathname);
  }, [pathname]);

  return null;
}
