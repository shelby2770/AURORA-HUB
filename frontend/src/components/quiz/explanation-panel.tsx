"use client";

import { CheckCircle2, XCircle, Lightbulb } from "lucide-react";
import type { QuestionOut } from "@/lib/api";
import { cn } from "@/lib/utils";
import { MathText } from "./math-text";

export function ExplanationPanel({
  question,
  selectedIndex,
}: {
  question: QuestionOut;
  selectedIndex: number | null;
}) {
  const correct =
    selectedIndex != null && selectedIndex === question.correctIndex;

  return (
    <div
      data-testid="explanation"
      className={cn(
        "flex flex-col gap-3 rounded-xl border p-4 text-sm",
        correct
          ? "border-emerald-500/40 bg-emerald-500/5"
          : "border-destructive/40 bg-destructive/5",
      )}
    >
      <div className="flex items-center gap-2 font-semibold">
        {correct ? (
          <>
            <CheckCircle2 className="size-4 text-emerald-500" /> Correct
          </>
        ) : (
          <>
            <XCircle className="size-4 text-destructive" />
            {selectedIndex == null ? "Not answered" : "Incorrect"}
          </>
        )}
      </div>

      {question.explanation ? (
        <p className="flex gap-2 leading-relaxed text-foreground/90">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-amber-400" />
          <span>
            <MathText>{question.explanation}</MathText>
          </span>
        </p>
      ) : null}

      {question.distractorRationales &&
      question.distractorRationales.length > 0 ? (
        <ul className="flex flex-col gap-1 text-muted-foreground">
          {question.distractorRationales.map((r, i) =>
            r && i !== question.correctIndex ? (
              <li key={i} className="flex gap-2">
                <span className="font-mono text-xs">
                  {["A", "B", "C", "D"][i]}
                </span>
                <span>
                  <MathText>{r}</MathText>
                </span>
              </li>
            ) : null,
          )}
        </ul>
      ) : null}
    </div>
  );
}
