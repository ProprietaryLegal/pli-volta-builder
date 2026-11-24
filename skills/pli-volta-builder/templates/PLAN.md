# PLAN: <model> on <n> <card> (<layout>)

Written <date -u> by <owner>. Labels: MEASURED (a log or probe, named), READ (code or a document, path given),
ARITHMETIC (shown here, from measured values), ESTIMATE (basis given), UPSTREAM (someone else's, linked).

**Decisions since the plan was written** (they govern where older text below differs; newest first):
- <date>: <the owner's decision, quoted, and what it changed>.

## 1. Answer
One paragraph: what will run, on which cards, in which layout, at what precision, and what is NOT possible.

## 2. Facts this plan stands on
Each with its label and source: card memory and the memory line; model geometry; bytes per expert/layer per card;
legal stage cuts; the overlap-table rows (AGENTS.md section 0) this plan touches, each adopted / partly / not /
duplicates.

## 3. Candidate layouts
| Layout | Stages x TP | Cuts | Residency (on card / compressed / host) | Fits? (arithmetic) | Why chosen or not |
|---|---|---|---|---|---|

## 4. Memory per card for the chosen layout (ARITHMETIC; not a boot)
| Stage | Layers | Weights | KV at <context> x <slots> | Graphs | Working memory | Total | Under the line by |
|---|---|---|---|---|---|---|---|

## 5. Which board holds which stage
Board order, hand-off pairs, ACS state, the probes to run before the first boot.

## 6. What the engine must change: the kit
Files, entry points (which server path runs each file, and whether a CPU test goes through it), switches (each
default-off), the kit's MANIFEST.

## 7. Expected speed (ESTIMATES; today's figures MEASURED)

## 8. Steps
The windows in order, each with its chain and what it ends serving.

## 9. Acceptance rule (fixed <date -u>, before any data) and amendments

Numbered lines, each with its judge and what PASS / FAIL / INCONCLUSIVE mean. INCONCLUSIVE is never a pass.

### Amendment form (copy for each window; time stamp from `date -u`)

**Amendment N (YYYY-MM-DDTHH:MMZ, before its data): window <TAG>: <what it tests>.**
- WHY NOW: <the size from the time budget; what is ready>.
- THE ARMS: `off` (this window's reference: every new switch off); `<variant>` (<switch=value>); ... One change per
  boot.
- THE LINES (each against `off`'s same cells; a missing cell is INCONCLUSIVE; strict judges):
  - `<variant>` line a: <boot checks>; line b: <identity 7 of 7 / closeness thresholds>; line c: <speed floor with
    its band: max(1.8 % of the reference, the A/A spread)>; line d: <memory: rehearsal at or under <MiB>, 0 out-of-memory lines>.
- PREDICTED: <figure per line, basis>.
- NEVER MET A SERVER: <piece>: <what its failure does>.
- ADOPTION: <adoptable by a later `adopt` boot / adopted now if `adopt` passes>.

**Amendment N+1 (YYYY-MM-DDTHH:MMZ): window <TAG>'s result.**
- MEASURED (<chain and tag>, <start> to <end>, <minutes without a server>, <power>, <runs per figure>): per arm,
  each line PASS / FAIL / INCONCLUSIVE with figures.
- PREDICTED vs MEASURED: held / WRONG (keep the wrong ones, with the corrected model).
- RETIRED from "never met a server": <...>. Not retired: <...>.
- What serves now, from which record. NEXT WINDOW: <...>.

## 10. Way back to the previous default
## 11. Side questions and their answers
## 12. What is ready, and where
## 13. Risks, plainly
