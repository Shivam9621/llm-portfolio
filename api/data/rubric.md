# Evaluation Rubric for Technical Explanations

This rubric guides the evaluation of candidate answers to technical software engineering questions. Use these criteria to select the superior answer (**Winner: "A"**, **Winner: "B"**, or **Winner: "tie"**).

---

## 1. Core Dimensions

### 1. Correctness (Weight: 45%)
- **Factually Accurate:** Statements about language runtimes, algorithms, protocols, and database semantics must be true.
- **No Hallucinations:** Does not invent imaginary flags, wrong complexity bounds, or non-existent behavior.
- **Edge-Case Truth:** Accurate regarding caveats (e.g. GIL released in C-extensions, circular reference limits).

### 2. Completeness & Nuance (Weight: 35%)
- **Covers Key Mechanics:** Explains *how* and *why* things work under the hood, not just surface-level definitions.
- **Trade-offs & Constraints:** Explains trade-offs (e.g., latency vs. consistency, memory overhead, failure modes).
- **Practical Context:** Relates theoretical concepts to production engineering realities.

### 3. Clarity & Structure (Weight: 20%)
- **Direct & Organized:** Gets straight to the point using logical flow, bullet points, or concise code references.
- **No Fluff or Filler:** Avoids boilerplate, repetitive intros, or padded word count that provides zero technical information.

---

## 2. Benchmark Anchors

### Question Example:
> *"How does Python's Global Interpreter Lock (GIL) impact the performance of CPU-bound vs IO-bound multi-threaded programs?"*

#### Weak Example (Rating: Low)
> *"Python has a GIL which makes multi-threading very fast for all programs because it manages memory safety. For CPU programs it uses multiple cores easily to speed up calculations. For IO programs like downloading files, it also works nicely because threads do parallel processing on your computer."*
- **Why it's Weak:** Factually incorrect. Claims the GIL makes CPU programs use multiple cores and run faster; fails to explain mutex contention or why threads block on the GIL.

#### OK Example (Rating: Medium)
> *"Python's GIL is a mutex that prevents multiple native threads from executing Python bytecodes at once. Because of this, CPU-bound tasks in Python threads don't run in parallel and can actually run slower due to lock contention overhead. For IO-bound tasks like network requests or file reads, threads release the GIL while waiting for IO, so threading provides good concurrency."*
- **Why it's OK:** Factually correct and covers the primary distinction between CPU and IO bound tasks. However, it misses practical nuances like using `multiprocessing` for CPU work or C-extension GIL releases (NumPy/Cython).

#### Strong Example (Rating: High)
> *"The GIL is a process-level mutual exclusion lock designed to ensure CPython's memory management (especially reference counting) is thread-safe without fine-grained locks. Its impact depends heavily on workload type:*
> *1. **CPU-bound tasks:** Because only one thread can hold the GIL at any instant, threads cannot utilize multiple CPU cores in parallel. Furthermore, frequent context switching and lock contention (eval breaker / check intervals) frequently cause multi-threaded CPU tasks to execute slower than single-threaded equivalents. The recommended solution is multi-processing (`multiprocessing` or `concurrent.futures.ProcessPoolExecutor`) or delegating heavy math to libraries like NumPy which explicitly release the GIL.*
> *2. **IO-bound tasks:** When a thread performs blocking system calls (e.g., socket reads, disk I/O, `time.sleep()`), CPython explicitly releases the GIL before the syscall and reacquires it when data is ready. Thus, other threads can execute Python code while one is waiting on I/O, providing effective concurrency without true CPU parallelism.*"
- **Why it's Strong:** Deeply accurate, explains *why* the GIL exists (refcount safety), explains *how* IO releases the GIL at the OS syscall boundary, notes lock contention overhead, and provides actionable production alternatives (`multiprocessing`, NumPy).

---

## 3. Decision Rules for the Judge

1. **Substance over Length:** A concise, punchy answer that covers the key points accurately beats a bloated, repetitive answer. Do not award wins simply for longer text.
2. **Factual Errors Disqualify:** If Answer A contains an objective error (e.g. inverted logic or false claims) and Answer B is correct, Answer B MUST win, regardless of formatting.
3. **Declare a Tie when Justified:** If both answers cover the same essential technical concepts with comparable accuracy and clarity, return `"tie"`. Do not force a winner when differences are purely cosmetic.
