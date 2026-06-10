"use client";

import { useEffect, useState } from "react";
import { codeToHtml } from "shiki";

// Lazily highlights a code snippet with Shiki. Falls back to a plain <pre>
// until the highlighter resolves (and if highlighting fails). The block scrolls
// horizontally so long lines never break the mobile layout.
const FALLBACK_LANG = "c";

export function CodeBlock({
  code,
  lang = FALLBACK_LANG,
}: {
  code: string;
  lang?: string;
}) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    codeToHtml(code, { lang, theme: "github-dark" })
      .then((out) => {
        if (active) setHtml(out);
      })
      .catch(() => {
        if (active) setHtml(null);
      });
    return () => {
      active = false;
    };
  }, [code, lang]);

  if (html) {
    return (
      <div
        className="my-2 overflow-x-auto rounded-md border bg-[#24292e] p-3 text-sm [&_pre]:!bg-transparent"
        data-testid="code-block"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <pre
      data-testid="code-block"
      className="my-2 overflow-x-auto rounded-md border bg-muted p-3 text-sm"
    >
      <code>{code}</code>
    </pre>
  );
}
