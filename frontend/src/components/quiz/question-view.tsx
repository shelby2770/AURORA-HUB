"use client";

import { BlockMath } from "react-katex";
import type { QuestionOut } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
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
  question: QuestionOut;
  selectedIndex: number | null;
  revealed: boolean;
  locked: boolean;
  onSelect: (index: number) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <Badge variant="secondary" className="w-fit capitalize">
        {question.difficulty}
      </Badge>

      <h2 className="text-lg font-medium leading-relaxed">
        <MathText>{question.questionText}</MathText>
      </h2>

      {question.latex ? (
        <div className="overflow-x-auto rounded-md border bg-card p-3">
          <BlockMath math={question.latex} />
        </div>
      ) : null}

      {question.codeSnippet ? <CodeBlock code={question.codeSnippet} /> : null}

      <div className="flex flex-col gap-3" data-testid="options">
        {question.options.map((opt, i) => (
          <OptionButton
            key={i}
            index={i}
            text={opt}
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
