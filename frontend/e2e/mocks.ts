import type { Page, Route } from "@playwright/test";

// Fixed question set with known correct answers, used to drive the UI without
// a live backend. One item has inline math, one has code, one has a latex block
// — so rendering paths (KaTeX/Shiki) are exercised in e2e.
export const MOCK_QUESTIONS = [
  {
    id: "q1",
    courseId: "c1",
    subtopicId: "s1",
    difficulty: "easy",
    questionText: "What is $2+2$?",
    options: ["3", "4", "5", "6"],
    correctIndex: 1,
    explanation: "Because $2+2=4$.",
    distractorRationales: ["too low", "", "too high", "way off"],
  },
  {
    id: "q2",
    courseId: "c1",
    subtopicId: "s1",
    difficulty: "medium",
    questionText: "What does the loop print?",
    codeSnippet: 'for (int i = 0; i < 3; i++) printf("%d", i);',
    options: ["012", "123", "000", "111"],
    correctIndex: 0,
    explanation: "i takes 0, 1, 2.",
    distractorRationales: ["off by one", "", "", ""],
  },
  {
    id: "q3",
    courseId: "c1",
    subtopicId: "s1",
    difficulty: "hard",
    questionText: "Solve the recurrence's complexity.",
    latex: "T(n) = 2T(n/2) + n",
    options: ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
    correctIndex: 1,
    explanation: "Master theorem case 2.",
    distractorRationales: ["", "too small", "too big", ""],
  },
];

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(route: Route, body: unknown, status = 200) {
  if (route.request().method() === "OPTIONS") {
    return route.fulfill({ status: 204, headers: CORS });
  }
  return route.fulfill({
    status,
    headers: { "Content-Type": "application/json", ...CORS },
    body: JSON.stringify(body),
  });
}

function stripAnswers<T extends Record<string, unknown>>(q: T) {
  const { correctIndex, explanation, distractorRationales, ...rest } = q;
  void correctIndex;
  void explanation;
  void distractorRationales;
  return rest;
}

export async function setupApiMocks(page: Page) {
  await page.route("**/courses", (route) =>
    json(route, [
      {
        id: "c1",
        name: "Operating Systems",
        slug: "operating-systems",
        isActive: true,
      },
      { id: "c2", name: "DBMS", slug: "dbms", isActive: true },
    ]),
  );

  await page.route("**/courses/*/subtopics", (route) =>
    json(route, [
      { id: "s1", courseId: "c1", name: "CPU Scheduling", slug: "cpu-scheduling" },
      { id: "s2", courseId: "c1", name: "Paging", slug: "paging" },
    ]),
  );

  await page.route("**/quiz/start", (route) => {
    const body = JSON.parse(route.request().postData() || "{}");
    const exam = body.mode === "exam";
    const questions = MOCK_QUESTIONS.map((q) =>
      exam ? stripAnswers(q) : q,
    );
    return json(route, {
      sessionId: "sess1",
      mode: body.mode,
      difficulty: body.difficulty,
      count: questions.length,
      durationSeconds: exam ? 270 : null,
      questions,
    });
  });

  await page.route("**/quiz/*/submit", (route) => {
    const { answers } = JSON.parse(route.request().postData() || "{}");
    let score = 0;
    const questions = MOCK_QUESTIONS.map((q, i) => {
      const selectedIndex = answers[i] ?? null;
      const isCorrect = selectedIndex === q.correctIndex;
      if (isCorrect) score += 1;
      return { ...q, selectedIndex, isCorrect };
    });
    return json(route, {
      sessionId: "sess1",
      mode: "exam",
      score,
      total: MOCK_QUESTIONS.length,
      questions,
    });
  });
}

// Three-question stand-in for a model test (real tests have 50). Mirrors the
// model-test API shape: an option object isn't used — the backend already
// returns options as an array — and answers are withheld on start.
export const MOCK_MODEL_TEST_QUESTIONS = [
  {
    number: 1,
    subject: "Mathematics",
    marks: 3,
    questionText: "What is $2+2$?",
    options: ["3", "4", "5", "6"],
    correctIndex: 1,
    explanation: "Because $2+2=4$.",
  },
  {
    number: 2,
    subject: "Programming",
    marks: 3,
    questionText: "What does the loop print?",
    codeSnippet: 'for (int i = 0; i < 3; i++) printf("%d", i);',
    codeLang: "c",
    options: ["012", "123", "000", "111"],
    correctIndex: 0,
    explanation: "i takes 0, 1, 2.",
  },
  {
    number: 3,
    subject: "Data Structures & Algorithms (DSA)",
    marks: 3,
    questionText: "Master theorem complexity?",
    latex: "T(n) = 2T(n/2) + n",
    options: ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
    correctIndex: 1,
    explanation: "Master theorem case 2.",
  },
];

export async function setupModelTestMocks(page: Page) {
  await page.route("**/model-tests", (route) =>
    json(route, [
      {
        slug: "model-test-1",
        title: "Model Test 1",
        totalQuestions: 3,
        fullMarks: 9,
        timeMinutes: 90,
        marksPerQuestion: 3,
        passMarks: 4,
      },
    ]),
  );

  await page.route("**/model-tests/*/start", (route) =>
    json(route, {
      sessionId: "mtsess1",
      slug: "model-test-1",
      title: "Model Test 1",
      durationSeconds: 5400,
      totalQuestions: 3,
      fullMarks: 9,
      passMarks: 4,
      marksPerQuestion: 3,
      instructions: ["Answer all questions."],
      questions: MOCK_MODEL_TEST_QUESTIONS.map(stripAnswers),
    }),
  );

  await page.route("**/model-tests/sessions/*/submit", (route) => {
    const { answers } = JSON.parse(route.request().postData() || "{}");
    let score = 0;
    const breakdown: Record<string, { correct: number; total: number }> = {};
    const questions = MOCK_MODEL_TEST_QUESTIONS.map((q, i) => {
      const selectedIndex = answers[i] ?? null;
      const isCorrect = selectedIndex === q.correctIndex;
      if (isCorrect) score += 1;
      const b = (breakdown[q.subject] ??= { correct: 0, total: 0 });
      b.total += 1;
      if (isCorrect) b.correct += 1;
      return { ...q, selectedIndex, isCorrect };
    });
    const marks = score * 3;
    return json(route, {
      sessionId: "mtsess1",
      score,
      total: MOCK_MODEL_TEST_QUESTIONS.length,
      marks,
      fullMarks: 9,
      passMarks: 4,
      passed: marks >= 4,
      subjectBreakdown: Object.entries(breakdown).map(([subject, v]) => ({
        subject,
        ...v,
      })),
      questions,
    });
  });
}
