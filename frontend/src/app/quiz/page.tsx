"use client";

import { useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Timer, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { submitQuiz } from "@/lib/api";
import { useQuizStore } from "@/store/quiz";
import { useExamTimer, formatTime } from "@/hooks/use-exam-timer";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { QuestionView } from "@/components/quiz/question-view";
import { ExplanationPanel } from "@/components/quiz/explanation-panel";
import { cn } from "@/lib/utils";

export default function QuizPage() {
  const router = useRouter();
  const {
    sessionId,
    mode,
    questions,
    answers,
    currentIndex,
    durationSeconds,
    startedAtMs,
    selectAnswer,
    goNext,
    goPrev,
    setResult,
  } = useQuizStore();

  const submittedRef = useRef(false);

  const submit = useMutation({
    mutationFn: () => submitQuiz(sessionId!, answers),
    onSuccess: (res) => {
      setResult(res);
      router.replace("/results/");
    },
    onError: () => {
      submittedRef.current = false;
      toast.error("Could not submit the quiz. Check your connection.");
    },
  });

  const finish = useCallback(() => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    submit.mutate();
  }, [submit]);

  const remaining = useExamTimer(
    mode === "exam" ? startedAtMs : null,
    mode === "exam" ? durationSeconds : null,
    finish,
  );

  // No active session (e.g. direct load / refresh) → back to config.
  useEffect(() => {
    if (!sessionId) router.replace("/");
  }, [sessionId, router]);

  if (!sessionId || questions.length === 0) return null;

  const question = questions[currentIndex];
  const selected = answers[currentIndex];
  const isPractice = mode === "practice";
  const revealed = isPractice && selected != null;
  const isLast = currentIndex === questions.length - 1;
  const answeredCount = answers.filter((a) => a != null).length;

  const onSelect = (i: number) => {
    if (isPractice && selected != null) return; // locked after first answer
    selectAnswer(i);
  };

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col">
      {/* Top bar */}
      <header className="sticky top-0 z-10 flex flex-col gap-2 border-b bg-background/95 p-4 backdrop-blur">
        <div className="flex items-center justify-between">
          <button
            type="button"
            data-testid="exit-quiz"
            onClick={() => router.replace("/")}
            className="flex size-9 items-center justify-center rounded-full hover:bg-muted"
            aria-label="Exit quiz"
          >
            <X className="size-5" />
          </button>
          <span className="text-sm font-medium" data-testid="progress-label">
            Question {currentIndex + 1} / {questions.length}
          </span>
          {mode === "exam" && remaining != null ? (
            <span
              data-testid="timer"
              role="timer"
              aria-label={`Time remaining: ${formatTime(remaining)}`}
              className={cn(
                "flex items-center gap-1 rounded-full px-2 py-1 text-sm font-semibold tabular-nums",
                remaining <= 30
                  ? "bg-destructive/15 text-destructive"
                  : "text-muted-foreground",
              )}
            >
              <Timer className="size-4" aria-hidden />
              {formatTime(remaining)}
            </span>
          ) : (
            <span className="w-9" />
          )}
        </div>
        <Progress value={((currentIndex + 1) / questions.length) * 100} />
      </header>

      {/* Question */}
      <section className="flex-1 overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={question.id}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col gap-4"
          >
            <QuestionView
              question={question}
              selectedIndex={selected}
              revealed={revealed}
              locked={revealed}
              onSelect={onSelect}
            />
            {revealed ? (
              <ExplanationPanel question={question} selectedIndex={selected} />
            ) : null}
          </motion.div>
        </AnimatePresence>
      </section>

      {/* Navigation */}
      <footer className="sticky bottom-0 flex items-center gap-3 border-t bg-background p-4">
        <Button
          variant="outline"
          size="lg"
          className="h-12"
          onClick={goPrev}
          disabled={currentIndex === 0}
          data-testid="prev"
        >
          <ChevronLeft className="size-5" />
        </Button>

        {isLast ? (
          <Button
            size="lg"
            className="h-12 flex-1"
            onClick={finish}
            disabled={submit.isPending}
            data-testid="finish"
          >
            {submit.isPending ? (
              <Loader2 className="size-5 animate-spin" />
            ) : (
              `Finish · ${answeredCount}/${questions.length} answered`
            )}
          </Button>
        ) : (
          <Button
            size="lg"
            className="h-12 flex-1"
            onClick={goNext}
            data-testid="next"
          >
            Next <ChevronRight className="size-5" />
          </Button>
        )}
      </footer>
    </main>
  );
}
