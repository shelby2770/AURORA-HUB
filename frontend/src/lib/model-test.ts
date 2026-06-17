// Helpers bridging the model-test API shape to the shared quiz renderers.
import type { DisplayQuestion, ModelTestQuestionOut } from "@/lib/api";

// Adapt a model-test question to the shape QuestionView/ExplanationPanel read.
// Model tests have no per-question difficulty (so the chip is hidden) and use
// `number` as a stable key; `codeLang` carries the shiki language hint.
export function toDisplayQuestion(q: ModelTestQuestionOut): DisplayQuestion {
  return {
    id: String(q.number),
    questionText: q.questionText,
    codeSnippet: q.codeSnippet,
    codeLang: q.codeLang,
    latex: q.latex,
    options: q.options,
    correctIndex: q.correctIndex,
    explanation: q.explanation,
  };
}
