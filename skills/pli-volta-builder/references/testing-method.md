# Testing method

How a change is judged on a serving build of old cards. The scripts named here are in `scripts/`; the rules behind
the method are in `standing-rules.md`, the failures that shaped it in `lessons.md`.

## Contents
1. The window
2. The amendment (rule before data)
3. The checks every serving candidate passes
4. Identity, closeness and what reference to use
5. Speed: bands, ABBA, the same window
6. Memory: the rehearsal
7. Shaping tests on the workload
8. The small test machine
9. Adopting: alone, then together
10. The serving record and the pair rule

## 1. The window

A window is one planned outage of the test port (and of serving, when there is one machine): stop what serves,
boot arms one at a time on the TEST port, judge each by its written lines, return to serving. One change per boot.
Every arm of a window is compared with the window's own reference boot (`off`: the same engine with every new
switch off), never with an earlier window's figure, so power, drift and boot-to-boot wobble cancel. A window is
driven by a script (`scripts/window_driver.sh` skeleton) with phases, exit codes and one result line per phase,
chained by a short `chain_<name>.sh` that always ends either serving again or saying exactly what does NOT serve and
which commands may follow.

## 2. The amendment (rule before data)

Before a window, append an amendment to the plan's section of amendments (`templates/PLAN.md`), with `date -u`:

    **Amendment N (YYYY-MM-DDTHH:MMZ, before its data): <window tag>: <what it tests>.**
    - WHY NOW: the size of the gain (from the time budget) and what is ready.
    - THE ARMS: each boot, its switches and values, one change per boot, the reference boot.
    - THE LINES: per arm, each acceptance line with its number, its judge (script and arguments) and what PASS,
      FAIL and INCONCLUSIVE mean. A missing cell is INCONCLUSIVE.
    - PREDICTED: the expected figure for each line, with its basis.
    - NEVER MET A SERVER: every piece (kit, switch, tool, pattern) that has not run against a real server, and what
      its failure does (stops the window, or ends one arm and the chain goes on).
    - ADOPTION: what passing means (adoptable by a later `adopt` boot, or adopted now).

After the window, a result amendment: MEASURED figures with conditions, each line PASS/FAIL/INCONCLUSIVE, each
prediction held or wrong (keep the wrong ones), what the window retired from "never met a server", next step.

## 3. The checks every serving candidate passes

- Boot checks: health, no traceback, the expected number of workers each logging its sizing line, the residency
  you planned (for example, the expected count of experts on cards and zero left in host memory), the memory limit
  logged by every worker, no fallback path taken (for example, the drafter not disabled).
- Identity to the accepted capture: the long public prompts captured when the standing configuration was accepted,
  identical token for token (`identity_judge.py`), for any change that should not move rounding.
- The memory rehearsal shaped on the workload, ending under the written line with zero out-of-memory lines
  (`mem_sampler.py judge`).
- A regression cell: one short and one long request, timed, against the same window's `off` boot.
- Line h (repeatability): each chat alone answers the same twice; several together answer as alone.

## 4. Identity, closeness and what reference to use

- **Identity** (`identity_judge.py`): equal length, equal ids, the same prompt digest, the same finish reason
  where both record one, the full key set. Use for every change that claims not to move arithmetic (a scheduler
  change, a cache, a release threshold, a kernel with the same reduction order).
- **Closeness** (`closeness_judge.py`): first divergence, the reference's margin at it, mean |dlogprob| before it.
  Use for a change that moves rounding (another reduction order, another chunk cut, a different split count, a
  different stage layout). Thresholds are written before the data and must be reachable by the reference itself:
  a line copied from another layout's reference can be impossible by construction.
- **Which reference.** Three references answer three questions: the previous serving build (did we break
  anything users had?), the accepted capture of the standing configuration (regression), and a reference in the
  best available arithmetic (fidelity). A reference taken in the OLD arithmetic cannot judge a change that moves
  arithmetic on purpose: the arm parts early and the line is INCONCLUSIVE forever. Take a reference in the arm's
  own arithmetic on a layout that holds everything, or use teacher forcing: feed the same history to both and
  compare next-token decisions (NLL, top-1, margin) at fixed positions across the whole answer, near chunk cuts,
  tool calls and end-of-sequence.
- **Near-ties.** Cross-boot differences at the first token where two candidates' logits differ by a rounding
  step are not bugs; trace each divergence's margin before calling it one.

## 5. Speed: bands, ABBA, the same window

- Report ms per decode round beside tok/s: tokens per round vary with the text when a drafter is on.
- The band is the A/A spread: two runs of the unchanged build in the same window (`speed_band.py band`). A
  difference inside the band is "within band", reported, not a verdict.
- Near a floor, use ABBA order (`speed_band.py abba`): it cancels slow drift over a session.
- Quiet CPU during arms: no builds, no compiles, no other session's jobs on the serving host.
- An untimed warm-up request after each boot: the first request compiles or tunes kernels.
- Same power limit and clock cap for every arm compared; a figure from another power setting is another condition.

## 6. Memory: the rehearsal

Grow one chat per slot to the context users reach (not the average: the long tail), send the turns they send,
sample every card through the whole run (`mem_sampler.py sample`, then `judge` against the line written before).
Stages differ: the stage holding the head and the drafter, or the most layers, is usually fullest. A peak "within the
sampler's resolution" is not a saving. A rehearsal that stops at half the longest real context leaves the top half
untested: say so.

## 7. Shaping tests on the workload

From the workload's measured shape (aggregates only, phase 0): prompt lengths at the median, 90th percentile and
maximum; new tokens per turn; generated tokens per task (reasoning included); how often one, two or more requests
run at once; how often a request begins with the previous one's whole prompt. Build cells for each: a first read at
the common packet size, turns of the common and the 90th-percentile size on a grown chat, a turn beside another
chat's long read, decode at short and long context, all slots grown at once. Use public text of those lengths.
Check every turn cell is a prefix hit in the server log; a turn read cold is not a turn cell (INCONCLUSIVE).

## 8. The small test machine

A smaller machine (four cards, a reduced layout, compressed weights) is where a new piece first meets a server:
it boots, logs what the checks read, keeps identity inside one boot, shows the direction of a speed change. It
never gives a verdict for the big build. It changes the ORDER and CONTENT of the big window: a variant that fails
there is fixed before it costs a stop of the serving build. Keep it busy.

## 9. Adopting: alone, then together

A change is adoptable after it passed every line alone in a window. It is adopted by an `adopt` boot: every
adoptable change on together, judged against the same window's `off` cells: identity 7 of 7 (or the closeness
lines of a rounding change, which is never part of an identity adopt), the boot checks, the rehearsal under the
line, every read rate at or above `off`'s, the small turn and one-request decode no more than a few percent worse,
every cell present. If `adopt` passes, the window ends serving that configuration and records it. If not, the
window returns to what it started from.

## 10. The serving record and the pair rule

The full check runs only on the test port. On PASS it stops its arm and writes the serving record
(`serving_record.py write`): a fingerprint of the kit, profile (without its port line), switches, slot count and
memory limit. The serving boot on the public port sends no request and boots only on a matching record. Any change
makes the record stale and the full check owed. A user's request never reaches a server that is still being judged,
and a user's request can never fail a check.
