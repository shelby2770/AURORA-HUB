"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Flag, Timer, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { submitModelTest } from "@/lib/api";
import { useModelTestStore } from "@/store/model-test";
import { toDisplayQuestion } from "@/lib/model-test";
import { useExamTimer, formatTime } from "@/hooks/use-exam-timer";
import { QuestionView } from "@/components/quiz/question-view";
import { QuestionNavigator } from "@/components/quiz/question-navigator";
import { cn } from "@/lib/utils";

export default function ModelTestRunPage() {
  const router = useRouter();
  const {
    sessionId,
    questions,
    answers,
    currentIndex,
    durationSeconds,
    startedAtMs,
    selectAnswer,
    goNext,
    goPrev,
    goTo,
    setResult,
  } = useModelTestStore();

  const submittedRef = useRef(false);

  const submit = useMutation({
    mutationFn: () => submitModelTest(sessionId!, answers),
    onSuccess: (res) => {
      setResult(res);
      router.replace("/model-test/result/");
    },
    onError: () => {
      submittedRef.current = false;
      toast.error("Could not submit the test. Check your connection.");
    },
  });

  const finish = useCallback(() => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    submit.mutate();
  }, [submit]);

  const remaining = useExamTimer(startedAtMs, durationSeconds, finish);

  // Adapt the model-test questions to the shared display shape once.
  const display = useMemo(() => questions.map(toDisplayQuestion), [questions]);

  // No active session (e.g. direct load / refresh) → back to the list.
  useEffect(() => {
    if (!sessionId) router.replace("/model-test/");
  }, [sessionId, router]);

  if (!sessionId || questions.length === 0) return null;

  const question = display[currentIndex];
  const selected = answers[currentIndex];
  const isLast = currentIndex === questions.length - 1;
  const answeredCount = answers.filter((a) => a != null).length;

  return (
    <main className="app flex min-h-dvh flex-col">
      <div className="aurora-bg" />
      <div className="app-inner mx-auto flex w-full max-w-md flex-1 flex-col">
        <header className="safe-top [--safe-pad-top:1rem] sticky top-0 z-10 flex flex-col gap-3.5 bg-[#07070a]/85 px-4 pb-3 backdrop-blur-md">
          <div className="qbar">
            <button
              type="button"
              data-testid="exit-model-test"
              onClick={() => router.replace("/model-test/")}
              className="icon-btn"
              aria-label="Exit model test"
            >
              <X className="size-5" />
            </button>
            <div className="qbar-title" data-testid="progress-label">
              Question {currentIndex + 1} <span>/ {questions.length}</span>
            </div>
            {remaining != null ? (
              <span
                data-testid="timer"
                role="timer"
                aria-label={`Time remaining: ${formatTime(remaining)}`}
                className={cn("timer", remaining <= 30 && "is-low")}
              >
                <Timer className="size-3.5" aria-hidden />
                {formatTime(remaining)}
              </span>
            ) : (
              <span className="w-10" />
            )}
          </div>
          <div className="progress-rail">
            <div
              className="progress-fill"
              style={{
                width: `${((currentIndex + 1) / questions.length) * 100}%`,
              }}
            />
          </div>
          <QuestionNavigator
            questions={display}
            answers={answers}
            currentIndex={currentIndex}
            isPractice={false}
            onJump={goTo}
          />
        </header>

        <section className="flex-1 overflow-y-auto px-5 py-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={question.id}
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -24 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col gap-4"
            >
              <span className="mt-subject-chip">
                {questions[currentIndex].subject}
              </span>
              <QuestionView
                question={question}
                selectedIndex={selected}
                revealed={false}
                locked={false}
                onSelect={selectAnswer}
              />
            </motion.div>
          </AnimatePresence>
        </section>

        <footer className="dock dock-split safe-bottom [--safe-pad-bottom:1.25rem] sticky bottom-0 px-5 pt-3.5">
          <button
            type="button"
            className="btn-ghost"
            onClick={goPrev}
            disabled={currentIndex === 0}
            data-testid="prev"
          >
            <ChevronLeft className="size-4.5" /> Previous
          </button>

          {isLast ? (
            <button
              type="button"
              className="btn-finish"
              onClick={finish}
              disabled={submit.isPending}
              data-testid="finish"
              aria-label={`Finish · ${answeredCount} of ${questions.length} answered`}
            >
              {submit.isPending ? (
                <Loader2 className="size-5 animate-spin" />
              ) : (
                <>
                  <Flag className="size-4.25" /> Finish
                </>
              )}
            </button>
          ) : (
            <button
              type="button"
              className="btn-next"
              onClick={goNext}
              data-testid="next"
            >
              Next <ChevronRight className="size-4.5" />
            </button>
          )}
        </footer>
      </div>
    </main>
  );
}
