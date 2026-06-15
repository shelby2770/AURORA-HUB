"use client";

import { Check, X } from "lucide-react";
import { MathText } from "./math-text";

export type OptionState =
  | "default"
  | "selected"
  | "correct"
  | "incorrect"
  | "muted";

const LETTERS = ["A", "B", "C", "D", "E", "F"];

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
      className="opt"
    >
      <span className="opt-letter">
        {state === "correct" ? (
          <Check className="size-4" />
        ) : state === "incorrect" ? (
          <X className="size-4" />
        ) : (
          LETTERS[index]
        )}
      </span>
      <span className="opt-text">
        <MathText>{text}</MathText>
      </span>
    </button>
  );
}
