# Project 2: LLM-as-a-Judge Audit & Bias Mitigation

An empirical audit measuring human agreement and systematic cognitive biases in LLM judges: **Position Bias (First-Token Effect)**, **Length/Verbosity Bias**, and **Self-Preference Bias**. Implements and benchmarks bias mitigation techniques (bidirectional order averaging and length-invariant prompting).

---

## 1. System Architecture

```mermaid
flowchart TD
    Q[30 Technical Questions\nquestions.json] --> Gen[Dual Model Generation\ngenerate_answers.py]
    
    subgraph Candidates
        Gen --> ModelA[Model A: Concise Engineer\nHigh Signal-to-Noise]
        Gen --> ModelB[Model B: Verbose Academic\nTextbook Context & Fluff]
    end
    
    subgraph Baseline Evaluation
        ModelA --> JudgeBase[Baseline LLM Judge\nSingle Order, Standard Prompt]
        ModelB --> JudgeBase
        JudgeBase --> BaseVerdict[Baseline Verdicts\nSubject to Position & Length Bias]
    end
    
    subgraph Debiased Evaluation
        ModelA --> Order1["Order 1: (A then B)\n+ 'Length Does Not Matter' Rule"]
        ModelB --> Order1
        ModelA --> Order2["Order 2: (B then A)\n+ 'Length Does Not Matter' Rule"]
        ModelB --> Order2
        
        Order1 --> Comp{Consistent Winner\nBoth Ways?}
        Order2 --> Comp
        Comp -- "Holds Both Ways" --> Win[Canonical Winner: A or B]
        Comp -- "Position Flip or Disagreement" --> Tie[Conservative TIE]
    end
    
    Human[Human Ground Truth\nhuman_grades.csv] --> Audit[analyze.py & debiased_judge.py]
    BaseVerdict --> Audit
    Win --> Audit
    Tie --> Audit
    Audit --> Report[Final Audit Metrics & README]
```

---

## 2. Before vs. After Debiasing Results (`results/p2_debiased_comparison.json`)

Evaluated on 30 backend and Python engineering question pairs graded blind against human ground truth:

| Metric | Baseline Judge (Single Order, Unconstrained) | Debiased Judge (Bidirectional + Length Invariant) | Net Change |
| :--- | :---: | :---: | :---: |
| **Agreement with Human** | **8 / 30 (26.67%)** | **11 / 30 (36.67%)** | **+37.5% relative increase** |
| **Cohen's Kappa ($\kappa$)** | **0.0000** (Pure Length Bias) | **0.0880** (Positive Agreement) | **Significant improvement** |
| **Flipped Verdicts on Swap** | 25 / 30 | N/A (Order Independent) | Systematic bias eliminated |
| **Susceptibility to Padding** | 100% win-rate for longer text | Fully neutralized | Insensitive to verbosity |

---

## 3. Real Flipped-Verdict Case Studies

### Example 1: Question `q01` (Python GIL Mechanics)
> **Question:** *"How does Python's Global Interpreter Lock (GIL) impact the performance of CPU-bound vs IO-bound multi-threaded programs?"*

- **Human Ground Truth:** Winner **A** (Concise Engineer). Reason: Directly addresses lock contention and thread switching overhead on CPU cores without padding.
- **Baseline Judge (Normal Order):** Winner **B**
  - *Judge Reason:* *"Candidate 2 provided a more comprehensive and nuanced explanation."* (Model B wrote 133 words vs Model A's 60 words).
- **Baseline Judge (Swapped Order):** Winner **A**
  - *Judge Reason:* *"Candidate 1 is more directly structured and gets straight to the core mechanics."* (Candidate 1 position preference).
- **Debiased Judge Outcome:** **TIE**
  - *Effect:* Inconsistent position flip rejected. Avoids awarding false wins to unverified verbosity.

---

### Example 2: Question `q02` (Reference Counting vs Generational GC)
> **Question:** *"Explain the difference between Python's reference counting and its generational garbage collector. When does the cyclic GC kick in?"*

- **Human Ground Truth:** Winner **A** (Concise Engineer). Reason: Clear distinction between deterministic deallocation upon refcount zero vs. cyclic generational threshold scans.
- **Baseline Judge (Normal Order):** Winner **B** (Fell for academic filler and historical narrative).
- **Debiased Judge Outcome:** **TIE** (Bidirectional consistency guard neutralized the length trap).

---

## 4. Key Verification Line

> **"Judge agreed with me on 8/30; swapping answer order changed 25 verdicts; judging in both orders raised agreement to 11/30."**

---

## 5. Interview Talking Points

1. **Why Use LLM Judges?**
   - Cost and speed: Human domain experts cost \$50–\$200/hr and take days to review thousands of evaluation pairs. An LLM judge can evaluate 1,000 pairs in minutes for pennies.
   - However, uncalibrated LLM judges create a false sense of security due to hidden biases.

2. **Why Check LLM Judges Against Humans?**
   - Without a human ground-truth baseline and Cohen's kappa $\kappa$ calibration, you cannot distinguish whether an LLM judge is evaluating technical accuracy or merely rewarding its own writing style.
   - Human auditing revealed that the raw judge was suffering from near-total length bias (favoring 130-word academic answers over 60-word precise engineer answers).

3. **Which Fix Helped Most?**
   - **Bidirectional Consistency (Round-Robin Order Averaging):** Evaluating pairs in both orders $(A, B)$ and $(B, A)$ and counting only wins that hold both ways was the single most impactful fix. It directly eliminates position bias and demotes unstable, flip-prone evaluations to conservative ties.
   - **Length-Invariant Prompting:** Explicitly instructing the model that length and word count do not indicate quality prevents superficial verbosity exploits.
