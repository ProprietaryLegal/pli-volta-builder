# Independent review of <build> at <commit>

You did not build this. Review it read-only: no server, no card, no write outside your own folder
`<reviewer folder>`, no messages to anyone but the owner.

## Read
The plan with every amendment (`documents/plans/PLAN.md`), the kernel and optimization plan, the time budget
(`research/TIME-BUDGET.md`), the harness (`window/`, `tools/`, `tests/`), the judges' code, these copies of receipts
and logs: <paths>, the workload's aggregate shape: <path>, AGENTS.md section 0 (the upstream table).

## Questions
1. What did we measure wrong? (A figure compared across conditions; totals compared where intervals overlap; a
   weight or unit taken from a product of medians; a speed claim inside the A/A band or under the 1.6 % cutoff.)
2. Which judge could pass something it should not? Try it: truncate an answer, drop a cell, repeat a key, edit a
   prompt at a boundary, feed a cold turn as a hit. Report each with a witness script and its output.
3. Which prediction rests on a figure that does not support it?
4. Which reference answers which question, and does each quality line use the right one?
5. What optimizations are we missing? Check upstream since our base (<commit/date>), the time budget's largest items,
   the workload's structure, idle hardware.
6. What is untested that the next window assumes?

## Report
`REPORT.md` in your folder: up to five findings for the owner first (each labelled RUN, MEASURED, READ or ESTIMATE,
with file and line references and a link to its evidence), then the detail. Put CPU evidence (scripts and outputs)
under `evidence/`. Do not soften: a finding the owner can re-run in a minute is worth more than ten opinions.
