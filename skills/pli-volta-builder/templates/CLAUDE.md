@AGENTS.md

## Claude-only notes

- Before any plan, helper brief or build, read AGENTS.md section 0 and do its upstream-overlap check; never answer a
  capability question about this card from first principles alone.
- Architecture research for this card is in `research/` (start with its README); read it before any kernel or
  serving plan. The research hub: https://github.com/ProprietaryLegal/volta-v100-research.
- Custom-kernel source material and the ranked opportunities: `research/kernels/` (read before any kernel work).
- What the build is optimized for: AGENTS.md section 6.0.
- State: BUILD-STATE.md (one screen), then PLAN.md section 9 (newest amendment last).
- A helper does not spawn helpers unless its brief says so; helpers report to the owner.
- Read files freely; never run anything that starts, stops, installs or sends requests unless your brief grants it.
  List those scripts here by path.
- Persistence: an inconclusive result is the start of the next hypothesis; name the missing input and keep going.
- The four sections at the end of this file are copied verbatim from AGENTS.md (pinned so they load in every
  session). Edit both files together; the test `tests/test_shared_sections.py` fails if the copies differ.

## Hard rules (a breach is a failed task)

1. The server and its cards belong to the owner session (<name>). Nobody else boots, stops, signals, sends requests,
   or runs anything on a card.
2. Never write another build's tree. This build's files on the host go under <its own tree> only, on the owner's word.
3. Never print, copy or commit a GPU identifier.
4. Private, never in any repository or report: <the list for this owner: traffic figures, user text, generated text,
   per-expert counts, credentials>.
5. Git: <who commits, who pushes, the boundary check before each commit>.
6. Public tree: only on the owner's order; one boundary check and one privacy read, then publish.
7. Never type into a terminal session you did not start; kill only exact PIDs you started.
8. Fail fast, no retries or fallbacks. A rule is written before its data. INCONCLUSIVE is not a pass. Every pattern
   a check applies to a boot's log first runs on a real log of that boot. `date -u` before stating a time.
9. Engine changes only as kits, applied by the kit's `apply.sh` in the build's own tree while nothing serves from it.
   Never edit a script a running job executes.
10. Crash rule: on a new Xid line or an unplanned host reset, stop nothing, start nothing, send nothing; report to
    the owner; wait for the owner's word.
11. Power, clocks and hardware are the owner's.

## Where state lives
<this repository; the build's tree on the host; the engine work copy; the progress log; the owner's server log>

## Start and stop (owner only)
<the three commands: stop what serves; start from nothing by the pair rule; move the serving arm>

## Building kernels
<identical to AGENTS.md>

## Upstream sources of our optimizations
<identical to AGENTS.md>

## Kernel research records
<identical to AGENTS.md>

## Lever status on this build
<identical to AGENTS.md>
