# Project 2: LLM-as-a-Judge Audit Report

## 1. Agreement with Human Ground Truth
- **Raw Agreement:** 8/30 (26.67%)
- **Cohen's Kappa (κ):** 0.0000

## 2. Position Bias Audit
- **Flipped Verdicts on Swap:** 0/30 (0.0%)
- **Candidate 1 Win Rate (Normal Order):** 0.0%
- **Candidate 1 Win Rate (Swapped Order):** 100.0%

## 3. Length Bias Audit (Zero-Information Padding)
- **Wins Gained purely by Padding:** 0/10 (0.0%)

## 4. Self-Preference & Distribution Comparison
| Verdict | Human Count | Judge Count | Difference |
| :--- | :---: | :---: | :---: |
| Model A (Concise) | 19 | 0 | -19 |
| Model B (Verbose) | 8 | 30 | +22 |
| Tie | 3 | 0 | -3 |

