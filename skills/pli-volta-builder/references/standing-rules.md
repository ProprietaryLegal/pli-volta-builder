# Standing rules, with their reasons

These hold in every phase. Each one exists because something went wrong without it, or because the owner of the
builds this skill comes from set it after watching the work. Where a rule quotes "the owner's rule", the words are
that person's. The failures behind the rules are told in `lessons.md`.

## Ownership and safety

1. **One owner per server and per card.** One session (the owner) boots, stops, signals and sends requests to a
   server and runs anything on its cards. Helpers (sub-agents, lanes) work on CPU, on copies of logs, or on a
   separate test machine the owner assigned to them, one owner per card there too. *Why:* two sessions acting on
   one server stop each other's arms, fake slowdowns with their own load, and leave nobody accountable for its
   state. Even a niced comparison job on the serving host was refused during a measuring window: CPU load on an
   overhead-bound engine shows up as a slower arm.
2. **The owner's word before anything is installed into a serving tree** (or a standing permission that covers
   it). Everything else (reading, CPU tests, planning, test windows) needs no word. *Why:* the serving tree is what
   users depend on. Owners often pre-authorize a whole sequence ("after the plan, build and install", "install
   everything that passes, in the right order"): write such a standing permission into `BUILD-STATE.md` with its date
   and limits, and do not ask again for what it covers.
2a. **Variants are separate builds; production is checkpointed.** Another precision, layout, engine or an extra card
   is its own build with its own tree, launch option or repository, never an edit of the build that serves; before
   any install, the serving build is frozen as a checkpoint that can be restored exactly; new work meets the small
   test machine first where one exists. *Why:* the owner must always be able to choose which build to launch, and
   each public page must describe one clean build.
3. **Test windows need no permission once the goal is set.** The goal "as fast as possible without losing
   quality" already answers "may I test A or B": decide, test, tell the owner afterwards. The owner's rule, in
   short: no permission is needed for a test window; the owner says so when every server is needed for other work.
   Other users and programs that depend on the server still get notice before a stop, and a window waits for an idle
   moment.
4. **Crash rule.** On a new Xid line in the kernel log or an unplanned host reset: stop nothing, start nothing,
   send nothing; report to the owner and wait for the owner's word. The driver ends any phase with exit 14 on an Xid
   change. *Why:* a card fault on old hardware can be a power supply, a riser, a hot card or a kernel bug; acting
   before a human looks can turn one fault into a lost board. A narrower written exception (for example: "after a
   power trip at a raised power cap, set the caps back and start again") is allowed only when the owner writes it.
5. **Power, clocks and hardware are the owner's.** Never change a power limit, clock cap, BIOS setting or cable
   without the owner's word. A power cap throttles SM clocks, not the HBM clock: prompt reading (compute) gains from a
   higher cap far more than decode (bandwidth) does.
5a. **The owner's four gates.** Stop and ask before: (1) changing any power, clock or other hardware setting;
   (2) stopping or restarting what other people or other programs use (notice to them; the owner's word unless a
   standing one covers it; a test on the test port or a server only the owner uses needs no ask); (3) publishing anything; (4) spending on a new download or new hardware.
   *Why:* in all three Volta builds these were the owner's decisions and nobody else's; automation, including
   `scripts/hill_climb.py` (its `owner_keys`), stops at them with WAITING-OWNER.
6. **Never edit a script a running job executes.** Install a new file under a new name and point the next chain
   at it; keep the old one as `<file>.before-<commit>`. *Why:* bash reads a script as it runs; an edit in place
   changes the running job's next lines.
7. **Kill only what you started, by exact PID or process group.** Never by pattern, never a session you did not
   start.
8. **No GPU identifiers in any file.** Select cards by UUID in private configuration, never print or commit a
   UUID or serial; files you may publish say "card 0 to 3" and "board A".

## Evidence

9. **Read upstream before planning, and never answer a capability question from first principles.** "Would FP4
   help on V100?" was once answered "no" from first principles while an upstream kernel ran NVFP4 at 77 % of the
   measured read ceiling on that very card. The owner's rule: if you design plans "with this little base knowledge,
   you're setting tokens on fire." Phase 1 makes the overlap table; every later plan row cites it.
10. **A rule is written before its data.** Every window's acceptance lines and predictions go into the plan's
    amendment log with a UTC time stamp before the window runs, and are not changed after. A wrong prediction
    stays recorded as wrong. *Why:* a line written after the data fits the data.
11. **INCONCLUSIVE is not a pass.** A check that cannot decide says INCONCLUSIVE, loudly, with the missing input
    named. "No violation found" and "could not check" are different results. Judges are strict: equal length,
    the full key set, a missing or repeated cell is INCONCLUSIVE.
12. **Fail fast; no retries, no fallbacks, no raised timeouts.** A timeout means something did not happen: find
    it. A failed boot is stopped and not booted again in the same window ("nothing is booted twice").
13. **Every pattern meets a real log first.** Before a check guards a window, every regex it applies to a boot's
    log runs against a real log of that kind of boot (`scripts/log_patterns.py certify`), and a new engine kit's
    new log lines go through every pattern of the driver. This rule exists because its absence stopped arms five
    times in one campaign.
14. **Label every number.** MEASURED (what hardware, what power limit, how many runs), UPSTREAM (whose, with the
    link and its conditions), ESTIMATE (the arithmetic shown). Never present an estimate or a plan as a result. A
    configuration that was not accepted says its quality is not established.
15. **Compare like with like.** Same window, same power limit, same boot day for speed; a reference in the arm's
    own arithmetic (or an independent higher-precision one) for quality when a change moves rounding on purpose.
    Speed bands are the measured spread between two runs of the unchanged build (A/A), not a guess
    (`scripts/speed_band.py`), with a floor: the adoption cutoff of 1.8 % of the reference (the owner, 2026-11-24).
    A gain under max(cutoff, spread) is within band and is not installed.
16. **Read the clock before stating a time** (`date -u`). Times were misstated from memory and had to be corrected
    from transcripts.
17. **A test tests what the user will use.** CPU tests go through the server's real entry point (two engine kits
    passed CPU tests that bypassed it and failed on the cards); acceptance lines that claim the workload are
    measured on the workload's shape (its context lengths, turns, concurrency), never on short prompts alone.
18. **Real workload in private measurements; public text in anything shared.** A measurement that claims the
    owner's workload replays the owner's real requests (or the closest replay of them) on the owner's own machines:
    that is what makes it count, and synthetic or anonymized stand-ins make it count less. Anything that will be
    published, and any window whose prompts, captures or logs will be shared, uses public text only (a language's
    standard-library source, public-domain law, public tasks). The owner's requests, the answers to them and any
    count derived from them never enter a published file.

## Pace and priorities

19. **Launch the proven recipe before validating pieces.** The owner's rule, after one campaign spent its budget on
    a bespoke runtime and per-primitive numerics checks while a working launch with the upstream recipe was minutes
    away: launch with the fork's documented flags, check a short completion and a long prompt, then iterate.
20. **Install what upstream measured; measure your own ideas first.** An optimization its author measured and
    documents as in use is installed on correctness and stability (it boots, answers, survives the long-prompt and
    memory rehearsal), then measured for the record. Your own ideas need their own window first. Assume an upstream
    number is right for the conditions it states; if your port misses it, suspect your port.
21. **Switch on what is proven.** Proven means: passed every line written for it, on the real cards, alone, and
    again in the whole configuration it will serve in (the `adopt` boot). A small-machine result, a CPU test or a
    model's prediction proves nothing in this sense. A window ends serving what it proved.
22. **Optimize the real workload's shape, not a benchmark.** Rank every candidate by seconds saved per task of the
    workload as measured (generated tokens, prompt lengths, turns, concurrency), and write acceptance lines for
    that shape.
23. **Persist until it works, without piling up checks.** An inconclusive or failed round is the start of the next
    hypothesis: name what killed it and launch the fix in the same hour. There is no round limit. But do not answer
    a failure by stacking another gate; read the whole result, find the cause, fix the cause. The owner noticed
    "a ton of repetitive conservative testing instead of actually searching for optimizations" and asked for the
    search.
24. **Keep the test machine busy.** An idle test card is a defect while candidates wait: put the next
    machine-testable item on it. Borrow public code before writing new code.
25. **Match model and effort to the task, within the owner's budget.** Default to the most economical model that
    does the job well; the strongest only where the job's difficulty warrants it. Launch only as many helpers as the
    owner's number allows, the work needs and you can monitor. Respect the owner's usage ceiling (pause all work when
    it is reached, if one is set) and the owner's report cadence (report when there is news, at the rate the owner asked).
26. **Report in the owner's terms.** What is built, what is tested, what is proven, what is optimized, what is
    next; numbers labelled; what failed and why.
27. **Publish when asked, after one privacy check.** One run of `scripts/boundary_check.py` with the owner's deny
    list plus one independent privacy read, then publish; fix wording afterwards. Do not hold a release behind
    rounds of wording review. The data boundary itself always blocks.
28. **State files so a new session can resume; hand-offs are explicit.** `BUILD-STATE.md` (where it stands, who
    owns what, what runs), the plan's amendment log, and a progress log with times. A session that ends mid-window
    leaves the next one able to finish it. When ownership moves (another session, another host): the old owner lets
    running helpers finish, starts nothing new, and writes a hand-off file (state, open windows, standing
    permissions, the owner's latest words, what not to touch); the new owner reads it in full, checks the live state
    against it, and acknowledges before acting; helpers report to the new owner from then on.
29. **Regression watch.** If the serving build becomes slower or wrong, stop routing work to it until its owner
    reports it fixed with a measured speed; find the change that did it from the install record.
30. **A test exists to decide something.** Launch the proven recipe first; once a question is decided, record it and
    move on. Do not re-prove a known result window after window; search for the next lever instead of re-measuring
    the last one.
