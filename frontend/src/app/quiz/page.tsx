"use client";

import { useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Flag,
  Timer,
  X,
  Zap,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { submitQuiz } from "@/lib/api";
import { useQuizStore } from "@/store/quiz";
import { useExamTimer, formatTime } from "@/hooks/use-exam-timer";
import { QuestionView } from "@/components/quiz/question-view";
import { QuestionNavigator } from "@/components/quiz/question-navigator";
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
    goTo,
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
    <main className="app flex min-h-dvh flex-col">
      <div className="aurora-bg" />
      <div className="app-inner mx-auto flex w-full max-w-md flex-1 flex-col">
        {/* Top bar */}
        <header className="safe-top [--safe-pad-top:1rem] sticky top-0 z-10 flex flex-col gap-3.5 bg-[#07070a]/85 px-4 pb-3 backdrop-blur-md">
          <div className="qbar">
            <button
              type="button"
              data-testid="exit-quiz"
              onClick={() => router.replace("/")}
              className="icon-btn"
              aria-label="Exit quiz"
            >
              <X className="size-5" />
            </button>
            <div className="qbar-title" data-testid="progress-label">
              Question {currentIndex + 1} <span>/ {questions.length}</span>
            </div>
            {isPractice ? (
              <span className="mode-pill">
                <Zap className="size-3.5" /> Practice
              </span>
            ) : remaining != null ? (
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
            questions={questions}
            answers={answers}
            currentIndex={currentIndex}
            isPractice={isPractice}
            onJump={goTo}
          />
        </header>

        {/* Question */}
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
