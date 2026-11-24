---
name: pli-volta-builder
description: "Build, serve, test and optimize a large language model (especially big mixture-of-experts models such as DeepSeek) on old NVIDIA datacenter cards - Tesla V100 / Volta sm_70 first, also Turing and Pascal - the way PLI Labs built Volta sPLIt, Volta Max uPLIft and Volta 12X AmPLIfy. Runs the whole campaign in order with its gates - intake, upstream-first sweep of 1Cat-vLLM and v100-skinny, layout arithmetic, first light on a proven recipe, a test harness with strict judges, a measured time budget, one-change-per-boot optimization windows with rules written before data, sm_70 kernels, independent review, research for new levers, and publishing. Use it whenever someone wants to run, fit, split across cards, or speed up a model on V100s or other older GPUs, plan pipeline or tensor parallel layouts, write a Volta kernel, judge whether an optimization really helped, resume such a build, or says 'find the next optimization' on an existing old-GPU build, even if they do not name the skill."
---

# PLI Volta Builder

This skill drives the campaign that built three DeepSeek-V4.1-Flash servers on Tesla V100 cards over many days:
two eight-card builds in two pipeline stages and a twelve-card build in three, each optimized window by window. It
encodes the order of work and the gates that kept it honest. You are the agent that runs it: you plan, build, test
and record; the person who owns the hardware owns the power, the cables, the serving port and the final word on
installs and publishing.

The research behind it lives at https://github.com/ProprietaryLegal/volta-v100-research (read its front page when
you start; phase 1 reads more; if it cannot be reached, the files here are enough to begin). The facts you will
need first are in `references/volta-facts.md`.

## Start or resume

1. Look for the build's state: `BUILD-STATE.md` and `state.json` in the build's repository (templates in
   `templates/`). If they exist, read them, then the newest amendments in `documents/plans/PLAN.md` section 9, and
   continue at the phase and next step they name. Do not restart a finished phase.
2. If there is no state, this is phase 0. Create the build's own repository folder (never inside another build's
   tree), copy the templates you need, and begin.
3. Before the first action that touches a card or a server, settle who the OWNER is (standing rule 1). When the
   person who owns the hardware tells this session to run things on it, this session is the server's owner: it
   alone boots, stops and tests, and still asks the owner for what the owner keeps (power, clocks, hardware, installing into what
   others use, downloading a model other than the one the owner named, publishing). If this session is not the owner, it
   plans, writes and tests on CPU, and hands the owner exact commands.

## The campaign

Read the phase file before doing a phase; each says what to collect, what to write and how to know it is done.

| Phase | Entry | What you do | What you write | Gate to the next | Read |
|---|---|---|---|---|---|
| 0 Intake | a request, no state | hardware, topology, model, formats, the workload's shape, the owner's objectives and bars, standing permissions | BUILD-STATE.md, state.json, AGENTS/CLAUDE from templates | every field filled or UNKNOWN with the command that settles it | `references/phases/00-intake.md` |
| 0b Hardware readiness | intake | link width and NVLink per card, power budget per circuit, faults; hardware settings as measured levers the owner applies | the hardware table in BUILD-STATE.md | every card at its expected link, no open fault | `references/phases/00b-hardware.md` |
| 1 Upstream first | state exists | sweep the engine fork, kernel repos, model cards, PLI builds | the overlap table (AGENTS.md section 0), the nearest proven recipe | table exists; no capability claim from first principles | `references/phases/01-upstream.md`, `references/upstream-sources.md` |
| 2 Layout arithmetic | phases 0-1 | bytes per layer per card, legal cuts, residency, card-count what-ifs, mixed precision by measured expert use, what is NOT possible | PLAN.md sections 1-6 | one layout under the memory line with margin, cuts cited | `references/phases/02-layout.md`, `references/expert-promotion.md` |
| 3 First light | a layout and a recipe | launch the proven recipe unchanged; smoke; baseline; first capture | PLAN result amendment, real boot logs kept | a server answers correctly; a baseline exists | `references/phases/03-first-light.md` |
| 4 Harness | first light | window driver, chains, serving record, strict judges, rehearsal, A/A bands | window/, tools/, tests/, docs/OPERATIONS.md, the accepted capture | serves by the pair rule; every judge and pattern met real data | `references/phases/04-harness.md`, `references/testing-method.md` |
| 5 Time budget | harness works | profile reads, turns, decode rounds at the workload's shape; intersect intervals; weigh by measured per-task totals | research/TIME-BUDGET.md, ranked candidates | first candidates sized in seconds per task | `references/phases/05-time-budget.md`, `references/workload-weighting.md` |
| 6 Optimization loop | ranked list | per candidate: amendment before data, default-off switch, CPU tests through the real entry point, rehearsal, one change per boot, adopt; automated by `scripts/hill_climb.py` | amendments, lever table, changelog, the loop's history | repeats; go to 7, 8 or 9 as named in the file | `references/phases/06-optimization-loop.md`, `references/hill-climb-loop.md` |
| 7 Kernels | a kernel is the top item | upstream kernels first, size, numerics contract, adversarial tests, end-to-end window | kit, tests, lever row, upstream PR | the window of phase 6 decides | `references/phases/07-kernels.md`, `references/kernel-building.md` |
| 8 Independent review | after the budget; every few windows; before release | hand the whole record to a reviewer who did not build it | the review, the amendment acting on it | judge findings fixed and re-run on real receipts | `references/phases/08-review.md`, `templates/REVIEWER-BRIEF.md` |
| 9 Research | the list runs dry, or "find the next optimization" | upstream since base, the budget again, idle hardware, the workload's structure, other engines, papers, the closed list | new sized candidates | each has a size and enters phase 6 | `references/phases/09-research.md` |
| 10 Document and publish | worth keeping; publish on the owner's word | the formal repository; the public tree; boundary check and one privacy read | README, docs, CREDITS, public tree | published, link given | `references/phases/10-publish.md` |

**"Find the next optimization" on an existing build:** resume from its state; if the ranked candidate list has
items worth more than the speed band, take the top one into phase 6 (re-size it in phase 5 first if the
configuration changed since the budget was measured); only when the list is empty or every item is below the band,
go to phase 9. Either way the first thing you write is the amendment, before any window.

**Scale the campaign to the stakes.** A server other people depend on gets everything: the pair rule, the serving
record, the full harness. A single-user box still gets phases 0 to 3 whole, the overlap table, rules before data,
strict judges and A/A bands, but phase 4 can be the identity judge, the memory sampler and the speed cells run by
hand, and windows can be short. Never drop: upstream first, the memory line, INCONCLUSIVE-is-not-a-pass, labelled
numbers, the 1.8 % adoption cutoff.

**Any card generation.** Phases 0 to 6 and 8 to 10 are the same for any cards; only two files are Volta-specific:
`references/volta-facts.md` (the pinned facts) and `references/kernel-building.md` (sm_70 kernels). Phase 0 asks
which generation the build faces; when it is not Volta, say so plainly to the user ("the pinned Volta facts do not
apply to these cards; I will establish this card's facts in phase 1"), read the neighbours table in
`volta-facts.md`, check in phase 1 what the engine fork supports for that compute capability, write the card's own
section 0 facts with sources, and re-derive the speed-of-light figures from its bandwidth and tensor-core formats. Cards without NVLink pay for tensor-parallel all-reduces over PCIe on every layer: measure the best
tensor-parallel and the best pipeline layout both before choosing.

`references/decision-table.md` answers the common forks ("upstream measured it", "a line came back INCONCLUSIVE",
"two candidates conflict", "a new Xid line"). `references/lessons.md` tells what went wrong before and what each
failure taught; read it before designing a harness or a window.

## The owner's four gates: STOP and ask, in every phase

The skill automates everything else. These four stay with the person who owns the hardware, and you stop and ask
before each one, even mid-loop, even when a script could do it, because in every one of the three builds these were
the owner's decisions and nobody else's:
1. **Anything that changes a power limit, a clock cap or another hardware setting** (BIOS, cabling, PCIe or ACS
   settings, card placement): the risk is to hardware and power supplies only the owner can judge.
2. **Stopping or restarting what other people or other programs are using**: they get notice first, a stop waits
   for an idle moment, and the owner's word is needed unless the owner has already given a standing one. A test on
   the test port, or a window on a server only the owner uses, needs no ask once the goal is set: the owner says
   when the machine is needed for other work.
3. **Publishing anything** (a repository, a model upload, a post): it is the owner's name and the owner's data
   boundary.
4. **Spending on a new download or new hardware** (weights other than the model the owner named, a new pack, cards,
   memory): it costs the owner money, disk or time.
`scripts/hill_climb.py` enforces the same four through `owner_keys`: it stops with WAITING-OWNER.
**Standing permissions.** At intake, and whenever the owner gives one, write the standing permissions into
`BUILD-STATE.md` (for example: "test windows need no ask", "install what passes, in this order", "publish when the
campaign closes"), with the date and their limits. While one holds, do not stop to ask again for what it covers.

## Standing rules (every phase; reasons in `references/standing-rules.md`)

1. One owner per server and per card; helpers work on CPU, on copies, or on cards the owner assigned them.
2. The owner's word (or a standing permission) before installing into a serving tree; test windows need no
   permission once the goal is set. Variants are separate builds (own tree or repository), never edits of what
   serves; checkpoint production before any install; test on the small test machine first where one exists.
3. Crash rule: on a new Xid line or an unplanned reset, stop nothing, start nothing, send nothing; report; wait.
4. Power, clocks and hardware are the owner's. Never edit a script a running job executes. Kill only what you
   started. No GPU identifiers in any file.
5. Upstream first: never answer a capability question from first principles; every plan row cites the overlap table.
6. A rule is written before its data, with `date -u`; a wrong prediction stays recorded as wrong.
7. INCONCLUSIVE is not a pass; judges are strict (equal length, full key set, missing cell = INCONCLUSIVE).
8. Fail fast: no retries, no fallbacks, no raised timeouts; nothing is booted twice in a window.
9. Every pattern a check applies to a log meets a real log of that boot kind first (`scripts/log_patterns.py`).
10. Label every number MEASURED (hardware, power, runs), UPSTREAM (link, conditions) or ESTIMATE (arithmetic).
11. Compare like with like: same window, same power, a reference in the right arithmetic; speed bands from A/A.
    **Adoption cutoff 1.8 %** (the owner, 2026-11-24): a change is adopted only when its target figure gains more than
    max(1.8 % of the reference, the window's A/A spread) and no other cell loses more than that band; a smaller gain is
    "within band", recorded, not installed. Scripts and judges carry it (`speed_band.py --cutoff-pct`, `hill_climb.py`
    `cutoff_pct`).
12. Tests go through the server's real entry point and replay the owner's real workload on the owner's machines;
    only what will be published (or shared logs) is limited to public text.
13. Launch the proven recipe before validating pieces; install what upstream measured on correctness and stability.
14. Switch on only what is proven: passed alone, then again in the whole configuration (`adopt`); a window ends
    serving what it proved.
15. Rank by seconds saved per task of the measured workload, not by a benchmark.
16. Persist: a failed round is the next hypothesis, no round limit; but fix causes, never stack new gates. A test
    exists to decide something: launch the proven recipe first, never re-prove a known result window after window,
    and search for the next lever instead of re-measuring the last one.
17. Keep test cards busy; match model and effort to the task; launch only the helpers the owner's number allows and
    the work needs; respect the owner's usage ceiling and report cadence.
18. State files and amendments so any new session can resume; a hand-off is written, read, checked against the live
    state and acknowledged (`references/standing-rules.md` rule 28).
19. Publish when the owner asks, after one boundary check and one privacy read.

## Scripts (CPU, Python 3 standard library and bash; each has `--self-test` with hand-worked values)

| Script | Use it for |
|---|---|
| `scripts/window_driver.sh` | the skeleton of a test window: phases, exit codes, Xid guard, one line per phase (fill `templates/window.conf`) |
| `scripts/serving_record.py` | the pair rule: write the record after a full check; refuse to serve on a stale one |
| `scripts/identity_judge.py` | strict token identity of two captures |
| `scripts/closeness_judge.py` | first divergence, margin and mean dlogprob for changes that move rounding |
| `scripts/hill_climb.py` | the automated loop of phase 6: one change per run against a same-run reference, strict gates, adopt together, resumable, losses recorded (`references/hill-climb-loop.md`) |
| `scripts/speed_band.py` | A/A bands with the 1.8 % adoption cutoff, and ABBA paired deltas |
| `scripts/mem_sampler.py` | card memory samples during a rehearsal, judged against the memory line |
| `scripts/timebudget_parse.py` | step intervals (union, intersection), kernel time by kind, candidate ranking |
| `scripts/log_patterns.py` | certify every pattern on real logs before it guards a window |
| `scripts/boundary_check.py` | the data-boundary check before a commit or a publish |

Run `bash tests/run_all.sh` (from the skill's folder) once after installing to see them pass on this machine. Copy the ones a build
uses into its own `tools/` and adapt them there; keep their self-tests.

## Templates

`templates/BUILD-STATE.md`, `state.json`, `PLAN.md` (with the amendment form), `AGENTS.md` (section 0 and the
operating rules), `CLAUDE.md` (the pinned-section pattern), `OPERATIONS.md`, `LANE-BRIEF.md` (a helper's brief),
`REVIEWER-BRIEF.md`, `CREDITS.md`, `window.conf`, `chain.sh`, `arms/` (an `off` arm).

## When you cannot reach the hardware

Many sessions plan on one machine while the cards are on another, or are asked before the cards arrive. Go as far
as the phase allows without a card (phases 0 to 2 need none; phase 4's CPU tests and phase 5's parsing need only
copies), then stop at the first step that needs a card and write, in `BUILD-STATE.md` under "To run on the machine",
the exact commands in order, who runs them (the owner), what each writes, and what you will do with the result.
Tell the user that list is the next step. Never claim a figure you did not measure.

## Reporting to the owner

Lead with the answer, and with what the owner asks first: tok/s and context. Speed in tables (no clock times in
them, so they can become graphics): prefill and decode at each normal context length, decode by content type (code,
structured output, prose, chat, the owner's own domain), several requests together where concurrency is on, each
change as a percent against the build's own reference. Then: what is built, what is tested, what is proven (passed its written lines on the real
cards), what is optimized (serving now, with the measured gain and its conditions), what failed and why, what is
next and its expected size (ESTIMATE). Numbers labelled. Times from the clock. Never score one of the owner's builds
against another in anything public.

## Closing a campaign

The owner decides when returns have diminished. On the owner's word: a final bench at every normal context and concurrency,
the documents and the public page updated (phase 10), wins and failed attempts sent upstream, and the list of what is
left with each item's size, so the next campaign starts from it.
