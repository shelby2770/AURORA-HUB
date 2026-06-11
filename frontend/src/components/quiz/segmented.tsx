"use client";

import { cn } from "@/lib/utils";

export function Segmented<T extends string | number>({
  options,
  value,
  onChange,
  getLabel,
  testid,
}: {
  options: T[];
  value: T | null;
  onChange: (v: T) => void;
  getLabel?: (v: T) => string;
  testid?: string;
}) {
  return (
    <div className="grid grid-flow-col gap-2" data-testid={testid}>
      {options.map((opt) => (
        <button
          key={String(opt)}
          type="button"
          aria-pressed={value === opt}
          data-testid={testid ? `${testid}-${opt}` : undefined}
          data-active={value === opt}
          onClick={() => onChange(opt)}
          className={cn(
            "min-h-12 rounded-lg border-2 px-3 text-sm font-medium capitalize transition-colors active:scale-[0.98]",
            value === opt
              ? "border-primary bg-primary/10 text-primary"
              : "border-border bg-card hover:border-primary/40",
          )}
        >
          {getLabel ? getLabel(opt) : String(opt)}
        </button>
      ))}
    </div>
  );
}
