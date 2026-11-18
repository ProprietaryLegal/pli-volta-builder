# Operations: running <build name>

Every command that starts, stops, moves, tests or installs anything, and who may run it.

## 1. Who may do what
| Action | Who | How |
|---|---|---|
| Boot, stop, signal a server; send a request to either port; run anything on a card | the owner only | the chains below |
| Install into the build's tree | the owner, while nothing serves from it | `tools/update_tree_kit.sh` (verifies every file) |
| Read logs, plan, CPU tests, analysis | anyone | on copies, off the serving host while a window measures |

## 2. The state at a glance
`BUILD-STATE.md`; on the host: `run/state/SERVING` (which window's arm serves), `run/state/SERVE-CHECKED` (the serving
record).

## 3. Ports
`<serve port>` serves users; `<test port>` is for arms. A server on the public port is never one still being checked.

## 4. Start, stop, move
    bash window/window_driver.sh window.conf TAG stoparm S        # stop what serves
    bash window/chain_start.sh NEWTAG                              # start from nothing by the pair rule
    bash window/chain_move.sh NEWTAG FROM                          # move the serving arm to a new boot

## 5. The full check and when it is owed
What the full check runs; the record it writes; what makes the record stale (any change of kit, profile, switches,
slots, memory limit).

## 6. The fallback
The previous build: how it is booted (only on the owner's command), how its trees are checked untouched first.

## 7. Test arms and their chains
| Arm (phase) | What it judges | Rule (amendment) | Chain | Result so far |
|---|---|---|---|---|

Exit codes of the driver: 0 done; 9 usage or precondition; 14 Xid count changed (crash rule); 20 a stop failed;
30 a boot or boot check failed; 33 a line FAIL; 34 a line INCONCLUSIVE; 36 the serving record is stale.

## 8. The crash rule and its exceptions
"On a new Xid line or an unplanned host reset: stop nothing, start nothing, send nothing, report, wait for the
owner's word." Exceptions only as the owner wrote them, quoted, with the exact tool.

## 9. Power and clocks
The owner's settings, where they are set, when they changed (dated).

## 10. The watch on what serves
What is sampled while the build serves (memory creep, errors), where, and what triggers a report.

## 11. Installing scripts and kits
Never edit a script a running job executes: `install` a new file, keep `<file>.before-<commit>`.

## 12. Tools
## 13. Tests
`make test` (or `tests/run_all.sh`): every judge with hand-worked cases; every pattern certified on real logs.

## 14. Logs: where each window writes
`logs/window/<TAG>/phases.log` (one line per phase), each arm's boot log, receipts. They stay on the host.

## 15. Lessons that are rules
Patterns meet a real log first; a new kit's log lines meet every pattern; rule before data; read the clock; never
edit a running script; never print a GPU identifier; nothing booted twice; public text only in test prompts.
