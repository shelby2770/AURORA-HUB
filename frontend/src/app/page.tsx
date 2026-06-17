"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  ClipboardList,
  GraduationCap,
  Loader2,
  RotateCcw,
  Timer,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import {
  getCourses,
  getSubtopics,
  startQuiz,
  fillQuiz,
  type RequestDifficulty,
  type QuizMode,
  ApiError,
  API_BASE_URL,
} from "@/lib/api";
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
import { LogoLockup } from "@/components/brand/logo";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const WHOLE_COURSE = "__whole__";
// 0 is the "All" sentinel: serve every available question in the scope. The
// backend resolves it to the current verified pool size (see /quiz/start).
const ALL_COUNT = 0;
const COUNTS = [5, 10, 20, 30, 40, ALL_COUNT];
const countLabel = (c: number) => (c === ALL_COUNT ? "All" : String(c));
const DIFFICULTIES: RequestDifficulty[] = ["easy", "medium", "hard", "random"];
// Section tabs, in display order. Courses are grouped under these by their
// `category`; any unknown category falls back into "Computer Science".
const SECTION_ORDER = ["Computer Science", "Others"];
const sectionOf = (c: { category?: string }) =>
  SECTION_ORDER.includes(c.category ?? "") ? c.category! : "Computer Science";

export default function ConfigPage() {
  const router = useRouter();
  const initSession = useQuizStore((s) => s.initSession);

  const [section, setSection] = useState<string>("Computer Science");
  const [courseSlug, setCourseSlug] = useState<string | null>(null);
  const [subtopicId, setSubtopicId] = useState<string>(WHOLE_COURSE);
  const [count, setCount] = useState<number>(20);
  const [difficulty, setDifficulty] = useState<RequestDifficulty>("random");
  const [mode, setMode] = useState<QuizMode>("exam");

  const courses = useQuery({ queryKey: ["courses"], queryFn: getCourses });

  // Section tabs that actually have at least one course, in display order.
  const sections = SECTION_ORDER.filter((s) =>
    courses.data?.some((c) => sectionOf(c) === s),
  );
  // Courses shown in the picker for the active section tab.
  const visibleCourses =
    courses.data?.filter((c) => sectionOf(c) === section) ?? [];

  // Switch tab: clear the course/subtopic selection so the picker can't keep a
  // course that belongs to the other section.
  const changeSection = (s: string) => {
    if (s === section) return;
    setSection(s);
    setCourseSlug(null);
    setSubtopicId(WHOLE_COURSE);
  };
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

  // ── DISABLED: on-demand fill generation ──────────────────────────────────
  // We currently serve only precomputed questions; if a subtopic is short we
  // block and ask the user to pick a smaller amount (see handleStart). The
  // generate-the-remainder flow below is kept (commented out) FOR FURTHER
  // IMPROVEMENT — re-enable it to fill gaps live via the LLM pipeline. To turn
  // it back on, restore the `gen`/`elapsed`/`cancelled` state, the imports it
  // needs (`useEffect`, `useRef`, `getJob`, `JobProgress`, `JobStatus`,
  // `Sparkles`, `Progress`), and the generating screen further down, and have
  // handleStart poll instead of toasting when `!fill.ready`.
  //
  // const [gen, setGen] = useState<JobProgress | null>(null);
  // // Seconds since generation started — a heartbeat so the wait never looks
  // // frozen during a (~40s) batch where the percent can't move.
  // const [elapsed, setElapsed] = useState(0);
  // // Set when the user cancels generation; stops polling and aborts the start.
  // const cancelled = useRef(false);
  //
  // useEffect(() => {
  //   if (!gen) return;
  //   setElapsed(0);
  //   const id = window.setInterval(() => setElapsed((s) => s + 1), 1000);
  //   return () => window.clearInterval(id);
  // }, [gen !== null]); // restart the ticker only when generation starts/stops
  //
  // // Poll a generation job until done/error (or the user cancels → null).
  // function pollJob(jobId: string): Promise<JobStatus | null> {
  //   return new Promise((resolve) => {
  //     const tick = async () => {
  //       if (cancelled.current) return resolve(null);
  //       try {
  //         const s = await getJob(jobId);
  //         if (cancelled.current) return resolve(null);
  //         if (s.progress) setGen(s.progress);
  //         if (s.status === "done" || s.status === "error") return resolve(s);
  //       } catch {
  //         /* transient network blip — keep polling */
  //       }
  //       window.setTimeout(tick, 1500);
  //     };
  //     void tick();
  //   });
  // }
  //
  // // Abandon an in-flight generation and return to the config form. The
  // // backend job keeps running, so the questions it makes are cached for later.
  // function cancelGeneration() {
  //   cancelled.current = true;
  //   setGen(null);
  //   setStarting(false);
  // }
  // ─────────────────────────────────────────────────────────────────────────

  // Start a session and navigate. Never throws.
  async function beginQuiz(subId: string | null) {
    try {
      const res = await startQuiz({
        courseId: course!.id,
        subtopicId: subId,
        count,
        difficulty,
        mode,
      });
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

  async function handleStart() {
    if (!course || starting) return;
    setStarting(true);
    const subId = wholeCourse ? null : subtopicId;
    try {
      // For a subtopic with a fixed count, check the verified pool first. If it
      // can't satisfy the requested count, block and ask the user to pick a
      // smaller amount rather than silently starting short. "All" (and whole-
      // course) skips this check — it serves whatever exists by design.
      if (subId && count !== ALL_COUNT) {
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
        if (!fill.ready) {
          // FOR FURTHER IMPROVEMENT: instead of blocking here we could kick off
          // on-demand generation (poll fill.jobId via the disabled pollJob/gen
          // flow above) to fill the remainder. For now we keep it precomputed-
          // only and ask the user to pick a smaller amount.
          toast.error(
            fill.available > 0
              ? `Only ${fill.available} question${fill.available === 1 ? "" : "s"} available for this subtopic right now — please select a smaller amount.`
              : "No questions available yet for this subtopic.",
            { id: "start-error" },
          );
          return;
        }
      }
      await beginQuiz(subId);
    } finally {
      setStarting(false);
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

  // ── DISABLED: generating-fill waiting screen ─────────────────────────────
  // Shown while on-demand generation runs (progress bar + heartbeat + cancel).
  // Kept FOR FURTHER IMPROVEMENT — re-enable together with the generation
  // helpers/state above and the `Sparkles`/`Progress` imports.
  //
  // if (gen) {
  //   return (
  //     <Shell>
  //       <div
  //         data-testid="generating"
  //         className="mt-10 flex flex-col items-center gap-4 rounded-2xl border bg-card p-8 text-center"
  //       >
  //         <Sparkles className="size-9 animate-pulse text-primary" />
  //         <div className="flex flex-col gap-1">
  //           <p className="font-semibold">Generating questions…</p>
  //           <p className="text-sm text-muted-foreground">
  //             Writing fresh questions in small batches and checking each answer.
  //             This can take a minute on the free tier.
  //           </p>
  //         </div>
  //         <Progress value={gen.percent} className="w-full" />
  //         <p className="text-sm tabular-nums text-muted-foreground">
  //           {gen.done} / {gen.target} ({gen.percent}%)
  //         </p>
  //         <p className="flex items-center gap-2 text-sm text-muted-foreground">
  //           <Loader2 className="size-4 animate-spin" />
  //           Working on the next batch… {elapsed}s
  //         </p>
  //         <Button
  //           variant="outline"
  //           data-testid="cancel-generation"
  //           className="mt-2 w-full"
  //           onClick={cancelGeneration}
  //         >
  //           Cancel
  //         </Button>
  //       </div>
  //     </Shell>
  //   );
  // }
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <Shell>
      {/* Entry point to the full-length model tests (separate from practice). */}
      <button
        type="button"
        data-testid="model-test-entry"
        className="mt-entry-card"
        onClick={() => router.push("/model-test/")}
      >
        <span className="mt-entry-icon">
          <ClipboardList className="size-5" />
        </span>
        <span className="mt-entry-text">
          <span className="mt-entry-title">Model Tests</span>
          <span className="mt-entry-desc">Full 90-min mock exams · 150 marks</span>
        </span>
        <ArrowRight className="mt-entry-arrow size-5" />
      </button>

      <div className="stagger flex flex-col gap-5">
      {/* Section tab — only shown once more than one section has courses */}
      {sections.length > 1 ? (
        <section className="flex flex-col gap-0" style={{ ["--i" as string]: 0 }}>
          <Label className="field-label">Section</Label>
          <Segmented
            testid="section"
            options={sections}
            value={section}
            onChange={changeSection}
          />
        </section>
      ) : null}

      {/* Course */}
      <section className="flex flex-col gap-0" style={{ ["--i" as string]: 1 }}>
        <Label htmlFor="course-select" className="field-label">Course</Label>
        {courses.isLoading ? (
          <Skeleton data-testid="course-skeleton" className="h-13 w-full rounded-[14px]" />
        ) : (
          <Select
            items={visibleCourses.map((c) => ({ value: c.slug, label: c.name }))}
            value={courseSlug}
            onValueChange={(v) => {
              setCourseSlug(v);
              setSubtopicId(WHOLE_COURSE);
            }}
          >
            <SelectTrigger id="course-select" data-testid="course-select">
              <SelectValue placeholder="Choose a course" />
            </SelectTrigger>
            <SelectContent>
              {visibleCourses.map((c) => (
                <SelectItem key={c.id} value={c.slug}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </section>

      {/* Subtopic */}
      <section className="flex flex-col gap-0" style={{ ["--i" as string]: 1 }}>
        <Label htmlFor="subtopic-select" className="field-label">Subtopic</Label>
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
          <SelectTrigger id="subtopic-select" data-testid="subtopic-select">
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
      <section className="flex flex-col gap-0" style={{ ["--i" as string]: 2 }}>
        <Label className="field-label">Questions</Label>
        <Segmented
          testid="count"
          options={COUNTS}
          value={count}
          onChange={setCount}
          getLabel={countLabel}
        />
      </section>

      {/* Difficulty */}
      <section className="flex flex-col gap-0" style={{ ["--i" as string]: 3 }}>
        <Label className="field-label">Difficulty</Label>
        <Segmented
          testid="difficulty"
          options={DIFFICULTIES}
          value={difficulty}
          onChange={setDifficulty}
        />
      </section>

      {/* Mode */}
      <section className="flex flex-col gap-0" style={{ ["--i" as string]: 4 }}>
        <Label className="field-label">Mode</Label>
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

      <div className="hide-on-keyboard safe-bottom [--safe-pad-bottom:1.875rem] dock fixed inset-x-0 bottom-0 z-20 mx-auto max-w-md px-5 pt-3.5">
        <button
          type="button"
          data-testid="start-quiz"
          className="btn-cta"
          disabled={!course || starting}
          onClick={handleStart}
        >
          {starting ? (
            <Loader2 className="size-5 animate-spin" />
          ) : (
            <>
              <span>{course ? "Start quiz" : "Choose a course to start"}</span>
              {course ? <ArrowRight className="btn-cta-arrow size-5" /> : null}
            </>
          )}
        </button>
      </div>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="app flex min-h-dvh flex-col">
      <div className="aurora-bg" />
      <div className="app-inner mx-auto flex w-full max-w-md flex-1 flex-col">
        <header className="brand safe-top [--safe-pad-top:0.5rem] flex items-center px-5 pt-2 pb-4">
          <LogoLockup />
        </header>
        <div className="flex flex-1 flex-col gap-6 px-5 pt-1 pb-32">
          {children}
        </div>
      </div>
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
      className={cn("mode-card", active && "is-active")}
    >
      <div className="mode-top">
        <span className="mode-icon">{icon}</span>
        {active ? <span className="mode-dot" /> : null}
      </div>
      <div className="mode-title">{title}</div>
      <div className="mode-desc">{desc}</div>
    </button>
  );
}
