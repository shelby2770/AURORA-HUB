"use client";

import { CheckCircle2, XCircle, Lightbulb } from "lucide-react";
import type { QuestionOut } from "@/lib/api";
import { cn } from "@/lib/utils";
import { MathText } from "./math-text";

const LETTERS = ["A", "B", "C", "D", "E", "F"];

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
      className={cn("feedback", correct ? "ok" : "bad")}
    >
      <div className="feedback-head">
        {correct ? (
          <>
            <CheckCircle2 className="size-4" /> Correct
          </>
        ) : (
          <>
            <XCircle className="size-4" />
            {selectedIndex == null ? "Not answered" : "Incorrect"}
          </>
        )}
      </div>

      {question.explanation ? (
        <p className="feedback-body flex gap-2 leading-relaxed">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-amber-400" />
          <span>
            <MathText>{question.explanation}</MathText>
          </span>
        </p>
      ) : null}

      {question.distractorRationales &&
      question.distractorRationales.length > 0 ? (
        <ul className="feedback-rationales">
          {question.distractorRationales.map((r, i) =>
            r && i !== question.correctIndex ? (
              <li key={i} className="flex gap-2">
                <span className="font-mono text-xs">{LETTERS[i]}</span>
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
