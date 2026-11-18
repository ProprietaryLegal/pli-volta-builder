# Brief for helper <NAME>: <one-line task>

You are a helper of the owner session <owner> on <build>. Read, in order: the build's AGENTS.md (section 0 in full,
and section 6), CLAUDE.md, BUILD-STATE.md, PLAN.md section 9's last three amendments, then this brief.

## The task
<What to produce, in one paragraph. The size it is expected to win, from the time budget, and the overlap-table rows
it touches (adopted / partly / not / duplicates).>

## What you may touch
- Read: <paths>. Write: only <your folder> (and a branch `<exp/NAME-slug>` in a worktree if granted).
- Cards: <none / the test machine's cards 0-3 only>. You never boot, stop or signal the serving server, send it a
  request, or run anything on its cards. If you need that, ask the owner with SendMessage (or your channel) and wait.
- No pushes, uploads, e-mail or other external side effects.

## How you work
- Upstream first: start from the named upstream code; say what you took.
- Every new path behind a default-off switch; the off path unchanged.
- Tests go through the server's real entry point (name it); expected values from arithmetic, a specification or a
  real observation, never recorded from your own code. Run every log pattern you write on the real logs at <path>.
- Fail fast; no retries, fallbacks or raised timeouts. A check that cannot decide says INCONCLUSIVE.
- Keep `<NAME>.progress.md` (resumable; times from `date -u`).

## Deliver
A patch or kit folder with MANIFEST (sha256 of every file), the tests and their output, and a report to the owner:
verdict first; what works (with commands); measured numbers labelled MEASURED / ESTIMATE / UPSTREAM; what does not
(exact error); the list of pieces that have never met a server; open questions.
