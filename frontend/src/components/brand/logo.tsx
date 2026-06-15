import { useId } from "react";
import { cn } from "@/lib/utils";

/**
 * Aurora Hub logomark — twin aurora arcs (emerald → sky → violet) rising from a
 * glowing hub node. Matches assets/brand/aurora-mark.svg. Inherits size from CSS
 * (width/height via className). Gradient ids are unique per instance.
 */
export function LogoMark({
  className,
  title = "Aurora Hub",
  ...props
}: React.SVGProps<SVGSVGElement> & { title?: string }) {
  const uid = useId();
  const aur = `aur-${uid}`;
  const glow = `glow-${uid}`;
  return (
    <svg
      viewBox="0 0 512 512"
      fill="none"
      role="img"
      aria-label={title}
      className={className}
      {...props}
    >
      <defs>
        <linearGradient id={aur} x1="40" y1="200" x2="472" y2="200" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#34d399" />
          <stop offset="0.48" stopColor="#38bdf8" />
          <stop offset="1" stopColor="#a78bfa" />
        </linearGradient>
        <radialGradient id={glow} cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#baf7df" />
          <stop offset="0.55" stopColor="#6ee7b7" />
          <stop offset="1" stopColor="#34d399" stopOpacity="0" />
        </radialGradient>
      </defs>
      <path d="M51 348 A205 205 0 0 1 461 348" stroke={`url(#${aur})`} strokeWidth="22" strokeLinecap="round" opacity="0.5" />
      <path d="M116 348 A140 140 0 0 1 396 348" stroke={`url(#${aur})`} strokeWidth="48" strokeLinecap="round" />
      <circle cx="256" cy="348" r="46" fill={`url(#${glow})`} opacity="0.85" />
      <circle cx="256" cy="348" r="23" fill="#f4fffb" />
    </svg>
  );
}

/**
 * Horizontal lockup: mark + "Aurora Hub" wordmark, with an optional tagline.
 * Mirrors the official lockup (Aurora in the aurora gradient, Hub in near-white).
 */
export function LogoLockup({
  className,
  tagline = "Make your DU dream come true",
  showTagline = true,
}: {
  className?: string;
  tagline?: string | null;
  showTagline?: boolean;
}) {
  return (
    <div className={cn("lockup", className)}>
      <LogoMark className="lockup-mark" />
      <div className="lockup-word">
        <span>
          <span className="lockup-a">Aurora</span> <span className="lockup-h">Hub</span>
        </span>
        {showTagline && tagline ? <span className="lockup-tag">{tagline}</span> : null}
      </div>
    </div>
  );
}
