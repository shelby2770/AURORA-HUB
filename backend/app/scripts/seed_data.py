"""Curated seed content: courses + a sensible, editable subtopic list each.

Order of courses is preserved as a stable display order. Subtopics are chosen
to map cleanly onto GATE CS / MSc-admission style topics so exemplars and
generated questions tag to a meaningful bucket.

Courses are grouped into two section tabs via ``COURSE_CATEGORY``:
  - "Computer Science": the core CS syllabus.
  - "Others":           Mathematics, Statistics, Analytical Ability.
A course not listed in ``COURSE_CATEGORY`` defaults to "Computer Science".
"""
from __future__ import annotations

# course name -> list of subtopic names
SEED: dict[str, list[str]] = {
    "Theory of Computation": [
        "Regular Languages & Finite Automata",
        "Regular Expressions & Closure Properties",
        "Context-Free Grammars & Pushdown Automata",
        "Pumping Lemmas",
        "Turing Machines & Decidability",
        "Undecidability & Reductions",
        "Time Complexity & NP-Completeness",
    ],
    "Programming": [
        "C Pointers & Memory",
        "Recursion & Stack Behavior",
        "Data Types, Operators & Type Conversion",
        "Arrays, Strings & Structures",
        "Parameter Passing & Scope",
        "Object-Oriented Concepts",
        "Program Output & Tracing",
    ],
    "Data Structures & Algorithms": [
        "Arrays, Linked Lists, Stacks & Queues",
        "Trees & Binary Search Trees",
        "Heaps & Priority Queues",
        "Hashing",
        "Graph Traversal (BFS/DFS)",
        "Shortest Paths & MST",
        "Sorting & Searching",
        "Greedy Algorithms",
        "Dynamic Programming",
        "Divide & Conquer",
        "Asymptotic & Recurrence Analysis",
    ],
    "Computer Architecture": [
        "Number Systems & Data Representation",
        "Boolean Algebra & Logic Gates",
        "Combinational & Sequential Circuits",
        "Instruction Set & Addressing Modes",
        "Pipelining & Hazards",
        "Cache & Memory Hierarchy",
        "I/O & Interrupts",
    ],
    "Operating Systems": [
        "Processes & Threads",
        "CPU Scheduling",
        "Synchronization & Deadlocks",
        "Memory Management & Paging",
        "Virtual Memory & Page Replacement",
        "File Systems",
        "Disk Scheduling",
    ],
    "Computer Networks": [
        "Network Models & Layering",
        "Data Link Layer & Error Control",
        "MAC & Ethernet",
        "IP Addressing & Subnetting",
        "Routing Algorithms",
        "TCP & Congestion Control",
        "Application Layer & DNS",
    ],
    "DBMS": [
        "ER Modeling",
        "Relational Algebra & Calculus",
        "SQL Queries",
        "Functional Dependencies & Normalization",
        "Transactions & Concurrency Control",
        "Indexing & B+ Trees",
        "Query Processing",
    ],
    "Distributed Systems": [
        "Time, Clocks & Ordering",
        "Mutual Exclusion & Election",
        "Consensus & Replication",
        "Consistency Models",
        "Fault Tolerance",
        "Distributed Transactions",
        "MapReduce & Distributed Storage",
    ],
    "Artificial Intelligence": [
        "Uninformed Search",
        "Informed & Heuristic Search",
        "Adversarial Search & Games",
        "Constraint Satisfaction",
        "Logic & Knowledge Representation",
        "Probabilistic Reasoning",
        "Machine Learning Basics",
    ],
    # ── Others section (non-CS-core subjects on the DU MSc Phase 1 syllabus) ──
    "Mathematics": [
        "Algebra & Equations",
        "Trigonometry",
        "Limits & Continuity",
        "Differentiation",
        "Integration",
        "Matrices & Determinants",
        "Permutations & Combinations",
    ],
    "Statistics": [
        "Central Tendency",
        "Measures of Dispersion",
        "Probability",
        "Probability Distributions",
        "Correlation & Regression",
        "Sampling & Estimation",
        "Hypothesis Testing",
    ],
    "Analytical Ability": [
        "Logical Reasoning & Syllogisms",
        "Number & Letter Series",
        "Data Interpretation",
        "Quantitative Aptitude",
        "Puzzles & Seating Arrangements",
        "Coding-Decoding & Direction Sense",
    ],
}

# Section tab per course. Anything omitted defaults to "Computer Science".
COMPUTER_SCIENCE = "Computer Science"
OTHERS = "Others"

COURSE_CATEGORY: dict[str, str] = {
    "Mathematics": OTHERS,
    "Statistics": OTHERS,
    "Analytical Ability": OTHERS,
}

# Stable display order of the section tabs in the UI.
CATEGORY_ORDER: list[str] = [COMPUTER_SCIENCE, OTHERS]


def category_for(course_name: str) -> str:
    """Section tab a course belongs to (default: Computer Science)."""
    return COURSE_CATEGORY.get(course_name, COMPUTER_SCIENCE)
