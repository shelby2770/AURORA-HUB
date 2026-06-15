"use client";

import { useEffect, useRef } from "react";
import { Check, X } from "lucide-react";
import type { QuestionOut } from "@/lib/api";
import { cn } from "@/lib/utils";

type TabStatus = "correct" | "incorrect" | "answered" | "unanswered";

function statusFor(
  answer: number | null,
  correctIndex: number | null | undefined,
  isPractice: boolean,
): TabStatus {
  if (answer == null) return "unanswered";
  // Practice mode reveals answers instantly → show right/wrong.
  if (isPractice && correctIndex != null) {
    return answer === correctIndex ? "correct" : "incorrect";
  }
  return "answered";
}

export function QuestionNavigator({
  questions,
  answers,
  currentIndex,
  isPractice,
  onJump,
}: {
  questions: QuestionOut[];
  answers: (number | null)[];
  currentIndex: number;
  isPractice: boolean;
  onJump: (index: number) => void;
}) {
  const trackRef = useRef<HTMLElement>(null);

  // Keep the active question's bubble visible as the user navigates the
  // horizontally-scrolling strip (otherwise tabs past the viewport edge
  // look like they're missing).
  useEffect(() => {
    const track = trackRef.current;
    const active = track?.querySelector<HTMLButtonElement>('[data-current="true"]');
    active?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  }, [currentIndex]);

  return (
    <nav
      ref={trackRef}
      aria-label="Question navigator"
      data-testid="question-navigator"
      className="pager-track -mx-1 px-1"
    >
      {questions.map((q, i) => {
        const status = statusFor(answers[i], q.correctIndex, isPractice);
        const isCurrent = i === currentIndex;
        return (
          <button
            key={q.id}
            type="button"
            data-testid="nav-tab"
            data-status={status}
            data-current={isCurrent ? "true" : undefined}
            aria-label={`Question ${i + 1}, ${status}${isCurrent ? ", current" : ""}`}
            aria-current={isCurrent ? "true" : undefined}
            onClick={() => onJump(i)}
            className={cn(
              "bubble",
              status === "correct" && "is-correct",
              status === "incorrect" && "is-incorrect",
              status === "answered" && "is-answered",
              isCurrent && "is-current",
            )}
          >
            {status === "correct" ? (
              <Check className="size-3.5" />
            ) : status === "incorrect" ? (
              <X className="size-3.5" />
            ) : (
              i + 1
            )}
          </button>
        );
      })}
    </nav>
  );
}
