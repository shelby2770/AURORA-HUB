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
  const idx = Math.max(
    0,
    options.findIndex((o) => o === value),
  );

  return (
    <div
      className="seg"
      style={{ ["--n" as string]: options.length }}
      data-testid={testid}
    >
      <div
        className="seg-thumb"
        style={{ transform: `translateX(${idx * 100}%)` }}
      />
      {options.map((opt) => (
        <button
          key={String(opt)}
          type="button"
          aria-pressed={value === opt}
          data-testid={testid ? `${testid}-${opt}` : undefined}
          data-active={value === opt}
          onClick={() => onChange(opt)}
          className={cn("seg-item capitalize", value === opt && "is-active")}
        >
          {getLabel ? getLabel(opt) : String(opt)}
        </button>
      ))}
    </div>
  );
}
