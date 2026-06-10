"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { RotateCcw, Trophy } from "lucide-react";
import { useQuizStore } from "@/store/quiz";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { QuestionView } from "@/components/quiz/question-view";
import { ExplanationPanel } from "@/components/quiz/explanation-panel";
import { cn } from "@/lib/utils";

export default function ResultsPage() {
  const router = useRouter();
  const result = useQuizStore((s) => s.result);
  const reset = useQuizStore((s) => s.reset);

  useEffect(() => {
    if (!result) router.replace("/");
  }, [result, router]);

  if (!result) return null;

  const pct = result.total > 0 ? Math.round((result.score / result.total) * 100) : 0;

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 p-5 pb-28">
      {/* Score */}
      <section
        data-testid="score"
        className="flex flex-col items-center gap-2 rounded-2xl border bg-card p-8 text-center"
      >
        <Trophy
          className={cn(
            "size-10",
            pct >= 60 ? "text-amber-400" : "text-muted-foreground",
          )}
        />
        <p className="text-4xl font-bold tabular-nums" data-testid="score-value">
          {result.score} / {result.total}
        </p>
        <p className="text-muted-foreground">{pct}% correct</p>
      </section>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Review</h2>
        <span className="text-sm text-muted-foreground">
          {result.questions.length} questions
        </span>
      </div>

      {/* Per-question review */}
      <div className="flex flex-col gap-5">
        {result.questions.map((q, i) => (
          <div key={q.id} className="flex flex-col gap-3" data-testid="review-item">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <span
                className={cn(
                  "flex size-6 items-center justify-center rounded-full text-xs font-bold",
                  q.isCorrect
                    ? "bg-emerald-500/15 text-emerald-500"
                    : "bg-destructive/15 text-destructive",
                )}
              >
                {i + 1}
              </span>
              Question {i + 1}
            </div>
            <QuestionView
              question={q}
              selectedIndex={q.selectedIndex}
              revealed
              locked
              onSelect={() => {}}
            />
            <ExplanationPanel question={q} selectedIndex={q.selectedIndex} />
            {i < result.questions.length - 1 ? <Separator className="mt-2" /> : null}
          </div>
        ))}
      </div>

      <div className="fixed inset-x-0 bottom-0 mx-auto max-w-md p-5">
        <Button
          data-testid="new-quiz"
          size="lg"
          className="h-14 w-full text-base"
          onClick={() => {
            reset();
            router.push("/");
          }}
        >
          <RotateCcw className="size-5" /> New quiz
        </Button>
      </div>
    </main>
  );
}
