"use client";

import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { MathText } from "./math-text";

export type OptionState =
  | "default"
  | "selected"
  | "correct"
  | "incorrect"
  | "muted";

const LETTERS = ["A", "B", "C", "D"];

export function computeOptionState(
  index: number,
  selectedIndex: number | null,
  correctIndex: number | null | undefined,
  revealed: boolean,
): OptionState {
  if (revealed && correctIndex != null) {
    if (index === correctIndex) return "correct";
    if (index === selectedIndex) return "incorrect";
    return "muted";
  }
  return index === selectedIndex ? "selected" : "default";
}

const STATE_HINT: Record<OptionState, string> = {
  default: "",
  selected: ", selected",
  correct: ", correct answer",
  incorrect: ", your answer, incorrect",
  muted: "",
};

export function OptionButton({
  index,
  text,
  state,
  checked,
  disabled,
  onSelect,
}: {
  index: number;
  text: string;
  state: OptionState;
  checked?: boolean;
  disabled?: boolean;
  onSelect?: () => void;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={!!checked}
      aria-label={`Option ${LETTERS[index]}: ${text}${STATE_HINT[state]}`}
      data-testid="option"
      data-state={state}
      disabled={disabled}
      // pointerdown-friendly via onClick; tap feedback through active: styles
      onClick={onSelect}
      className={cn(
        "flex w-full items-center gap-3 rounded-xl border-2 p-4 text-left transition-colors",
        "min-h-14 active:scale-[0.99]",
        "disabled:cursor-default",
        state === "default" && "border-border bg-card hover:border-primary/40",
        state === "selected" && "border-primary bg-primary/10",
        state === "correct" && "border-emerald-500 bg-emerald-500/10",
        state === "incorrect" && "border-destructive bg-destructive/10",
        state === "muted" && "border-border bg-card opacity-60",
      )}
    >
      <span
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold",
          state === "selected" && "border-primary text-primary",
          state === "correct" && "border-emerald-500 text-emerald-500",
          state === "incorrect" && "border-destructive text-destructive",
        )}
      >
        {state === "correct" ? (
          <Check className="size-4" />
        ) : state === "incorrect" ? (
          <X className="size-4" />
        ) : (
          LETTERS[index]
        )}
      </span>
      <span className="flex-1 text-base leading-snug">
        <MathText>{text}</MathText>
      </span>
    </button>
  );
}
