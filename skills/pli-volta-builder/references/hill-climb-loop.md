# The automated loop: hill climbing with the campaign's gates

`scripts/hill_climb.py` automates phase 6 (and runs the candidates phase 9 produces). It proposes one change,
measures it against a reference taken in the same run, keeps it only if it passed every gate, and loops. It is
resumable after any interruption, never runs the same change on the same base twice, and records every loss.

## Where the design comes from

The driver shape is borrowed from 0xSero's `bench/hillclimb.py` in
[0xSero/Inkling-Small-2-Sparks](https://github.com/0xSero/Inkling-Small-2-Sparks) (Apache-2.0), a hill-climb of a
serving configuration on two DGX Sparks. What it does well, and the skill keeps:

- **A small driver with three verbs**: run one step, measure without changing anything, print the state. One step per
  invocation, so a human or a scheduler can run it, stop it and resume it.
- **State plus history**: a JSON state file (current best, candidates tried, the next index) and an append-only JSONL
  history of every run with its full result.
- **An ordered candidate ladder**, each entry changing exactly ONE setting, with a one-line "why". Its author learned
  the one-change rule the hard way: stacking three memory changes in one restart exhausted host memory and cost a
  physical power-cycle.
- **Safety rails before a run**: a candidate that would break a known boot floor, or ask for more context than the
  memory budget covers, is refused before anything restarts; a candidate that needs headroom is deferred when the
  host lacks it.
- **Revert on a failed boot**, and **quality as a hard gate before any speed score**: an incoherent configuration
  scores as a loss however fast it is.
- **A contended run is not comparable**: its tuning log found two measurement bugs (counters flushed on an interval
  smeared one request into the next; another user's traffic inflated step times), and its benchmarks now wait for an
  idle server and flag a contended request.

Two more design ideas, credited: from 0xSero's [omarchy-local-intelligence](https://github.com/0xSero/omarchy-local-intelligence)
(no licence file: the idea only, no code) the outcome states of a sweep (valid, rejected, unsupported, unrun,
infrastructure-invalid) kept visible beside the winners, and a manifest that freezes the exact workload and runtime
identity of every claim; from [0xSero/inkling2-exl3](https://github.com/0xSero/inkling2-exl3) (MIT) the habit of
median-of-repeats sweeps on public prompt text.

## What the borrowed loop lacks for a serving build, and the gates added on top

| Their loop | Why it is not enough here | The gate in `hill_climb.py` |
|---|---|---|
| Compares a candidate's score with the stored best score from an earlier run | Power, drift and boot-to-boot wobble move the number between runs | Reference and candidate measured in the SAME run (ABBA by default); the band is that run's own A/A spread |
| Accepts any score above the best | A gain inside the noise is noise, and a gain under the cutoff is not worth a boot | A metric's change counts only beyond the band, max(the run's A/A spread, `cutoff_pct` 1.8 % of the reference); a gain below `min_gain_s` per task is WITHIN BAND |
| Weighted normalised score of decode, prefill and concurrency | Weights not tied to what a task spends | Seconds saved per task: time per unit x units per task, measured (`workload-weighting.md`) |
| Coherence check (finish reason, repetition) | Coherent is not identical; it misses a changed token | The measure command judges quality with the strict identity or closeness judge against the accepted capture; FAIL is a loss, INCONCLUSIVE never a win |
| Keeps each winning change at once | Two changes that each win can lose together | Winners go to a passed set; `adopt` runs them together against a same-run reference; adopted only if no metric is worse and the set saves at least 97 % of the best single |
| Ladder of predictions in comments | A prediction after the data fits the data | `rule` writes each candidate's amendment (lines and prediction, UTC time) before `step` may run it |
| Any key may be changed | Some settings are the owner's | `owner_keys` (power, clocks, hardware, downloads, a shared server's stop, publishing): the loop stops WAITING-OWNER |
| Next index only | The same change can come back under another name or after a restart | Every (base, change) fingerprint is stored; a repeat is SKIPPED-TRIED unless the candidate states `retry_reason` |
| One process at a time by convention | Two drivers on one server corrupt each other's runs | A PID lock file: a second driver refuses |

## How to use it

1. Phase 5 gives a ranked candidate list. Write `climb.json` (format in the script's docstring): the standing
   configuration as `base`, the time metrics with their units per task, `min_gain_s`, `owner_keys`, `rails`, the
   `measure_cmd`, the candidates in rank order (each one setting, with `why`, `predict`, `exact`).
2. Write `measure_cmd` for your server: given `CLIMB_ARM` and the settings in its environment, it boots that arm on
   the TEST port, runs the cells, judges quality with `identity_judge.py` (or `closeness_judge.py` for a candidate
   marked `"exact": false`), samples memory, stops the arm, and prints one JSON line. Certify its log patterns on
   real logs first. Expensive boots: use `"order": "AB"` with both passes inside one boot and `bands` from phase 4's
   A/A run, rather than booting the reference twice.
3. `hill_climb.py init DIR climb.json`, then loop: `rule DIR` (the amendment, before data), `step DIR` (one run),
   until EXHAUSTED or WAITING-OWNER; then `adopt DIR`. Exit codes: 0 progress, 1 a loss, 3 inconclusive, 5 the
   owner's decision is needed, 9 refused.
4. After ADOPTED: the standing configuration changed. Update the serving record by the full check on the test port,
   and the build's documents (phase 6 step 7). The loop does not touch what serves; serving moves only by the pair
   rule.
5. When the ladder is exhausted: phase 9 for new sized candidates, appended to the ladder; the fingerprints keep the
   old ones from running again on the same base.

## Against over-testing

The loop is a search, not a re-measurement service. Launch the proven recipe before starting it (phase 3). Each
candidate is run once on a base; the fingerprints stop it from running again. A result that is decided (adopted, or a
loss with its numbers) is not re-proven in later windows "to be sure"; if a condition changes, the candidate states
its `retry_reason`. When the ladder runs low, the next step is phase 9's search for new levers, not more decimal
places on the last one.

## What it does not decide

Whether a change that moves rounding is acceptable at all, whether to stop a server others use, which power limit to
run, whether to download a pack: those stay with the owner. The loop's output is a record and a recommendation;
`history.jsonl` and `amendments.md` go into the build's PLAN section 9 as they are.
