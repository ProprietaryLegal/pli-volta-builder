# Phase 9: Research for new optimizations

**Entry:** the ranked list runs dry (its items are each worth less than the band), or the owner asks "find the next
optimization".

**Goal:** new candidates with a size, each ready to enter phase 6.

## Where to look, in this order

1. **Upstream since your base.** Every pull request merged or opened in the engine fork since your engine's base
   commit (commands in `../upstream-sources.md`), the kernel repositories, the mainline engines. For each: does it
   touch a place the time budget says matters; is its switch already in your engine (search the switch names); does
   it apply to your layout (stages, tensor width, formats).
2. **The time budget again,** at the workload's shape, for what grew since: the index at long context, the front end
   per prompt token, the time outside any kernel, idle cards inside prompt steps, stages that wait for each other.
3. **The hardware's idle resources.** Host memory and CPU cores (tokenization, caching, prefix storage), PCIe and
   NVLink time between hand-offs, a card idle at a stage boundary, the small test machine, power headroom (the
   owner's decision).
4. **The workload's own structure.** How often a request begins with the previous one's whole prompt (a prefix
   cache, a conversation store that survives restarts, a shared document cache), the turn sizes (a turn pipeline
   across stages), how many requests overlap (batched decode only if overlap is common), what the drafter accepts
   on the workload's text (draft depth, drafting mode).
5. **Other engines and other hardware.** Recipes for other hardware (unified-memory boxes such as the DGX Spark,
   newer cards) for ideas (drafting, expert pruning, overlap of communication with compute), checked against your
   card's limits and your numerics. When an idea that won there does not carry over, explain why in your card's
   terms (separate host and card memory instead of unified memory, the PCIe or NVLink bandwidth between stages, no
   tensor cores for that format, a different bottleneck in your time budget), so the owner does not have to ask.
5b. **A better whole package upstream.** At every pass, check whether the engine fork (or another engine) now ships a
   complete package for this model that is better than the one being tuned. Moving to it can be worth more than any
   lever on the old engine; it becomes a new build (phase 3), not an edit of this one.
6. **Papers and model-author write-ups** for the model's own structure (sparse attention indexes, hybrid caches,
   multi-token prediction).
7. **What was rejected before.** Re-read the closed list with its numbers: a lever lost under another condition may
   win under this one; say which condition changed.

## Turn a finding into a candidate

Prefer an existing, usable solution over a complicated new one. Say plainly whether an idea is novel or already
done elsewhere, and give an honest speed estimate with its reason, not the most hopeful one.

For each: what it changes; the place in the time budget it attacks; the most it can save per unit (speed of light or
measured interval) and per task (units from the workload); exact or rounding-moving; the upstream row or "own"; the
effort; what could make it fail. Add it to the ranked list and go to phase 6: append it to the hill-climb ladder
(`climb.json`) in rank order; the loop's fingerprints keep candidates already run on this base from running again.

## Writes

`documents/reviews/UPSTREAM-REVIEW-<date>.md` (what applies, what to avoid), new rows in the kernel and optimization
plan, the overlap table refreshed.
