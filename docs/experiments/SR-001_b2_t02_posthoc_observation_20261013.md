# SR-001 — B2/FM-1 Isolated Intervention — T02 post-hoc observation
**Date:** 2026-10-13  
**Status:** EXECUTED / SAFETY GOAL PASSED ON FROZEN T02 / NOT ELIGIBLE FOR PRODUCTION  
**Human authorization:** explicit HUMAN GO, 2026-10-13, isolated B2/FM-1 only.  
**Issue:** #158 (remains OPEN; experimental/non-functional, weight=0, progress=0).

## Custody and execution
- Proposed change: `experiments/sr001_b2_dimensional_probe.py`; 12 contract tests at `experiments/tests/test_sr001_b2_dimensional_probe.py`.
- Branch: `experiment/issue-158-b2-fm1-isolated-20261013`.
- GitHub Actions specialized execution: [SR-001 B2 isolated probe, run 38388955420](https://github.com/Jk-Pascoal/agent-lab-pascoal/actions/runs/38388955420), job `115267643686`, 2026-10-13 11:15 UTC. All 12 B2 tests PASSED; evidence emitted in machine-readable JSON to that job's log.
- B0 original detector reproduced pairwise by independent `is_possible_duplicate` comparison in 40/40 records. Candidate Selection fixed at 39 retained / 1 positive dropped. T02 loader verified hashes before reading data:
  - catalog: `74e1389f66fd14155dba1b3be9b16ef2ef9fe79b04e16232d2c2fb142e1c218b`
  - GT: `052bd6fec3f165cea9cdbf686cb961af4eccf962f4689d938a00fdc459b92008`
  - manifest: `cab0732e83594111522e5edfd8c4bc1ff310c4be2df0b1d4c282b40a4f48a88b`
- No product files (`src/agent_lab/`), canonical `tests/`, dataset, GT or manifest modified; no tuning of B1 or combination with other interventions.
- Execution was in GitHub-hosted Ubuntu / Python 3.11; not independently reproduced on a local checkout.

## Inconditional detector results (40 pairs)
| Metric | B0 | B2 |
| --- | ---: | ---: |
| TP | 19 | 19 |
| FP | 17 | 13 |
| TN | 3 | 7 |
| FN | 1 | 1 |
| Precision | 0.5277777778 | 0.5937500000 |
| Recall | 0.9500000000 | 0.9500000000 |
| F1 | 0.6785714286 | 0.7307692308 |

## Conditional detector results (39 retained)
| Metric | B0 | B2 |
| --- | ---: | ---: |
| TP | 19 | 19 |
| FP | 17 | 13 |
| TN | 3 | 7 |
| FN | 0 | 0 |
| Precision | 0.5277777778 | 0.5937500000 |
| Recall | 1.0000000000 | 1.0000000000 |
| F1 | 0.6909090909 | 0.7450980392 |

## Pair-level changes
Four and only four original false positives on Rota 2 were vetoed through a bilateral typed physical disagreement:
1. `CASE-SR001-B-T02-005`: fastener length 60 vs 70 mm
2. `CASE-SR001-B-T02-013`: valve nominal inch 3 vs 4
3. `CASE-SR001-B-T02-029`: cable nominal section 16 vs 25 mm²
4. `CASE-SR001-B-T02-037`: belt length 60 vs 62 inches

`CASE-SR001-B-T02-021` was already TN before the intervention and is not counted as recovered. Other 13 FPs remain, including FM-2, FM-3, FM-4. The blocking FN remains. Each pair's candidate state, decision, route, typed signals and truth-for-evaluation are recorded in the execution log. The label and case ID do **not** enter the predicate.

## Gate decision
- **B0 reproducibility:** PASS — 40/40 pairwise; TP19/FP17/TN3/FN1.
- **Frozen input integrity:** PASS through T02 descriptor hash validation.
- **Candidate-selection invariant:** PASS — 39 retained.
- **Zero original TP sacrificed:** PASS — 19 preserved.
- **Safety Goal:** **PASS on T02**.
- **Research status:** **VALID POST-HOC EXPERIMENT, NOT INDEPENDENT VALIDATION, NOT ELIGIBLE FOR PRODUCTION**.

## Limits and next questions
The extractor is intentionally restricted to four typed syntactic contexts in `description_short`; it is not a validated dimensional ontology/parser. A positive result on the same synthetic tranche whose error modes motivated the design is potentially subject to post-hoc selection and overfitting. Sample size 40, one fixed synthetic tranche, and no holdout prohibit generalized efficacy claims. No inferential confidence intervals or production KPI changes are claimed. Before any wider deployment: independent blinded sample, ambiguity/units audit, negative controls and robustness evaluation, new explicit human decision.

**Issue #158 remains open. A1/B3-B5/T03 untouched. B1 remains SAFETY FAILED.**
