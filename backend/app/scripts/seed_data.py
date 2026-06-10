"""Curated seed content: 9 courses + a sensible, editable subtopic list each.

Order of courses is preserved as a stable display order. Subtopics are chosen
to map cleanly onto GATE CS / MSc-admission style topics so exemplars and
generated questions tag to a meaningful bucket.
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
}
