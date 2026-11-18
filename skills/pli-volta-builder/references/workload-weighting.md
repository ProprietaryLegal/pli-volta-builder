# Weighing candidates by what a whole task spends

Getting this wrong cost one campaign a day of ordering: decode was ranked low for a day while it was the largest item.
This page is the rule phase 5 and `scripts/timebudget_parse.py rank` / `scripts/hill_climb.py` apply.

## The rule

Rank every candidate by **seconds saved per task**:

    seconds saved per task = (time saved per unit) x (units per task)

where a unit is what the candidate makes faster (one decode round, one prompt chunk, one request's front end, one
turn) and units per task is MEASURED over whole tasks of the real workload:

| Unit | Units per task, measured as |
|---|---|
| decode round | generated tokens per task (answer AND reasoning, every request of the task summed) / tokens per round (from the server's counters at the workload's acceptance) |
| prompt chunk | rows read cold per task (first reads, reads after a cache miss) / chunk size |
| request front end | requests per task (every model request: the main chat, its checkers, its sub-agents) |
| turn on a grown chat | continued requests per task, by new-token size class |

Measure the per-task totals directly from per-task records (sum within each task, then take the median and the 90th
percentile of the sums). **Never multiply a median request count by a median answer length**: the product of
medians is not the median of the products, and long-tailed answers (reasoning, long drafts) make it far too small.
That is the exact mistake that under-weighted decode.

Rank by the median task and check the order holds at the 90th percentile; where it does not, say so and prefer the
order the owner's priorities name (for example, "never re-read a long context" first).

## Know the instrument's endpoints before reading a number

Before any figure from a log, a router or a client enters the weighting, write down what its two endpoints are:

- **Time to first byte** at the router may end at a protocol event (a header, a keep-alive ping) before any token.
- **Time to first token** at the client may include queueing for a slot and the stream's delivery.
- **Arrival to last byte** includes waiting for a slot, forwarding and delivery, not only the server's work.
- **"Prompt tokens" per request** is the request's whole prompt, not rows computed: with a prefix cache, a very long
  prompt may compute only a few hundred new rows. Rows computed must come from the engine's own hit and scheduled-row
  counters.
- **"New tokens" by subtraction** of successive prompt lengths is arithmetic, not an observation of what the engine
  read; confirm with the engine's hit depth.
- **Sum of per-request tok/s is not elapsed throughput** when requests overlap; report both.
- **Concurrency share** measured over a task's active model time leaves out idle tool time and other tasks' requests.

Write the endpoints next to each figure in the time-budget document. A number whose endpoints are unknown is
INCONCLUSIVE for ranking.

## Worked example (illustrative numbers, not anyone's real traffic)

A task generates 8,000 tokens in total; the drafter emits 2.0 tokens per decode round: 4,000 rounds per task. It
reads 100,000 tokens cold in 4,096-row chunks: 25 chunks. It makes 20 requests.

| Candidate | Saving per unit | Units per task | Seconds per task |
|---|---|---|---|
| decode kernel, -1.0 ms per round | 0.001 s | 4,000 | 4.0 |
| prompt chunk, -80 ms per chunk | 0.080 s | 25 | 2.0 |
| front end, -0.25 s per request | 0.25 s | 20 | 5.0 |

Had the decode units been taken as "20 requests x a median answer of 200 tokens / 2.0" = 2,000 rounds, the decode
kernel would have been ranked at 2.0 s, level with the prompt chunk, instead of 4.0 s.
