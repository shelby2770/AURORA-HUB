"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  GraduationCap,
  Loader2,
  RotateCcw,
  Sparkles,
  Timer,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import {
  getCourses,
  getSubtopics,
  startQuiz,
  fillQuiz,
  getJob,
  type RequestDifficulty,
  type QuizMode,
  type JobProgress,
  type JobStatus,
  ApiError,
  API_BASE_URL,
} from "@/lib/api";
import { Progress } from "@/components/ui/progress";
import { useQuizStore } from "@/store/quiz";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Segmented } from "@/components/quiz/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const WHOLE_COURSE = "__whole__";
const COUNTS = [5, 10, 20, 30, 40];
const DIFFICULTIES: RequestDifficulty[] = ["easy", "medium", "hard", "random"];

export default function ConfigPage() {
  const router = useRouter();
  const initSession = useQuizStore((s) => s.initSession);

  const [courseSlug, setCourseSlug] = useState<string | null>(null);
  const [subtopicId, setSubtopicId] = useState<string>(WHOLE_COURSE);
  const [count, setCount] = useState<number>(20);
  const [difficulty, setDifficulty] = useState<RequestDifficulty>("random");
  const [mode, setMode] = useState<QuizMode>("exam");

  const courses = useQuery({ queryKey: ["courses"], queryFn: getCourses });
  const subtopics = useQuery({
    queryKey: ["subtopics", courseSlug],
    queryFn: () => getSubtopics(courseSlug!),
    enabled: !!courseSlug,
  });

  const course = courses.data?.find((c) => c.slug === courseSlug);
  const wholeCourse = subtopicId === WHOLE_COURSE;

  const changeSubtopic = (v: string | null) => {
    setSubtopicId(v ?? WHOLE_COURSE);
  };

  const [starting, setStarting] = useState(false);
  const [gen, setGen] = useState<JobProgress | null>(null);
  // Seconds since generation started — a heartbeat so the wait never looks
  // frozen during a (~40s) batch where the percent can't move.
  const [elapsed, setElapsed] = useState(0);
  // Set when the user cancels generation; stops polling and aborts the start.
  const cancelled = useRef(false);

  useEffect(() => {
    if (!gen) return;
    setElapsed(0);
    const id = window.setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => window.clearInterval(id);
  }, [gen !== null]); // restart the ticker only when generation starts/stops

  // Start a session and navigate. `target` (when set) reports how many were
  // requested, so we can toast if generation came up short. Never throws.
  async function beginQuiz(subId: string | null, target?: number) {
    try {
      const res = await startQuiz({
        courseId: course!.id,
        subtopicId: subId,
        count,
        difficulty,
        mode,
      });
      if (target !== undefined && res.count < target) {
        toast.message(`Starting with ${res.count} of ${target} questions.`);
      }
      initSession(res);
      router.push("/quiz/");
    } catch (err) {
      // One toast id → repeated taps replace rather than stack.
      if (err instanceof ApiError && err.status === 404) {
        toast.error("No questions available yet for this selection.", {
          id: "start-error",
        });
      } else {
        toast.error("Could not start the quiz. Server error.", {
          id: "start-error",
        });
      }
    }
  }

  // Poll a generation job until done/error (or the user cancels → null).
  function pollJob(jobId: string): Promise<JobStatus | null> {
    return new Promise((resolve) => {
      const tick = async () => {
        if (cancelled.current) return resolve(null);
        try {
          const s = await getJob(jobId);
          if (cancelled.current) return resolve(null);
          if (s.progress) setGen(s.progress);
          if (s.status === "done" || s.status === "error") return resolve(s);
        } catch {
          /* transient network blip — keep polling */
        }
        window.setTimeout(tick, 1500);
      };
      void tick();
    });
  }

  // Abandon an in-flight generation and return to the config form. The
  // backend job keeps running, so the questions it makes are cached for later.
  function cancelGeneration() {
    cancelled.current = true;
    setGen(null);
    setStarting(false);
  }

  async function handleStart() {
    if (!course || starting) return;
    cancelled.current = false;
    setStarting(true);
    const subId = wholeCourse ? null : subtopicId;
    try {
      // Whole-course: serve whatever exists, instantly (never generates).
      if (!subId) {
        await beginQuiz(subId);
        return;
      }
      const fill = await fillQuiz({
        courseId: course.id,
        subtopicId: subId,
        count,
        difficulty,
      }).catch(() => null);
      if (!fill) {
        toast.error("Could not start the quiz. Server error.", {
          id: "start-error",
        });
        return;
      }
      if (fill.ready) {
        await beginQuiz(subId);
        return;
      }
      // Short on questions → generate the remainder with a progress bar.
      setGen({
        done: fill.available,
        target: fill.target,
        percent: Math.round((fill.available * 100) / fill.target),
      });
      const job = await pollJob(fill.jobId!);
      if (job === null) return; // user cancelled
      if (job.status === "error" && fill.available === 0) {
        toast.error(
          "Sorry — couldn't generate questions right now. Please try again in a bit.",
          { id: "start-error" },
        );
        return;
      }
      // Start with whatever exists now (available + freshly generated).
      await beginQuiz(subId, fill.target);
    } finally {
      if (!cancelled.current) {
        setStarting(false);
        setGen(null);
      }
    }
  }

  // Backend unreachable → don't show an empty, mysterious form.
  if (courses.isError) {
    return (
      <Shell>
        <div
          data-testid="courses-error"
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
            data-testid="courses-retry"
            onClick={() => courses.refetch()}
            disabled={courses.isFetching}
          >
            {courses.isFetching ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RotateCcw className="size-4" />
            )}
            Try again
          </Button>
        </div>
      </Shell>
    );
  }

  // Loaded but no courses → the database hasn't been seeded yet.
  if (!courses.isLoading && (courses.data?.length ?? 0) === 0) {
    return (
      <Shell>
        <div
          data-testid="courses-empty"
          className="flex flex-col items-center gap-3 rounded-2xl border bg-card p-8 text-center"
        >
          <GraduationCap className="size-10 text-muted-foreground" />
          <p className="font-semibold">No courses yet</p>
          <p className="text-sm text-muted-foreground">
            Seed the database with{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
              python -m app.scripts.seed
            </code>
            , then reload.
          </p>
        </div>
      </Shell>
    );
  }

  // Generating fill questions → dedicated waiting screen with a progress bar.
  if (gen) {
    return (
      <Shell>
        <div
          data-testid="generating"
          className="mt-10 flex flex-col items-center gap-4 rounded-2xl border bg-card p-8 text-center"
        >
          <Sparkles className="size-9 animate-pulse text-primary" />
          <div className="flex flex-col gap-1">
            <p className="font-semibold">Generating questions…</p>
            <p className="text-sm text-muted-foreground">
              Writing fresh questions in small batches and checking each answer.
              This can take a minute on the free tier.
            </p>
          </div>
          <Progress value={gen.percent} className="w-full" />
          <p className="text-sm tabular-nums text-muted-foreground">
            {gen.done} / {gen.target} ({gen.percent}%)
          </p>
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Working on the next batch… {elapsed}s
          </p>
          <Button
            variant="outline"
            data-testid="cancel-generation"
            className="mt-2 w-full"
            onClick={cancelGeneration}
          >
            Cancel
          </Button>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="flex flex-col gap-5 rounded-2xl border bg-card p-5 shadow-sm">
      {/* Course */}
      <section className="flex flex-col gap-2">
        <Label htmlFor="course-select">Course</Label>
        {courses.isLoading ? (
          <Skeleton data-testid="course-skeleton" className="h-12 w-full rounded-md" />
        ) : (
          <Select
            items={courses.data?.map((c) => ({ value: c.slug, label: c.name }))}
            value={courseSlug}
            onValueChange={(v) => {
              setCourseSlug(v);
              setSubtopicId(WHOLE_COURSE);
            }}
          >
            <SelectTrigger id="course-select" data-testid="course-select" className="h-12 w-full">
              <SelectValue placeholder="Choose a course" />
            </SelectTrigger>
            <SelectContent>
              {courses.data?.map((c) => (
                <SelectItem key={c.id} value={c.slug}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </section>

      {/* Subtopic */}
      <section className="flex flex-col gap-2">
        <Label htmlFor="subtopic-select">Subtopic</Label>
        <Select
          items={[
            { value: WHOLE_COURSE, label: "Whole course" },
            ...(subtopics.data?.map((s) => ({ value: s.id, label: s.name })) ??
              []),
          ]}
          value={subtopicId}
          onValueChange={changeSubtopic}
          disabled={!courseSlug || subtopics.isLoading}
        >
          <SelectTrigger id="subtopic-select" data-testid="subtopic-select" className="h-12 w-full">
            <SelectValue
              placeholder={subtopics.isLoading ? "Loading…" : "Whole course"}
            />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={WHOLE_COURSE}>Whole course</SelectItem>
            {subtopics.data?.map((s) => (
              <SelectItem key={s.id} value={s.id}>
                {s.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </section>

      {/* Count */}
      <section className="flex flex-col gap-2">
        <Label>Questions</Label>
        <Segmented
          testid="count"
          options={COUNTS}
          value={count}
          onChange={setCount}
        />
      </section>

      {/* Difficulty */}
      <section className="flex flex-col gap-2">
        <Label>Difficulty</Label>
        <Segmented
          testid="difficulty"
          options={DIFFICULTIES}
          value={difficulty}
          onChange={setDifficulty}
        />
      </section>

      {/* Mode */}
      <section className="flex flex-col gap-2">
        <Label>Mode</Label>
        <div className="grid grid-cols-2 gap-3">
          <ModeCard
            active={mode === "exam"}
            onClick={() => setMode("exam")}
            testid="mode-exam"
            icon={<Timer className="size-5" />}
            title="Exam"
            desc="Timed · answers at the end"
          />
          <ModeCard
            active={mode === "practice"}
            onClick={() => setMode("practice")}
            testid="mode-practice"
            icon={<Zap className="size-5" />}
            title="Practice"
            desc="Instant feedback"
          />
        </div>
      </section>
      </div>

      <div className="hide-on-keyboard safe-bottom [--safe-pad-bottom:1.25rem] fixed inset-x-0 bottom-0 z-20 mx-auto max-w-md border-t border-border/60 bg-background/80 p-5 backdrop-blur-md">
        <Button
          data-testid="start-quiz"
          size="lg"
          className="h-14 w-full text-base"
          disabled={!course || starting}
          onClick={handleStart}
        >
          {starting ? (
            <Loader2 className="size-5 animate-spin" />
          ) : (
            "Start quiz"
          )}
        </Button>
      </div>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col">
      <header className="safe-top [--safe-pad-top:0.5rem] sticky top-0 z-30 flex items-center gap-3 border-b border-border/60 bg-background/75 px-5 py-3 backdrop-blur-md">
        <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
          <GraduationCap className="size-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold leading-tight">Aurora Hub</h1>
          <p className="text-xs text-muted-foreground">Build your quiz</p>
        </div>
      </header>
      <div className="flex flex-1 flex-col gap-6 p-5 pb-28">{children}</div>
    </main>
  );
}

function ModeCard({
  active,
  onClick,
  icon,
  title,
  desc,
  testid,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  desc: string;
  testid: string;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      data-testid={testid}
      data-active={active}
      onClick={onClick}
      className={cn(
        "flex flex-col items-start gap-1 rounded-xl border-2 p-4 text-left transition-colors active:scale-[0.99]",
        active
          ? "border-primary bg-primary/10"
          : "border-border bg-card hover:border-primary/40",
      )}
    >
      <span className={cn(active ? "text-primary" : "text-muted-foreground")}>
        {icon}
      </span>
      <span className="font-semibold">{title}</span>
      <span className="text-xs text-muted-foreground">{desc}</span>
    </button>
  );
}
