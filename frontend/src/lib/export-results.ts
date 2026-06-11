import { Capacitor } from "@capacitor/core";
import type { QuizResultResponse } from "@/lib/api";

const LETTERS = ["A", "B", "C", "D"];

// Strips $…$/$$…$$ math delimiters for a clean plain-text export.
function plain(text: string): string {
  return text.replace(/\$\$?([^$]+)\$\$?/g, "$1").trim();
}

/** A human-readable plain-text report of a finished quiz. */
export function buildResultsText(result: QuizResultResponse): string {
  const pct =
    result.total > 0 ? Math.round((result.score / result.total) * 100) : 0;
  const lines: string[] = [
    "Aurora Hub — Quiz Results",
    "=========================",
    `Mode:  ${result.mode}`,
    `Score: ${result.score} / ${result.total}  (${pct}%)`,
    "",
  ];

  result.questions.forEach((q, i) => {
    const mark = q.isCorrect ? "[CORRECT]" : "[WRONG]";
    lines.push(`Q${i + 1}. ${mark}  (${q.difficulty})`);
    lines.push(plain(q.questionText));
    q.options.forEach((opt, oi) => {
      const flags = [
        oi === q.correctIndex ? "✓ answer" : "",
        oi === q.selectedIndex ? "← you" : "",
      ]
        .filter(Boolean)
        .join(" ");
      lines.push(`   ${LETTERS[oi]}. ${plain(opt)}${flags ? `   ${flags}` : ""}`);
    });
    if (q.explanation) lines.push(`   Why: ${plain(q.explanation)}`);
    lines.push("");
  });

  return lines.join("\n");
}

const FILENAME = "aurora-hub-results.txt";

/**
 * Export the results. Rule 6: a WebView can't trigger a browser download, so on
 * native we write the report to the cache dir and open the native share sheet;
 * on web we keep the ordinary browser download. Plugins are dynamically imported
 * so the web bundle never pulls native code.
 */
export async function shareResults(result: QuizResultResponse): Promise<void> {
  const text = buildResultsText(result);

  if (Capacitor.isNativePlatform()) {
    const { Filesystem, Directory, Encoding } = await import(
      "@capacitor/filesystem"
    );
    const { Share } = await import("@capacitor/share");
    const { uri } = await Filesystem.writeFile({
      path: FILENAME,
      data: text,
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
    });
    await Share.share({
      title: "Aurora Hub — Quiz Results",
      text: "My Aurora Hub quiz results",
      files: [uri],
      dialogTitle: "Share results",
    });
    return;
  }

  // Web: ordinary browser download.
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = FILENAME;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
