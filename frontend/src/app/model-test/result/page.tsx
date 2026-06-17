"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Check, ClipboardList, Home, List, X } from "lucide-react";
import { useModelTestStore } from "@/store/model-test";
import { toDisplayQuestion } from "@/lib/model-test";
import { QuestionView } from "@/components/quiz/question-view";
import { ExplanationPanel } from "@/components/quiz/explanation-panel";
import { ScoreRing } from "@/components/quiz/score-ring";
import { cn } from "@/lib/utils";

export default function ModelTestResultPage() {
  const router = useRouter();
  const result = useModelTestStore((s) => s.result);
  const title = useModelTestStore((s) => s.title);
  const reset = useModelTestStore((s) => s.reset);

  useEffect(() => {
    if (!result) router.replace("/model-test/");
  }, [result, router]);

  if (!result) return null;

  const wrong = result.total - result.score;
  const pct =
    result.fullMarks > 0
      ? Math.round((result.marks / result.fullMarks) * 100)
      : 0;

  const leave = () => {
    reset();
    router.push("/model-test/");
  };

  return (
    <main className="app flex min-h-dvh flex-col">
      <div className="aurora-bg" />
      <div className="app-inner mx-auto flex w-full max-w-md flex-1 flex-col">
        <div className="safe-top [--safe-pad-top:1.25rem] flex flex-1 flex-col gap-6 px-5 pt-2 pb-32">
          {/* Score */}
          <section className="score-card" data-testid="model-test-score">
            <div
              className={cn(
                "mt-verdict",
                result.passed ? "is-pass" : "is-fail",
              )}
              data-testid="verdict"
            >
              {result.passed ? "Passed" : "Not passed"}
            </div>
            <ScoreRing pct={pct} />
            <div className="score-line" data-testid="marks-value">
              {result.marks} / {result.fullMarks} marks
            </div>
            <div className="score-stats">
              <div className="stat">
                <span className="stat-dot ok" /> {result.score} right
              </div>
              <div className="stat">
                <span className="stat-dot bad" /> {wrong} wrong
              </div>
              <div className="stat">
                pass mark {result.passMarks}
              </div>
            </div>
            {title ? <div className="mt-result-title">{title}</div> : null}
          </section>

          {/* Subject-wise breakdown */}
          <section className="flex flex-col gap-2">
            <div className="review-head">
              <h3>
                <ClipboardList className="size-4.25" /> By subject
              </h3>
            </div>
            <div className="flex flex-col gap-2">
              {result.subjectBreakdown.map((s) => {
                const ratio = s.total > 0 ? (s.correct / s.total) * 100 : 0;
                return (
                  <div
                    key={s.subject}
                    className="subject-row"
                    data-testid="subject-row"
                  >
                    <span className="subject-name">{s.subject}</span>
                    <span className="subject-bar">
                      <span
                        className="subject-bar-fill"
                        style={{ width: `${ratio}%` }}
                      />
                    </span>
                    <span className="subject-score">
                      {s.correct}/{s.total}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Per-question review */}
          <div className="review-head">
            <h3>
              <List className="size-4.25" /> Review
            </h3>
            <span>{result.questions.length} questions</span>
          </div>

          <div className="flex flex-col gap-3">
            {result.questions.map((q, i) => (
              <div
                key={q.number}
                className="review-item"
                data-testid="review-item"
              >
                <div className="review-top">
                  <span
                    className={cn("review-num", q.isCorrect ? "ok" : "bad")}
                  >
                    {q.isCorrect ? (
                      <Check className="size-3.5" />
                    ) : (
                      <X className="size-3.5" />
                    )}
                  </span>
                  <span className="review-q">
                    Question {i + 1} · {q.subject}
                  </span>
                </div>
                <QuestionView
                  question={toDisplayQuestion(q)}
                  selectedIndex={q.selectedIndex}
                  revealed
                  locked
                  onSelect={() => {}}
                />
                <ExplanationPanel
                  question={toDisplayQuestion(q)}
                  selectedIndex={q.selectedIndex}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="dock dock-split safe-bottom [--safe-pad-bottom:1.875rem] sticky bottom-0 px-5 pt-3.5">
          <button
            type="button"
            data-testid="back-home"
            className="btn-ghost wide"
            onClick={() => {
              reset();
              router.push("/");
            }}
          >
            <Home className="size-4.25" /> Home
          </button>
          <button
            type="button"
            className="btn-next"
            onClick={leave}
            data-testid="more-tests"
          >
            <ClipboardList className="size-4" /> More tests
          </button>
        </div>
      </div>
    </main>
  );
}
