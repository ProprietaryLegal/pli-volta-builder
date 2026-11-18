# Phase 6: The optimization loop

**Entry:** a ranked candidate list (phase 5) and a working harness (phase 4).

**Goal:** turn candidates into proven, serving improvements, one change per boot, fast, without trading away
quality. The owner's order for this loop: prioritize the fastest, biggest gains and run; switch on what is proven;
go as fast as possible but do not sacrifice the quality of optimizations.

## For each candidate, in rank order

1. **Upstream row.** Name the overlap-table rows it touches. If upstream measured it on equivalent hardware and
   documents it in use: install on correctness and stability, measure for the record (skip to step 6).
2. **Rule and prediction before data.** Write the amendment (`../testing-method.md` section 2): arms, lines,
   predictions with their basis, the "never met a server" list.
3. **Default-off switch.** The new path behind an environment switch, off by default; the off path proven unchanged
   (identity against the accepted capture with the switch off). The engine change lives as a kit (`kit/<NAME>/`:
   `apply.sh`, `rollback.sh`, `MANIFEST` with base and new sha256 of every file), applied only to the build's own
   tree while nothing serves from it, and to BOTH the installed site-packages and the source tree if the engine
   imports one and the build keeps the other.
4. **CPU tests through the real entry point.** Test the code path the server runs (the scheduler's real loop, the
   loader the engine calls, the API server's renderer), not a helper beside it. Expected values from arithmetic,
   a specification or a real observation, never recorded from the code under test. Certify the kit's new log lines
   against every pattern of the driver.
5. **Small-machine rehearsal** if one exists: does it boot, does it log what the checks read, does it keep identity
   inside one boot, which way does speed move. It reorders the big window; it proves nothing.
6. **The window.** `off` (this window's reference), then one boot per variant on the test port, each judged against
   `off`'s same cells; a failed boot is stopped and the chain goes on; the way back by the pair rule.
7. **Adopt.** A variant that passed alone joins an `adopt` boot with every other passing variant; adopt passes ->
   the window ends serving that configuration, the record is rewritten, the docs updated in one commit (README
   figures, measurements, changelog, lever table, AGENTS section 0). Rounding-moving variants are judged by their
   closeness lines and are never part of an identity adopt.
8. **Record wins and losses** with numbers in the lever table and the result amendment. A loss recorded saves the
   next session from re-proposing it.

## Pace

- Batch variants that are ready into one window; do not hold a ready variant for one that is hours away.
- Use the small test machine and CPU helpers in parallel (within the owner's number), the big machine for windows.
- A failed or inconclusive round is the next hypothesis: name the cause, fix the cause (often the probe or the
  judge, not the change), run again next window. No round limit. No new gate for each failure.
- Mid-campaign, NOTHING changes in what serves outside a window: a change of kit, profile, switch, slots or memory
  limit is a new amendment and makes the serving record stale.

## Writes

Per window: the before-data amendment, the result amendment, the lever table rows, `BUILD-STATE.md` (what serves now,
from which record), the changelog.

## Gate

There is no gate out of this phase: it repeats. Go to phase 7 when the top candidate is a kernel, phase 8 at the
review points, phase 9 when the ranked list's remaining items are each worth less than the band.
