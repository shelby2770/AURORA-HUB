"use client";

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
  return (
    <nav
      aria-label="Question navigator"
      data-testid="question-navigator"
      className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1"
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
              "flex size-8 shrink-0 items-center justify-center rounded-md border text-xs font-semibold tabular-nums transition-colors",
              status === "correct" &&
                "border-emerald-500 bg-emerald-500 text-white",
              status === "incorrect" &&
                "border-destructive bg-destructive text-white",
              // Exam mode: answered is a solid fill so it clearly stands apart
              // from the hollow unanswered tabs.
              status === "answered" &&
                "border-primary bg-primary text-primary-foreground",
              status === "unanswered" &&
                "border-border bg-card text-muted-foreground hover:border-primary/40",
              // Current tab keeps its underlying answered/unanswered fill and
              // gains a ring so you can always see where you are.
              isCurrent &&
                "ring-2 ring-ring ring-offset-2 ring-offset-background",
            )}
          >
            {i + 1}
          </button>
        );
      })}
    </nav>
  );
}
