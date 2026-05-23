# Sections

This file defines all sections, their ordering, impact levels, and descriptions.
The section ID (in parentheses) is the filename prefix used to group rules.

---

## 1. Project Setup with uv (setup)

**Impact:** CRITICAL
**Description:** Using uv correctly is the foundation of every modern Python project. Wrong tooling choices (pip, venv manually, requirements.txt) create reproducibility and portability problems that affect every downstream task.

## 2. Design Decisions (design)

**Impact:** HIGH
**Description:** Choosing the right abstraction — dataclass vs Pydantic, function vs class, composition vs inheritance — determines long-term maintainability. Bad choices here are expensive to undo.

## 3. Testing with pytest (test)

**Impact:** HIGH
**Description:** Well-structured tests catch regressions and document intent. Poorly structured tests are brittle, slow, and give false confidence.

## 4. Type Safety (types)

**Impact:** HIGH
**Description:** Type annotations eliminate whole categories of bugs, make code self-documenting, and enable reliable refactoring. They cost almost nothing to write upfront and save significant time later.

## 5. Python Idioms (idiom)

**Impact:** MEDIUM
**Description:** Idiomatic Python is shorter, faster, and more readable. Non-idiomatic code works but signals unfamiliarity with the language and is harder to maintain.

## 6. Async Patterns (async)

**Impact:** MEDIUM
**Description:** Async/await is frequently misused — applied to CPU-bound work, or blocking the event loop. Used correctly it provides significant I/O throughput; used incorrectly it adds complexity with no benefit.
