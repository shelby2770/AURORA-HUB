import { create } from "zustand";
import type {
  QuizMode,
  QuizResultResponse,
  QuizStartResponse,
  RequestDifficulty,
} from "@/lib/api";

interface QuizState {
  sessionId: string | null;
  mode: QuizMode | null;
  difficulty: RequestDifficulty | null;
  durationSeconds: number | null; // exam only
  startedAtMs: number | null; // for timer; remaining is recomputed from this
  questions: QuizStartResponse["questions"];
  answers: (number | null)[];
  currentIndex: number;
  result: QuizResultResponse | null;

  // actions
  initSession: (res: QuizStartResponse) => void;
  selectAnswer: (index: number) => void;
  goNext: () => void;
  goPrev: () => void;
  goTo: (index: number) => void;
  setResult: (result: QuizResultResponse) => void;
  reset: () => void;
}

const initial = {
  sessionId: null,
  mode: null,
  difficulty: null,
  durationSeconds: null,
  startedAtMs: null,
  questions: [],
  answers: [],
  currentIndex: 0,
  result: null,
};

export const useQuizStore = create<QuizState>((set) => ({
  ...initial,

  initSession: (res) =>
    set({
      sessionId: res.sessionId,
      mode: res.mode,
      difficulty: res.difficulty,
      durationSeconds: res.durationSeconds ?? null,
      startedAtMs: Date.now(),
      // Order is already randomized server-side per start (Mongo $sample +
      // random.shuffle), so it stays aligned with session.questionIds for
      // positional scoring on submit.
      questions: res.questions,
      answers: new Array(res.questions.length).fill(null),
      currentIndex: 0,
      result: null,
    }),

  selectAnswer: (index) =>
    set((s) => {
      const answers = [...s.answers];
      answers[s.currentIndex] = index;
      return { answers };
    }),

  goNext: () =>
    set((s) => ({
      currentIndex: Math.min(s.currentIndex + 1, s.questions.length - 1),
    })),

  goPrev: () =>
    set((s) => ({ currentIndex: Math.max(s.currentIndex - 1, 0) })),

  goTo: (index) =>
    set((s) => ({
      currentIndex: Math.max(0, Math.min(index, s.questions.length - 1)),
    })),

  setResult: (result) => set({ result }),

  reset: () => set({ ...initial }),
}));
