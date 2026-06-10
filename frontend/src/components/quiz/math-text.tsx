"use client";

import { InlineMath, BlockMath } from "react-katex";
import { Fragment } from "react";

// Renders text that may embed KaTeX: $$block$$ or $inline$. Plain segments
// are returned as-is so normal prose still flows. Used for question text and
// options so formal CS notation renders correctly.
const TOKEN = /(\$\$[^$]+\$\$|\$[^$]+\$)/g;

export function MathText({ children }: { children: string }) {
  if (!children) return null;
  const parts = children.split(TOKEN);

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("$$") && part.endsWith("$$")) {
          return (
            <span key={i} className="block overflow-x-auto py-1">
              <BlockMath math={part.slice(2, -2)} />
            </span>
          );
        }
        if (part.startsWith("$") && part.endsWith("$") && part.length > 1) {
          return <InlineMath key={i} math={part.slice(1, -1)} />;
        }
        return <Fragment key={i}>{part}</Fragment>;
      })}
    </>
  );
}
