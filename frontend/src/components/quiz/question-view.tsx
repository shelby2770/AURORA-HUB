"use client";

import { BlockMath } from "react-katex";
import type { DisplayQuestion } from "@/lib/api";
import { cn } from "@/lib/utils";
import { MathText } from "./math-text";
import { CodeBlock } from "./code-block";
import { OptionButton, computeOptionState } from "./option-button";

export function QuestionView({
  question,
  selectedIndex,
  revealed,
  locked,
  onSelect,
}: {
  question: DisplayQuestion;
  selectedIndex: number | null;
  revealed: boolean;
  locked: boolean;
  onSelect: (index: number) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      {/* Bank questions carry a difficulty; model-test questions don't, so the
          chip is shown only when one is present. */}
      {question.difficulty ? (
        <span className={cn("diff-chip w-fit", `diff-${question.difficulty}`)}>
          {question.difficulty}
        </span>
      ) : null}

      <h2 className="qtext">
        <MathText>{question.questionText}</MathText>
      </h2>

      {question.latex ? (
        <div className="overflow-x-auto rounded-md border bg-card p-3">
          <BlockMath math={question.latex} />
        </div>
      ) : null}

      {question.codeSnippet ? (
        <CodeBlock
          code={question.codeSnippet}
          lang={question.codeLang ?? undefined}
        />
      ) : null}

      <div
        className="flex flex-col gap-3"
        data-testid="options"
        role="radiogroup"
        aria-label="Answer options"
      >
        {question.options.map((opt, i) => (
          <OptionButton
            key={i}
            index={i}
            text={opt}
            checked={i === selectedIndex}
            state={computeOptionState(
              i,
              selectedIndex,
              question.correctIndex,
              revealed,
            )}
            disabled={locked}
            onSelect={() => onSelect(i)}
          />
        ))}
      </div>
    </div>
  );
}
