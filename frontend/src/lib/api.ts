// Client-side API helper. The app is a static SPA (no SSR/route handlers),
// so every backend call goes through here to the FastAPI base URL.

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ── Domain types (mirror backend schemas) ──────────────────────────────────
export type Difficulty = "easy" | "medium" | "hard";
export type RequestDifficulty = Difficulty | "random";
export type QuizMode = "exam" | "practice";

export interface Course {
  id: string;
  name: string;
  slug: string;
  category: string;
  isActive: boolean;
}

export interface Subtopic {
  id: string;
  courseId: string;
  name: string;
  slug: string;
}

// The shape the question renderers (QuestionView, ExplanationPanel,
// QuestionNavigator) actually read. Both quiz questions and model-test
// questions adapt to this so the display components are shared. `difficulty`
// is optional — model tests don't tag a difficulty — and `codeLang` is an
// optional shiki language hint for the code block.
export interface DisplayQuestion {
  id: string;
  difficulty?: Difficulty | null;
  questionText: string;
  codeSnippet?: string | null;
  codeLang?: string | null;
  latex?: string | null;
  options: string[];
  // Present only when answers may be revealed (practice / review).
  correctIndex?: number | null;
  explanation?: string | null;
  distractorRationales?: string[] | null;
}

export interface QuestionOut extends DisplayQuestion {
  courseId: string;
  subtopicId: string;
  difficulty: Difficulty; // always set for bank questions
}

export interface QuizStartRequest {
  courseId: string;
  subtopicId?: string | null;
  count: number;
  difficulty: RequestDifficulty;
  mode: QuizMode;
}

export interface QuizStartResponse {
  sessionId: string;
  mode: QuizMode;
  difficulty: RequestDifficulty;
  count: number;
  durationSeconds?: number | null;
  questions: QuestionOut[];
}

export interface QuestionReview extends QuestionOut {
  selectedIndex: number | null;
  isCorrect: boolean;
}

export interface QuizResultResponse {
  sessionId: string;
  mode: QuizMode;
  score: number;
  total: number;
  questions: QuestionReview[];
}

export interface QuizFillRequest {
  courseId: string;
  subtopicId?: string | null;
  count: number;
  difficulty: RequestDifficulty;
}

export interface QuizFillResponse {
  ready: boolean; // true → enough already; start immediately
  available: number;
  target: number;
  jobId?: string | null; // present when ready=false (a fill job is running)
}

export interface JobProgress {
  done: number;
  target: number;
  percent: number;
}

export interface JobStatus {
  jobId: string;
  status: "running" | "done" | "error";
  progress?: JobProgress | null;
  error?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
}

// ── Endpoint wrappers ──────────────────────────────────────────────────────
export const getHealth = () => apiFetch<HealthResponse>("/health");
export const getCourses = () => apiFetch<Course[]>("/courses");
export const getSubtopics = (slug: string) =>
  apiFetch<Subtopic[]>(`/courses/${slug}/subtopics`);

export const startQuiz = (body: QuizStartRequest) =>
  apiFetch<QuizStartResponse>("/quiz/start", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const fillQuiz = (body: QuizFillRequest) =>
  apiFetch<QuizFillResponse>("/quiz/fill", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const getJob = (jobId: string) =>
  apiFetch<JobStatus>(`/authoring/jobs/${jobId}`);

export const submitQuiz = (sessionId: string, answers: (number | null)[]) =>
  apiFetch<QuizResultResponse>(`/quiz/${sessionId}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });

// ── Model tests (full-length mock exams) ────────────────────────────────────
export interface ModelTestSummary {
  slug: string;
  title: string;
  totalQuestions: number;
  fullMarks: number;
  timeMinutes: number;
  marksPerQuestion: number;
  passMarks: number;
}

export interface ModelTestQuestionOut {
  number: number;
  subject: string;
  marks: number;
  questionText: string;
  codeSnippet?: string | null;
  codeLang?: string | null;
  latex?: string | null;
  options: string[];
  // Withheld during the exam; present in the submitted review.
  correctIndex?: number | null;
  explanation?: string | null;
}

export interface ModelTestStartResponse {
  sessionId: string;
  slug: string;
  title: string;
  durationSeconds: number; // timeMinutes * 60
  totalQuestions: number;
  fullMarks: number;
  passMarks: number;
  marksPerQuestion: number;
  instructions: string[];
  questions: ModelTestQuestionOut[];
}

export interface ModelTestQuestionReview extends ModelTestQuestionOut {
  selectedIndex: number | null;
  isCorrect: boolean;
}

export interface SubjectScore {
  subject: string;
  correct: number;
  total: number;
}

export interface ModelTestResultResponse {
  sessionId: string;
  score: number; // number of correct answers
  total: number; // number of questions
  marks: number; // score * marksPerQuestion
  fullMarks: number;
  passMarks: number;
  passed: boolean;
  subjectBreakdown: SubjectScore[];
  questions: ModelTestQuestionReview[];
}

export const getModelTests = () =>
  apiFetch<ModelTestSummary[]>("/model-tests");

export const startModelTest = (slug: string) =>
  apiFetch<ModelTestStartResponse>(`/model-tests/${slug}/start`, {
    method: "POST",
  });

export const submitModelTest = (
  sessionId: string,
  answers: (number | null)[],
) =>
  apiFetch<ModelTestResultResponse>(
    `/model-tests/sessions/${sessionId}/submit`,
    { method: "POST", body: JSON.stringify({ answers }) },
  );

// ── Visitor tracking ───────────────────────────────────────────────────────
export interface VisitGeo {
  country: string | null;
  countryCode: string | null;
  region: string | null;
  city: string | null;
  lat: number | null;
  lon: number | null;
  timezone: string | null;
  isp: string | null;
}

export interface Visit {
  id: string;
  ip: string;
  geo: VisitGeo | null;
  path: string | null;
  referrer: string | null;
  userAgent: string | null;
  createdAt: string;
}

export interface CountryStat {
  countryCode: string | null;
  country: string | null;
  count: number;
}

/** Record the current visit. Fire-and-forget; never throws to the caller. */
export const trackVisit = (path?: string) =>
  apiFetch<Visit>("/track/visit", {
    method: "POST",
    body: JSON.stringify({ path: path ?? null }),
  }).catch(() => undefined);

const adminHeaders = (password: string): RequestInit => ({
  headers: { "X-Admin-Password": password },
});

export const getVisits = (password: string, limit = 100) =>
  apiFetch<Visit[]>(`/track/visits?limit=${limit}`, adminHeaders(password));

export const getVisitStats = (password: string) =>
  apiFetch<CountryStat[]>("/track/stats", adminHeaders(password));
