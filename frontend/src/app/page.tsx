"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { GraduationCap, Loader2, Timer, Zap } from "lucide-react";
import { toast } from "sonner";
import {
  getCourses,
  getSubtopics,
  startQuiz,
  type RequestDifficulty,
  type QuizMode,
  ApiError,
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
import { cn } from "@/lib/utils";

const WHOLE_COURSE = "__whole__";
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
  const countOptions = useMemo(
    () => (wholeCourse ? [10, 20, 30, 40, 50] : [10, 20, 30, 40]),
    [wholeCourse],
  );

  // 50 is whole-course only; clamp when narrowing scope to a subtopic.
  const changeSubtopic = (v: string | null) => {
    const next = v ?? WHOLE_COURSE;
    setSubtopicId(next);
    if (next !== WHOLE_COURSE && count === 50) setCount(40);
  };

  const start = useMutation({
    mutationFn: () =>
      startQuiz({
        courseId: course!.id,
        subtopicId: wholeCourse ? null : subtopicId,
        count,
        difficulty,
        mode,
      }),
    onSuccess: (res) => {
      initSession(res);
      router.push("/quiz/");
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 404) {
        toast.error("No questions available yet for this selection.");
      } else {
        toast.error("Could not start the quiz. Is the backend running?");
      }
    },
  });

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 p-5 pb-24">
      <header className="flex items-center gap-3 pt-2">
        <GraduationCap className="size-8 text-primary" />
        <div>
          <h1 className="text-2xl font-bold leading-tight">Aurora Hub</h1>
          <p className="text-sm text-muted-foreground">Build your quiz</p>
        </div>
      </header>

      {/* Course */}
      <section className="flex flex-col gap-2">
        <Label>Course</Label>
        <Select
          value={courseSlug ?? undefined}
          onValueChange={(v) => {
            setCourseSlug(v);
            setSubtopicId(WHOLE_COURSE);
          }}
        >
          <SelectTrigger data-testid="course-select" className="h-12">
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
      </section>

      {/* Subtopic */}
      <section className="flex flex-col gap-2">
        <Label>Subtopic</Label>
        <Select
          value={subtopicId}
          onValueChange={changeSubtopic}
          disabled={!courseSlug}
        >
          <SelectTrigger data-testid="subtopic-select" className="h-12">
            <SelectValue placeholder="Whole course" />
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
          options={countOptions}
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

      <div className="fixed inset-x-0 bottom-0 mx-auto max-w-md p-5">
        <Button
          data-testid="start-quiz"
          size="lg"
          className="h-14 w-full text-base"
          disabled={!course || start.isPending}
          onClick={() => start.mutate()}
        >
          {start.isPending ? (
            <Loader2 className="size-5 animate-spin" />
          ) : (
            "Start quiz"
          )}
        </Button>
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
