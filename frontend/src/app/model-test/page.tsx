"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  ClipboardList,
  Clock,
  Loader2,
  RotateCcw,
  Trophy,
} from "lucide-react";
import { toast } from "sonner";
import {
  getModelTests,
  startModelTest,
  API_BASE_URL,
  type ModelTestSummary,
} from "@/lib/api";
import { useModelTestStore } from "@/store/model-test";
import { Button } from "@/components/ui/button";
import { LogoLockup } from "@/components/brand/logo";
import { Skeleton } from "@/components/ui/skeleton";

export default function ModelTestListPage() {
  const router = useRouter();
  const initSession = useModelTestStore((s) => s.initSession);
  const [startingSlug, setStartingSlug] = useState<string | null>(null);

  const tests = useQuery({ queryKey: ["model-tests"], queryFn: getModelTests });

  async function handleStart(slug: string) {
    if (startingSlug) return;
    setStartingSlug(slug);
    try {
      const res = await startModelTest(slug);
      initSession(res);
      router.push("/model-test/run/");
    } catch {
      toast.error("Could not start the model test. Server error.", {
        id: "mt-start-error",
      });
      setStartingSlug(null);
    }
  }

  return (
    <Shell>
      <div className="mt-intro">
        <h1 className="mt-title">Model Tests</h1>
        <p className="mt-subtitle">
          Full-length mock exams · 50 questions · 150 marks · 90 minutes · pass
          mark 60 (40%).
        </p>
      </div>

      {tests.isError ? (
        <div
          data-testid="model-tests-error"
          role="alert"
          className="flex flex-col items-center gap-4 rounded-2xl border bg-card p-8 text-center"
        >
          <AlertTriangle className="size-10 text-destructive" />
          <div className="flex flex-col gap-1">
            <p className="font-semibold">Couldn&apos;t reach the server</p>
            <p className="text-sm text-muted-foreground">
              Make sure the backend is running at {API_BASE_URL}.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => tests.refetch()}
            disabled={tests.isFetching}
          >
            {tests.isFetching ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RotateCcw className="size-4" />
            )}
            Try again
          </Button>
        </div>
      ) : tests.isLoading ? (
        <div className="flex flex-col gap-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
      ) : (tests.data?.length ?? 0) === 0 ? (
        <div
          data-testid="model-tests-empty"
          className="flex flex-col items-center gap-3 rounded-2xl border bg-card p-8 text-center"
        >
          <ClipboardList className="size-10 text-muted-foreground" />
          <p className="font-semibold">No model tests yet</p>
          <p className="text-sm text-muted-foreground">
            Seed them with{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
              python -m app.scripts.seed_model_tests
            </code>
            , then reload.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {tests.data!.map((t) => (
            <ModelTestCard
              key={t.slug}
              test={t}
              starting={startingSlug === t.slug}
              disabled={startingSlug != null}
              onStart={() => handleStart(t.slug)}
            />
          ))}
        </div>
      )}
    </Shell>
  );
}

function ModelTestCard({
  test,
  starting,
  disabled,
  onStart,
}: {
  test: ModelTestSummary;
  starting: boolean;
  disabled: boolean;
  onStart: () => void;
}) {
  return (
    <button
      type="button"
      data-testid="model-test-card"
      onClick={onStart}
      disabled={disabled}
      className="mt-card"
    >
      <div className="mt-card-body">
        <span className="mt-card-icon">
          <Trophy className="size-5" />
        </span>
        <div className="mt-card-text">
          <div className="mt-card-name">{test.title}</div>
          <div className="mt-card-meta">
            <span>{test.totalQuestions} questions</span>
            <span>· {test.fullMarks} marks</span>
            <span className="inline-flex items-center gap-1">
              · <Clock className="size-3.5" /> {test.timeMinutes} min
            </span>
          </div>
        </div>
      </div>
      <span className="mt-card-cta">
        {starting ? (
          <Loader2 className="size-5 animate-spin" />
        ) : (
          <ArrowRight className="size-5" />
        )}
      </span>
    </button>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  return (
    <main className="app flex min-h-dvh flex-col">
      <div className="aurora-bg" />
      <div className="app-inner mx-auto flex w-full max-w-md flex-1 flex-col">
        <header className="brand safe-top [--safe-pad-top:0.5rem] flex items-center gap-3 px-5 pt-2 pb-4">
          <button
            type="button"
            aria-label="Back to home"
            data-testid="model-test-back"
            onClick={() => router.push("/")}
            className="icon-btn"
          >
            <ArrowLeft className="size-5" />
          </button>
          <LogoLockup />
        </header>
        <div className="flex flex-1 flex-col gap-6 px-5 pt-1 pb-32">
          {children}
        </div>
      </div>
    </main>
  );
}
