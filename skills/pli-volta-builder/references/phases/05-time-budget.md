# Phase 5: The time budget

**Entry:** the harness works (phase 4).

**Goal:** know where the time of the WORKLOAD goes on THIS layout before ranking any optimization. A budget from
another layout or another card count misleads: measure this one.

## Do

1. **An arm T** (one window): the standing configuration with the profiler on (a copy of the serving profile with the
   torch profiler enabled for a fixed number of cycles) and any timing switches the engine has. Its cells, shaped on
   the workload: a first read at the common packet size; turns of the common and the 90th-percentile new-token
   count on a grown chat (each confirmed a prefix HIT in the server log; a cold turn is not a turn cell); a turn at
   the long-tail context; a turn beside another chat's long read; decode rounds at short and long context. Judge
   only that the timing ran whole (trace files from every worker, timer lines from every stage, no traceback).
2. **Parse on the analysis machine, not the server** (`scripts/timebudget_parse.py`):
   - a decode round by stage (stages run in series) and by kind (experts, dense multiplies, drafter, attention,
     norms, router, index, communication), plus the time outside any kernel;
   - a prompt chunk by stage and kind, the cards' idle time inside each step and the host calls during it, by
     INTERVAL INTERSECTION (`steps`), never by comparing totals;
   - the front of a request (API arrival to scheduled): template, tokenization, hashing, hand-over. On a long-context
     workload the front can be a large share of a turn's first token: one build spent 3 to 3.4 microseconds per
     prompt token there on every request, most of it tokenizing the whole prompt again (MEASURED).
3. **Weigh by the workload** (the rule and the instrument checklist: `../workload-weighting.md`). Units per task from phase 0's measured totals: decode rounds per task = generated
   tokens / tokens per round; prompt chunks per task from first reads; turns per task. Seconds per task for each
   item = its time per unit x units.
4. **Write candidates** with a size: for each place the time goes, the levers (from phase 1's table first, then
   your own), the most each could save (its speed-of-light or its share of the measured interval), the effort, and
   whether it is exact (identity) or moves rounding (closeness). Rank by seconds saved per task per effort
   (`timebudget_parse.py rank`).

## Writes

`research/TIME-BUDGET.md` (the tables, every figure MEASURED with window, power and run count), the ranked
candidate list in `documents/plans/KERNEL-AND-OPTIMIZATION-PLAN.md` (tiers: in motion, largest levers, kernel gaps,
latency and housekeeping, closed with their numbers), and PLAN.md's arm T amendment and result.

## Gate to phase 6

A ranked list whose first items each carry a size in seconds per task from measured intervals and measured units.

## Common mistakes

- Ranking by a benchmark's shape (short prompts, many concurrent requests) when the workload is one long request.
- Weighting by requests x median answer instead of counted generated tokens (decode was badly under-weighted that
  way).
- Crediting overlapping host time as idle time (a 16 to 19 % hypothesis became about 9 % by interval analysis, and
  the cards then confirmed about 9.9 %).
