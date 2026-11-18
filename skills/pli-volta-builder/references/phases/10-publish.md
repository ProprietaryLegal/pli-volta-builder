# Phase 10: Document and publish

**Entry:** any time the build reaches a state worth keeping; publishing only on the owner's word.

## The formal repository (the structure the PLI Volta builds use)

| File | Holds |
|---|---|
| `README.md` | What the build is, the measured headline figures with conditions, how to run it, the hardware, credits, the byline |
| `AGENTS.md` | Rules for every agent: section 0 front-line facts with the overlap table (`templates/AGENTS.md`), the build's place on the host, the data boundary, git, reporting, the operating rules |
| `CLAUDE.md` | The pinned sections, copied verbatim from AGENTS.md and checked equal by a test: "Building kernels", "Upstream sources", "Kernel research records", "Lever status" (`templates/CLAUDE.md`) |
| `documents/plans/PLAN.md` | Layout arithmetic, the kit, the windows, section 9's amendments (rule, prediction, result) |
| `documents/plans/KERNEL-AND-OPTIMIZATION-PLAN.md` | Where the build stands, the method, the time budget's step 0, the tiers, the closed list, the order of work |
| `docs/OPERATIONS.md` | Who may do what, ports, start/stop/move, the full check, the crash rule, tools, tests, logs, lessons that are rules |
| `docs/measurements.md` | Every figure with its window, power limit, run count |
| `docs/history.md` | Each window in a few lines: what was tried, what happened |
| `docs/ARCHITECTURE.md` | The layout, the kit, the data flow |
| `research/` | The research copied in with origin and sha256 per file (`PORT-MANIFEST.tsv`) |
| `CREDITS.md`, `LICENSE`, `NOTICE` | Every upstream used, by public handle and link; licences of copied files |

## Publishing (only on the owner's word)

1. A separate public tree: never push a private working repository's history.
2. Leave out: host names, private paths, IP addresses, GPU identifiers, session and agent names, credentials, e-mail
   addresses, user or client text, generated model text, figures about anyone's real traffic, per-expert usage
   counts, logs, weights, captures. Describe hardware generically ("a twelve-V100 server").
3. Every number labelled; a configuration that was not accepted says its quality is not established; no sentence
   claims a test mirrors anyone's real use.
4. Third parties by public handle, linked, with what is theirs stated plainly.
5. `scripts/boundary_check.py <tree> --deny <private deny list>` (the deny list lives outside the tree), plus one
   independent privacy read. Then publish and give the owner the link. Fix wording in follow-up commits; do not hold
   the release for review rounds.

## The public page (the order owners of these builds asked for)

1. **Speed headline first**: decode tok/s for one request (and several together, if concurrency is on) by content
   type, at the context lengths users run, and the longest context that works. Then the long-prompt table (prompt
   reading and first token at each length). Then accuracy (closeness to the reference, with the reference named).
   Short; detail and history move to other files; sections that do not apply are removed.
2. **Describe the build on its own.** Never score one of the owner's builds against another in public text (no "x
   faster than our other build", no "slower than"). A build's own before and after, its own configurations, and
   upstream's figures with their sources are fine.
3. **Name:** offer about five names in the pattern the owner's earlier builds use; the owner picks.
4. **Byline:** the owner's byline and site link on every page, card and model upload, exactly as on the earlier ones.
5. **Upstream:** send the wins AND the failed attempts to the engine fork and the kernel repository, as pull requests
   or issues with their measured numbers and conditions, so others can build on them; check those pull requests'
   status later and answer reviews.
6. **Maintain** the public repository: fix simple reported issues; keep the figures current after a close-out bench.
7. **Posts** (forums, social media) only when the owner asks, in the owner's voice, as past posts show it, and none
   when the owner says not to.

## Writes

The formal repository, the public tree when ordered, the hub entry (a link and a summary).
