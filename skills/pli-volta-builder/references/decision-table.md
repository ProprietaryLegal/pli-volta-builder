# Decision table

Common situations, and what the PLI Volta campaigns did. When a row says "owner", the decision belongs to the person
who owns the hardware; tell the owner the numbers and wait only where the row says so.

| Situation | Do | Do not |
|---|---|---|
| A capability question ("would FP4 help on Volta?", "can sm_70 run this kernel?") | Read `volta-facts.md` and the upstream pull requests; answer with the source | Answer from first principles |
| The model does not fit the cards at the precision wanted | Phase 2 arithmetic: per-card bytes per layer, legal stage cuts; options: more cards, compress the least-used parts, hold part in host memory (slow, exact), fewer slots, shorter context | Download another model or quant without the owner's word |
| Several layouts fit | Prefer tensor parallel inside a board, pipeline across boards; the fewest stages that fit with margin; then measure the top two | Pick by a microbenchmark |
| An upstream pull request already measured the lever on equivalent hardware | Install it on correctness and stability (boots, identity or closeness, rehearsal), measure for the record | Re-test it as if it were your own idea for days |
| Your own idea, untested | Phase 6: amendment, default-off switch, CPU tests through the entry point, small-machine rehearsal, one window | Switch it on because a model predicts a gain |
| A line comes back INCONCLUSIVE | Name the missing input; fix that (the judge, the reference, the probe); run again in the next window | Count it as a pass; or quietly drop the line |
| A prediction was wrong | Record it as wrong in the result amendment; update the model of where time goes | Rewrite the prediction |
| A change moves rounding on purpose (another split count, another reduction order) | Judge by closeness against a reference in its own arithmetic, or teacher-forced decisions; tell the owner it moves tokens | Judge it by identity against the old arithmetic (it can never pass) |
| Two candidates conflict (both touch the same code or memory) | Test each alone, then stacked; keep the faster with quality held; record the conflict | Ask the owner "A or B?" when the goal already answers it |
| A new Xid line or an unplanned reset | Stop nothing, start nothing, send nothing; report; wait for the owner | Restart to "see if it happens again" |
| A boot fails in a window | Stop that arm; the chain goes on or returns to serving; no second boot of it in this window | Retry the boot |
| The serving record does not match the trees | Run the full check on the test port first | Boot the public port on hope |
| A check's pattern is new or a kit adds log lines | `log_patterns.py certify` on real logs of that boot kind | Trust a CPU test with synthetic logs |
| The plan runs dry | Phase 9 research; an independent review (phase 8) | Re-run the same windows for more decimal places |
| Speed difference near the band | ABBA in one window; report "within band" if it stays inside max(the A/A spread, the 1.6 % cutoff) | Call a win from one run; adopt a gain under 1.6 % because it beat the spread |
| The small test machine shows a gain | Order the big window by it | Adopt on it |
| Several requests at once are rare in the workload | Rank single-request latency and decode first; batched decode last | Optimize the sum over many requests because a benchmark does |
| The owner asks to publish | One boundary check with the owner's deny list and one privacy read, then publish; fix wording after | Hold it for review rounds |
| A sub-agent is useful | Brief it (`templates/LANE-BRIEF.md`) for CPU work or an assigned test card; it reports to the owner | Let it touch the serving server |
| A test port or a server only the owner uses | Run the window; tell the owner the result | Ask permission for each window |
| Stopping a server other people or programs use | Give them notice, wait for an idle moment; the owner's word unless a standing one covers it | Stop it mid-request |
| The owner gave a standing permission | Write it in BUILD-STATE.md with its date and limits; act on it | Ask again for what it covers |
| A variant of the serving build (precision, layout, engine, extra card) | A separate build and launch option; checkpoint production first | Edit the serving build in place |
| The serving build got slower or wrong | Stop routing work to it until its owner reports a measured fix | Keep sending work and hope |
| The model does not fit at the wanted precision, MoE | Mixed precision by measured expert use (`expert-promotion.md`) | Compress every expert the same way without asking why |
| A result is already decided | Record it; search for the next lever | Re-prove it next window |
| Idle test cards | Put the next machine-testable candidate on them | Leave them idle while candidates wait |
