import { create } from "zustand";
import type {
  ModelTestQuestionOut,
  ModelTestResultResponse,
  ModelTestStartResponse,
} from "@/lib/api";

// Mirrors `store/quiz.ts` but for a full-length model test. Model tests are
// always timed (exam-style); scoring/pass-fail come back from the backend on
// submit, so the store only tracks the in-progress sitting plus the result.
interface ModelTestState {
  sessionId: string | null;
  slug: string | null;
  title: string | null;
  durationSeconds: number | null;
  startedAtMs: number | null;
  fullMarks: number;
  passMarks: number;
  marksPerQuestion: number;
  questions: ModelTestQuestionOut[];
  answers: (number | null)[];
  currentIndex: number;
  result: ModelTestResultResponse | null;

  initSession: (res: ModelTestStartResponse) => void;
  selectAnswer: (index: number) => void;
  goNext: () => void;
  goPrev: () => void;
  goTo: (index: number) => void;
  setResult: (result: ModelTestResultResponse) => void;
  reset: () => void;
}

const initial = {
  sessionId: null,
  slug: null,
  title: null,
  durationSeconds: null,
  startedAtMs: null,
  fullMarks: 150,
  passMarks: 60,
  marksPerQuestion: 3,
  questions: [],
  answers: [],
  currentIndex: 0,
  result: null,
};

export const useModelTestStore = create<ModelTestState>((set) => ({
  ...initial,

  initSession: (res) =>
    set({
      sessionId: res.sessionId,
      slug: res.slug,
      title: res.title,
      durationSeconds: res.durationSeconds,
      startedAtMs: Date.now(),
      fullMarks: res.fullMarks,
      passMarks: res.passMarks,
      marksPerQuestion: res.marksPerQuestion,
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
