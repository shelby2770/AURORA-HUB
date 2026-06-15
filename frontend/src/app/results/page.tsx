"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, List, RotateCcw, Share2, Trophy, X } from "lucide-react";
import { toast } from "sonner";
import { useQuizStore } from "@/store/quiz";
import { shareResults } from "@/lib/export-results";
import { QuestionView } from "@/components/quiz/question-view";
import { ExplanationPanel } from "@/components/quiz/explanation-panel";
import { ScoreRing } from "@/components/quiz/score-ring";
import { cn } from "@/lib/utils";

export default function ResultsPage() {
  const router = useRouter();
  const result = useQuizStore((s) => s.result);
  const reset = useQuizStore((s) => s.reset);
  const [sharing, setSharing] = useState(false);

  useEffect(() => {
    if (!result) router.replace("/");
  }, [result, router]);

  if (!result) return null;

  const onShare = async () => {
    if (sharing) return;
    setSharing(true);
    try {
      await shareResults(result);
    } catch (err) {
      // A user dismissing the native share sheet rejects — don't nag them.
      const msg = err instanceof Error ? err.message : "";
      if (!/cancel|abort|dismiss/i.test(msg)) {
        toast.error("Could not export results.");
      }
    } finally {
      setSharing(false);
    }
  };

  const wrong = result.total - result.score;
  const pct =
    result.total > 0 ? Math.round((result.score / result.total) * 100) : 0;

  let verdict = "Keep practicing";
  if (pct >= 90) verdict = "Outstanding";
  else if (pct >= 70) verdict = "Well done";
  else if (pct >= 50) verdict = "Good effort";

  return (
    <main className="app flex min-h-dvh flex-col">
      <div className="aurora-bg" />
      <div className="app-inner mx-auto flex w-full max-w-md flex-1 flex-col">
        <div className="safe-top [--safe-pad-top:1.25rem] flex flex-1 flex-col gap-6 px-5 pt-2 pb-32">
          {/* Score */}
          <section className="score-card" data-testid="score">
            <div className="score-badge">
              <Trophy className="size-4.5" /> {verdict}
            </div>
            <ScoreRing pct={pct} />
            <div className="score-line" data-testid="score-value">
              {result.score} / {result.total}
            </div>
            <div className="score-stats">
              <div className="stat">
                <span className="stat-dot ok" /> {result.score} right
              </div>
              <div className="stat">
                <span className="stat-dot bad" /> {wrong} wrong
              </div>
            </div>
          </section>

          <div className="review-head">
            <h3>
              <List className="size-4.25" /> Review
            </h3>
            <span>{result.questions.length} questions</span>
          </div>

          {/* Per-question review */}
          <div className="flex flex-col gap-3">
            {result.questions.map((q, i) => (
              <div key={q.id} className="review-item" data-testid="review-item">
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
                  <span className="review-q">Question {i + 1}</span>
                </div>
                <QuestionView
                  question={q}
                  selectedIndex={q.selectedIndex}
                  revealed
                  locked
                  onSelect={() => {}}
                />
                <ExplanationPanel question={q} selectedIndex={q.selectedIndex} />
              </div>
            ))}
          </div>
        </div>

        <div className="dock dock-split safe-bottom [--safe-pad-bottom:1.875rem] sticky bottom-0 px-5 pt-3.5">
          <button
            type="button"
            data-testid="new-quiz"
            className="btn-ghost wide"
            onClick={() => {
              reset();
              router.push("/");
            }}
          >
            <RotateCcw className="size-4.25" /> New quiz
          </button>
          <button
            type="button"
            className="btn-next"
            onClick={onShare}
            disabled={sharing}
            data-testid="share-results"
          >
            <Share2 className="size-4" /> Share
          </button>
        </div>
      </div>
    </main>
  );
}
