# Phase 4: The harness

**Entry:** first light (a server that answers correctly, a baseline, real boot logs kept).

**Goal:** a test harness that can judge a change honestly and return the server to serving without a human at the
keyboard: the window driver, the chains, the serving record, the judges, the rehearsal. Build it once; every
optimization window after this uses it.

## The pieces (templates in `scripts/` and `templates/`; fill `templates/window.conf`)

| Piece | What it does | Template |
|---|---|---|
| Window driver | Phases (check, stop, boot ARM, judge ARM, stoparm, servestate, servedefault), exit codes, one result line per phase, the Xid guard, "nothing booted twice" | `scripts/window_driver.sh` |
| Arm files | `arms/<ARM>.env` (switches, every new one default-off), `.bootchecks` (one check per line), `.lines` (the amendment's acceptance lines as commands) | `templates/arms/` |
| Chains | A window as a short script: stop serving, arms in order, return by the pair rule; its last line says what serves or exactly what does not and which commands may follow | `templates/chain.sh` |
| Serving record and pair rule | Full check on the test port writes the record; the public port boots only on a matching record and sends no request | `scripts/serving_record.py` |
| Identity judge | Strict token identity against the accepted capture | `scripts/identity_judge.py` |
| Closeness judge | For changes that move rounding; thresholds written before the data | `scripts/closeness_judge.py` |
| Capture tool | Sends the public prompts greedily, records ids, log-probabilities, top lists, finish reason, prompt digest | write for your engine's API (`logprobs`, `top_logprobs`) |
| Memory rehearsal | One grown chat per slot at the workload's long-tail context, its turns, cards sampled throughout | `scripts/mem_sampler.py` + a request script you write |
| Speed cells | One request fresh and repeated text, all slots together, prompt reads at the workload's sizes, turns on a grown chat; ms per round beside tok/s | write for your API; judge with `scripts/speed_band.py` |
| Pattern certification | Every regex a boot check or witness applies, run on real logs first | `scripts/log_patterns.py` |
| Data boundary | Before every commit | `scripts/boundary_check.py` |

## Do

1. Fill `window.conf` for this server: start and stop commands for an arm on the test port and for serving, the
   health command, the command that counts Xid lines (`journalctl -k | grep -c Xid`, or `dmesg`), the check that
   the cards are empty, timeouts measured from real boots (a timeout is a failure, not a value to raise).
2. Write the boot checks and certify every pattern on the real boot logs of phase 3 (`log_patterns.py certify`).
3. Write the capture tool and take the ACCEPTED CAPTURE of the standing configuration: long public prompts at
   several sizes, greedy, whole answers with finish reasons. Take it twice in one boot and check the two are
   identical (if not, find out why before anything else).
4. Write the rehearsal shaped on the workload (phase 0's long tail) and run it once on the standing configuration:
   its high-water marks are the reference every later memory line uses.
5. Run the A/A: two boots (or two passes) of the unchanged build in one window; their spread is each speed metric's
   band where it exceeds the 1.6 % adoption cutoff, otherwise the cutoff is. On a small test machine, also check whether two boots of the same bytes give the same answers.
6. Run the full check once on the test port, write the serving record, and move serving to the public port with
   `servedefault`. From now on a test window ends by the pair rule.
7. CPU-test every judge and the driver (`tests/run_all.sh` shows the pattern: hand-worked expected values, never
   values recorded from the code itself) and run every judge once on the REAL receipts of step 3.

## Writes

The harness files in the build's repository (`window/`, `tools/`, `tests/`), `docs/OPERATIONS.md` from its template
(who may do what, ports, start/stop/move, the full check, the crash rule, every tool and test), the accepted capture's
location and digest in PLAN.md, the A/A bands.

## Gate to phase 5

The build serves from a matching record by the pair rule; every judge and pattern has met real receipts and logs;
`tests/` pass; OPERATIONS.md names every command and who may run it.
