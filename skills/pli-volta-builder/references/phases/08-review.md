# Phase 8: Independent review

**When:** after the time budget and before the first optimization window that adopts anything; then every few
windows, and whenever the owner asks; always before a public release.

**Why:** the people (or sessions) who built the harness share its blind spots. In the twelve-card campaign one
read-only review found, in under an hour: a token cache that returned wrong ids on an edit at its cut (the tests had
missed it), equality judges that passed truncated answers, set judges that passed with cells missing, a workload
weighting that under-counted decode, and a hypothesis whose size was double what interval analysis allowed. Each
finding changed the plan; none had been visible from inside.

## Do

0. The reviewer researches first: the card's architecture, the engine fork's pull requests and the kernel
   repositories (`../upstream-sources.md`), so its findings rest on the same base knowledge the build should have.
1. Choose a reviewer that did not build it: another model or another person, at high effort, READ-ONLY (no server,
   no card, no write outside its own folder).
2. Hand it the whole record (`templates/REVIEWER-BRIEF.md`): the plan with every amendment, the time budget, the
   harness code and judges, the receipts and logs it may read (copies), the workload's aggregate shape, the
   upstream table. Ask: "What did we measure wrong? What are we missing? Which judge could pass something it should
   not? Which prediction rests on a figure that does not support it?" Ask for CPU evidence (a witness script and its
   output) for each finding.
3. **The owner re-runs or re-reads each finding before acting on it,** and writes in the next amendment which
   findings were re-run, which read, and what changes. A finding is evidence to check, not an order.
   Ask also, separately: every lever upstream claims as a win that this build measured as a loss or no gain. Scrutinize
   those hardest: was the port faithful, was the measurement able to see the gain, did a condition differ? "Re-checked,
   the loss stands, no basis to retry" is a valid answer; write it next to the loss in the lever table.
4. Act: fix judges before the next window; re-check historical results the finding touches (keep those that stand,
   say so); re-rank the candidate list; hold a change until its boundary case is proven.

## Writes

`documents/reviews/REVIEW-<date>.md` (the reviewer's report, without private material), the amendment recording what
was acted on, the fixes.

## Gate

The next adopting window runs only after the judge findings are fixed and the fixed judges have met real receipts.
