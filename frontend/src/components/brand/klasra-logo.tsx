import * as React from "react";
import { cn } from "@/lib/utils";

interface KlasraMarkProps {
  className?: string;
}

/**
 * Original geometric Klasra emblem:
 * A crisp architectural pillar (structured school system) paired with
 * two ascending angled planes (learning pathway & open book geometry).
 * Designed to stay razor-sharp from 16px favicons up to hero headers
 * on both light and dark surfaces.
 */
export function KlasraMark({ className }: KlasraMarkProps) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={cn("h-7 w-7 shrink-0", className)}
    >
      <rect width="32" height="32" rx="8" className="fill-primary" />
      {/* Left structural pillar */}
      <rect x="8.5" y="7.5" width="3.5" height="17" rx="1.25" fill="white" />
      {/* Upper ascending plane */}
      <path
        d="M14 15.2L20.6 8.1C21.1 7.6 21.8 7.5 22.4 7.5H23.7L17.2 14.8L14 15.2Z"
        fill="white"
      />
      {/* Lower forward plane (subtle emerald-tinted highlight for progression) */}
      <path
        d="M14 16.5L17.5 16L24 24.5H20.1C19.5 24.5 18.9 24.2 18.5 23.7L14 16.5Z"
        fill="#A5F3FC"
      />
    </svg>
  );
}

interface KlasraLogoProps {
  className?: string;
  markClassName?: string;
  showTagline?: boolean;
  inverted?: boolean;
}

export function KlasraLogo({
  className,
  markClassName,
  showTagline = false,
  inverted = false,
}: KlasraLogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <KlasraMark className={markClassName} />
      <span className="flex flex-col leading-none">
        <span
          className={cn(
            "font-display text-[17px] font-bold tracking-[-0.025em]",
            inverted ? "text-white" : "text-foreground"
          )}
        >
          Klasra
        </span>
        {showTagline && (
          <span
            className={cn(
              "mt-0.5 text-[10px] font-medium tracking-wide",
              inverted ? "text-zinc-400" : "text-muted-foreground"
            )}
          >
            Secondary LMS
          </span>
        )}
      </span>
    </span>
  );
}
