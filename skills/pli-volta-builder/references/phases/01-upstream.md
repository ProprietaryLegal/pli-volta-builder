# Phase 1: Upstream first

**Entry:** phase 0's state file exists.

**Goal:** know what already exists for this model on this card generation before planning anything, so nothing is
re-built by accident and no capability question is answered from first principles.

## Do

1. Read the hub's front page and research index (`../upstream-sources.md`), then `../volta-facts.md`.
2. Sweep the engine fork's pull requests and issues for the card generation and for the model family (commands in
   `../upstream-sources.md`). For each relevant one read the body: what it does, its measured numbers, the hardware,
   power, batch, parallel layout and flags they were measured under, its state.
3. Sweep the kernel repositories (v100-skinny and others) and the model author's and vendor's cards.
4. Read the published PLI builds closest to your case (same model family, same card count) and their credits.
5. For other hardware's recipes (newer cards, other engines), list ideas only, each with the hardware assumption
   that would have to hold on yours.

## Writes

- The overlap table in the build's `AGENTS.md` section 0 (columns in `../upstream-sources.md`): one row per upstream
  item that touches this build, with adopted / partly / not / duplicates.
- Section 0's front-line facts for this build: the card's limits that matter, the formats and where each runs, the
  traps, each line labelled and dated.
- The nearest proven recipe for phase 3: which fork commit, which pull requests on top, which launch flags, which
  weights, and the speed upstream measured with it (UPSTREAM).

## Gate to phase 2

The overlap table exists and the nearest proven recipe is named. Every later plan row, window arm and helper brief
lists the table rows it touches.

## Common mistakes

- Reading only merged pull requests: open ones often hold the newest Volta work.
- Copying a model card's serving flags written for newer cards (FP8 KV cache is a measured trap on sm_70).
- Treating a number from other hardware as a prediction for yours. Write it as UPSTREAM with its conditions.
