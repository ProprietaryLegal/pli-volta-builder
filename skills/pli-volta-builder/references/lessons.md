# Lessons: what failed, and what each taught

Told generically. Every lesson happened in the campaigns that built three DeepSeek-V4.1-Flash servers on Tesla V100
cards (Volta sPLIt and Volta Max uPLIft on eight cards in two stages, Volta 12X AmPLIfy on twelve cards in three
stages). Figures are MEASURED on those servers unless labelled. Read this before you design a harness or a window;
each lesson is already encoded in a rule (`standing-rules.md`) or a script.

## Checks that had never met a real log

| # | What happened | What it cost | Rule now |
|---|---|---|---|
| 1 | The out-of-memory pattern matched the card limit's own start-up announcement ("... out of memory ...") and refused a good boot | a second boot in that window | every pattern runs on a real log first; `except` lines in `log_patterns.py` |
| 2 | A new engine kit printed a second "rank ready" line per worker; the driver counted ranks and found twice too many | the window stopped at its first boot | a new kit's new log lines go through every pattern of the driver before the window |
| 3 | The witness that proved a switch was set read each worker's `/proc/<pid>/environ`; the engine renames its worker processes (process titles), which blanks that file | an arm with no verdict | read the leader process's environment, or have the engine log the switch it read |
| 4 | A time-budget probe replayed earlier answers without their reasoning text, so the next turn's prompt did not begin with the stored prompt and every "turn" was read cold | a whole set of turn timings void | a probe's turns must reuse the exact rendered prompt, reasoning included; check prefix hits in the server log |
| 5 | The engine warns once about every environment variable it does not know ("Unknown ... environment variable"); a witness treated the warning as a failure | an arm stopped 2.5 minutes in, nothing measured | expect exactly that warning for each new unregistered switch; certify on real logs |

Five stops of this kind in one campaign. A CPU test with synthetic logs found none of them. Hence
`scripts/log_patterns.py certify` on real logs of the same kind of boot, every time a pattern or a kit changes.

## Judges that passed what they should not

- **The equality judge compared answers only through the shorter one.** An answer cut short of its reference
  counted as identical. An independent review removed one token from each of twelve real reference answers and the
  judge said "identical 12 of 12". The historical identity results were re-checked on whole sequences (they stood),
  and both judges were made strict: equal length, equal key set, a missing, extra or repeated key INCONCLUSIVE.
  `scripts/identity_judge.py` is that judge.
- **A set judge passed with cells missing.** One acceptance line passed with one of four required read sizes
  measured; a mixed-turn aggregate counted turns of unknown prefix status as hits; a repeat check compared text
  digests instead of token ids. Fixed by a full expected key set per variant and "unknown is INCONCLUSIVE".
- **A speed floor accepted one pass of two.** The floor must say which passes it needs.

## A cache that was wrong only at its edge

The API server re-tokenized the whole rendered prompt on every request: about 2 microseconds per token on
the serving host's CPU, a quarter of a second at 120,000 tokens before the scheduler even saw the request (MEASURED
on CPU with the build's own tokenizer). A prefix token cache reused the ids of the longest shared prefix up to the
last special token and tokenized only the rest. Its tests passed (209 of 209 cuts at special tokens, 80 of 80
continued requests). An independent review then edited a message AT the delimiter: the cache hit, returned the
right NUMBER of ids and the wrong SEQUENCE. A line that compared `prompt_tokens` counts could never have seen it.
The repair: a cut is usable only if the whole special token lies in the text both prompts share, and the cache
checks the tokenizer's premises at start (added tokens matched on raw text first, none strips neighbours, empty
normalizer) and refuses the switch otherwise. Proof: a fuzz of 3,200 chained edits, most within a few characters of
a delimiter, 0 sequences different from a full encode. Lessons: test edits at the boundary, compare whole id
sequences, and require real hits in the verify run (a run of misses compares a full encode with itself).

## The workload's weights were wrong

The first ranking weighted a task as (requests per task) x (median answer length) and concluded decode was a small
share. The review counted generated tokens per task directly (reasoning included) and found them far
above that product: one request's decode round became the largest item, and each millisecond off a round is worth
seconds per task. Rule: units per task come from the workload's measured totals, not from products of medians.

## A prediction halved by interval analysis, then confirmed on the cards

Profiler totals showed the host spending 163 to 187 ms per 4,092-row prompt step in `cudaMalloc`/`cudaFree` while
cards idled 164 to 203 ms; the hypothesis credited the allocator-cache release after each step with 16 to 19 % of a
first read. Intersecting the intervals (`scripts/timebudget_parse.py steps`) showed about half of that host time
coincided with the cards working: the ceiling was about 9 %. The window then measured raising the release threshold
above the chunk size at +9.9 % on a 93,000-token read, +12.6 % on 60,700, +2.8 % at 248,000 (where the index
dominates), identical answers 7 of 7, and no higher memory peak (MEASURED, twelve V100s at 200 W, one boot each).
Lesson: intersect intervals; never compare totals of overlapping things.

## A scheduler that was right at two stages and wrong at three

The first three-stage boot answered wrongly: 15 of 15 answers differed, junk from token 1. Running the real engine
loop on CPU found it: under synchronous scheduling nothing spaced a request's decode steps by the pipeline depth;
at two stages the call sequence happened to arrive on time, at three the first stage embedded the previous request's
tokens. Fix: a request's next decode step waits `pp_size` steps; a stall guard of `max(2, pipeline depth)`. A CPU
test of the call sequence (17 of 28 cases fail before the fix, all pass after) now guards it. Lesson: when a layout
changes depth, re-derive every timing assumption; run the real loop on CPU before a card.

## Same bytes, different answers on a small test bed

On a one-stage four-card bed with experts partly in host memory, two boots of the same engine bytes gave different
greedy tokens on three of five kinds of prompt; inside one boot everything repeated exactly. Comparing a change
across boots there read as "the change alters answers" and cost three boots. Rule: boot the same bytes twice before
judging identity across boots; if they differ, judge the change inside one boot (a pause switch: off, on, off, on).
The large build repeated across boots; check yours.

## Microbenchmarks mislead in both directions

A decode kernel predicted 0.03 ms by its microbenchmark saved 0.42 ms end to end; a fused plan slightly slower in its
microbenchmark saved 0.36 ms in an ABBA run. Under graph replay, kernels start about 0.3 microseconds apart and
profiled small kernels read about 1.8 times long: size a fusion from the kernel time it removes. Only the end-to-end
ABBA decides; never drop a lever on a microbenchmark alone.

## Other lessons, briefly

- **More slots are not more speed when a step carries one request.** Four slots gave about the same sum as three on
  the pipelined build; the fourth slot's value is keeping a fourth chat's context warm. Sum of per-request rates is
  not elapsed throughput: report both.
- **A rule mis-scaled to its reference closed a good arm.** A closeness line copied from a two-stage reference onto
  a three-stage arm could not be met by construction. Lines are written against a reference the arm can meet.
- **A cache release at 512 rows lost**: same memory peak, larger turns' first token twice as slow. Losses are
  recorded with numbers so nobody re-proposes them.
- **Async scheduling on a two-stage V100 pipeline cost a third of decode speed** (UPSTREAM, 1Cat-vLLM issue #852).
- **A reference arm must use the build's own engine**, or a "difference" may be the engine copy, not the change.
- **Upstream was re-built by accident.** One campaign wrote an FP8-dense patch that duplicated an open upstream pull
  request; another nearly shipped a drafting mode upstream had measured as worse. The overlap table prevents both.
- **A slowdown nobody caught.** A change once made the serving build much slower and the owner noticed before the
  campaign did. Keep a regression cell (one short and one long request, timed) in every serving check.
