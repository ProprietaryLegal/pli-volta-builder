# BUILD-STATE: <build name>

Updated <date -u>. A new session reads this first, then PLAN.md section 9 (newest amendment last), then the progress
log's last entries. Keep it to one screen.

## Now
- Phase: <0-10> (<name>). Next step: <one line, with the command or file>.
- Serving: <yes/no>, configuration <name>, port <serve port>, since <time>, from serving record <digest> (MATCH/STALE).
- Test port: <port>, in use by <nothing / window TAG arm ARM>.
- Window running: <none / TAG, chain, started at>.
- Xid count at last read: <n> (<time>).

## Objectives, bars and standing permissions (phase 0; the owner's words, dated)
- What matters first: <decode / thinking decode / prompt reading / first token / several together / context / quality>.
- Bars: one-request decode <tok/s>; minimum context <tokens>; default concurrency <n> and the single-request cost
  accepted for it <percent>.
- Standing permissions: <"test windows need no ask" (date)>, <"install what passes, in this order" (date, limits)>,
  <"publish at close-out" (date)>.
- Reports: <format, cadence>; usage ceiling: <...>; helpers allowed: <n>.

## Hardware readiness (phase 0b)
| Card | Board | Link now / capable | NVLink | Temp under load | Faults |
|---|---|---|---|---|---|
- Power budget per supply and circuit: <...>. Hardware levers proposed / applied by the owner / measured: <...>.

## Owner and helpers
- Owner of the server and its cards: <session or person>. Only the owner boots, stops, sends requests, runs on cards.
- Helpers and what each may touch: <name: CPU only / test machine cards 0-3 / read-only>.
- The hardware owner's standing words that apply (quoted, with dates): <...>.

## Hardware (phase 0)
- Cards: <n x model, memory>; boards and links: <...>; host RAM: <...>; power/clock: <...> (owner's).
- Memory line: <MiB> per card (the most a card may hold under serving).
- UNKNOWN, and how to settle each: <...>.

## Model and layout (phases 0, 2)
- Model: <name, revision>; formats: <...>; layout: <stages x TP, cuts, residency>.

## Workload shape (phase 0; aggregates only)
- Prompt length p50/p90/max: <...>; new tokens per turn p50/p90: <...>; generated tokens per task: <...>;
  concurrency shares: <...>; prefix continuation share: <...>. Source: <measured / assumed>.

## Standing configuration and figures
- Kit <name/commit>, profile <file>, switches <...>, slots <n>, context <n>, memory limit <MiB>.
- MEASURED (<window>, <power>, <runs>): one request <tok/s, ms/round>; together <...>; prompt read <tok/s>; peak card
  <MiB>.

## Open items (ranked; from the kernel and optimization plan)
1. <candidate> <size in s/task> <state>

## To run on the machine (when this session has no access)
- <exact commands, in order, with what each writes>
