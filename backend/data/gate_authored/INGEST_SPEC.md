# GATE ingest spec (read fully before processing)

You convert scraped GATE CS exam questions into clean, classified MCQ records for a Dhaka
University CS MSc admission study app. This is authorized educational use of official public IIT
exam questions. Your specific input file, output file, year, examName, and verifiedBy are given in
the spawning message.

## Input format
The input file is a JSON array of `{"text": "...", "source": "..."}`. Each `text` is:

```
GATE CS <year> (<year>) — past-year MCQ.

Question: <question, may contain inline C/Java code or math notation>

Options:
A. <opt0>
B. <opt1>
C. <opt2>
D. <opt3>

Correct answer: <one of A/B/C/D>
```

## Output: a JSON array, one object per KEPT question, EXACTLY this schema:

```json
{
  "course": "<course-slug>",
  "subtopic": "<subtopic-slug belonging to that course>",
  "difficulty": "easy" | "medium" | "hard",
  "questionText": "<question prose, cleaned>",
  "codeSnippet": "<code if the question has a program; OMIT this key if none>",
  "latex": "<KaTeX for heavy math/formal notation; OMIT if none>",
  "options": ["<opt0>", "<opt1>", "<opt2>", "<opt3>"],
  "correctIndex": 0,
  "explanation": "<YOUR OWN fresh explanation of why the correct option is right>",
  "distractorRationales": ["<why opt0 wrong>", "<why opt1 wrong>", "<why opt2 wrong>", "<why opt3 wrong>"],
  "examName": "<as given in spawn message>",
  "year": 0,
  "verifiedBy": "<as given in spawn message>"
}
```
`correctIndex` from the 'Correct answer' letter: A=0, B=1, C=2, D=3. Set `year` to the given year.

## Classification — choose course + subtopic from THIS controlled vocabulary ONLY (never invent slugs):

- artificial-intelligence: adversarial-search-games, constraint-satisfaction, informed-heuristic-search, logic-knowledge-representation, machine-learning-basics, probabilistic-reasoning, uninformed-search
- computer-architecture: boolean-algebra-logic-gates, cache-memory-hierarchy, combinational-sequential-circuits, i-o-interrupts, instruction-set-addressing-modes, number-systems-data-representation, pipelining-hazards
- computer-networks: application-layer-dns, data-link-layer-error-control, ip-addressing-subnetting, mac-ethernet, network-models-layering, routing-algorithms, tcp-congestion-control
- data-structures-algorithms: arrays-linked-lists-stacks-queues, asymptotic-recurrence-analysis, divide-conquer, dynamic-programming, graph-traversal-bfs-dfs, greedy-algorithms, hashing, heaps-priority-queues, shortest-paths-mst, sorting-searching, trees-binary-search-trees
- dbms: er-modeling, functional-dependencies-normalization, indexing-b-trees, query-processing, relational-algebra-calculus, sql-queries, transactions-concurrency-control
- distributed-systems: consensus-replication, consistency-models, distributed-transactions, fault-tolerance, mapreduce-distributed-storage, mutual-exclusion-election, time-clocks-ordering
- operating-systems: cpu-scheduling, disk-scheduling, file-systems, memory-management-paging, processes-threads, synchronization-deadlocks, virtual-memory-page-replacement
- programming: arrays-strings-structures, c-pointers-memory, data-types-operators-type-conversion, object-oriented-concepts, parameter-passing-scope, program-output-tracing, recursion-stack-behavior
- theory-of-computation: context-free-grammars-pushdown-automata, pumping-lemmas, regular-expressions-closure-properties, regular-languages-finite-automata, time-complexity-np-completeness, turing-machines-decidability, undecidability-reductions

## DROP RULES — silently SKIP (do not emit) any question that:
- Is OUT OF SCOPE for the courses above: general aptitude/English, engineering or discrete
  mathematics (combinatorics, probability not tied to AI, calculus, linear algebra, set/graph
  theory as pure math, propositional/predicate-logic puzzles), DIGITAL LOGIC design (K-maps, gate
  minimization, flip-flop circuits — computer-architecture's boolean-algebra-logic-gates is only
  for CPU/architecture-context items, NOT pure digital-logic drills), or COMPILER DESIGN (parsing
  tables, LR/LL, syntax-directed translation, code generation). When in doubt whether something is
  core CS in scope vs these dropped areas, DROP it.
- Depends on an image/diagram/table whose content isn't in the text.
- Cannot be cleanly represented as a 4-option single-answer MCQ.

## Quality rules
- Trust the provided 'Correct answer' — it is the official GATE key. Set correctIndex from it. If
  you are highly confident the key is a transcription error, still use the provided key but add a
  `"reviewNote": "<why>"` field.
- Clean OCR/scrape artifacts: smart quotes “ ” → ", stray language tags like "C++"/"C" floating
  above code, doubled spaces. Do NOT change meaning, numbers, or options.
- If the question has a program, move code into `codeSnippet` (faithfully) and keep `questionText`
  as the prose (e.g. "What is the output of the following C program?").
- explanation: 2-5 sentences, YOUR OWN words, technically correct and specific.
- distractorRationales: exactly 4 strings aligned to options by index; "" for the correct slot.
- options: copy the 4 option texts faithfully (cleaned), KEEP original order so correctIndex stays valid.

Process ALL input items rigorously. Write ONLY the specified output file. Then reply with: total
input items, number KEPT, number DROPPED, and kept-by-course breakdown.
