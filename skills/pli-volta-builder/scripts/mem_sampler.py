#!/usr/bin/env python3
"""mem_sampler.py : card memory high-water marks, sampled during a rehearsal and judged against a written line.

  mem_sampler.py sample OUT.csv [--every-ms 500]
      Live (the server's owner only, while a rehearsal runs): appends "unix_time,index,used_mib" rows from
      `nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits` until stopped (Ctrl-C or SIGTERM).
      It asks for the card INDEX only: never write GPU UUIDs or serial numbers into a file you may publish.

  mem_sampler.py judge OUT.csv --cards 12 --stages 0-3,4-7,8-11 --line 31998 [--max-gap-s 5]
      Reads the samples and prints the highest sample per card and per stage, then:
        PASS           every card sampled, no gap longer than --max-gap-s in any card's series, highest <= line
        FAIL           a card's highest sample is above the line
        INCONCLUSIVE   a card was never sampled, or a gap longer than --max-gap-s (a sampler that stalled can miss
                       the peak), or no rows. Never a pass.

Why a rehearsal and not a short test: memory grows with what the workload does (several long chats open at once,
each slot's state, graphs, allocator caching). The rehearsal must be shaped on the real workload: one grown chat
per slot at the context lengths users reach, the turns they send. A line is written before the data: the most a card
may hold under serving, below the physical card size by a margin the owner sets.

`--self-test` judges hand-made samples.
"""
import argparse
import csv
import signal
import subprocess
import sys
import time


def parse_stages(spec):
    stages = []
    for part in spec.split(","):
        lo, hi = part.split("-")
        stages.append(list(range(int(lo), int(hi) + 1)))
    return stages


def judge(rows, cards, stages, line, max_gap_s):
    series = {}
    for t, idx, used in rows:
        series.setdefault(idx, []).append((t, used))
    out = []
    missing = [i for i in range(cards) if i not in series]
    if not rows or missing:
        return "INCONCLUSIVE", [f"no samples for card(s) {missing}" if rows else "no samples"]
    gaps = []
    for i, s in series.items():
        s.sort()
        g = max((b[0] - a[0] for a, b in zip(s, s[1:])), default=0.0)
        if g > max_gap_s:
            gaps.append(f"card {i}: a gap of {g:.1f} s")
    high = {i: max(u for _, u in s) for i, s in series.items()}
    for n, st in enumerate(stages):
        out.append(f"stage {n}: highest {max(high[i] for i in st)} MiB (cards {st[0]}-{st[-1]})")
    top = max(high.values())
    out.append(f"highest card sample {top} MiB against the line {line} MiB ({line - top:+d} MiB)")
    if top > line:
        return "FAIL", out + [f"MEMORY FAIL: card(s) {[i for i, h in high.items() if h > line]} above the line"]
    if gaps:
        return "INCONCLUSIVE", out + gaps + ["MEMORY INCONCLUSIVE: the sampler stalled; the peak may be missed"]
    return "PASS", out + ["MEMORY PASS"]


def read_rows(path):
    rows = []
    with open(path) as f:
        for r in csv.reader(f):
            if len(r) == 3:
                rows.append((float(r[0]), int(r[1]), int(float(r[2]))))
    return rows


def sample(out, every_ms):
    stop = []
    signal.signal(signal.SIGTERM, lambda *a: stop.append(1))
    with open(out, "a") as f:
        while not stop:
            t = time.time()
            res = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, check=True)
            for line in res.stdout.strip().splitlines():
                idx, used = (x.strip() for x in line.split(","))
                f.write(f"{t:.3f},{idx},{used}\n")
            f.flush()
            time.sleep(every_ms / 1000)
    return 0


def self_test():
    bad = 0
    st = parse_stages("0-1,2-3")
    rows = [(0, 0, 100), (0, 1, 120), (0, 2, 90), (0, 3, 95),
            (1, 0, 150), (1, 1, 110), (1, 2, 200), (1, 3, 95)]
    # highest: card0 150, card1 120, card2 200, card3 95 -> stage0 150, stage1 200; top 200 <= 250 -> PASS
    v, lines = judge(rows, 4, st, 250, 5)
    bad += v != "PASS" or "stage 1: highest 200" not in lines[1]
    print("ok  " if v == "PASS" else "FAIL", lines[-2])
    # line 180: card 2 at 200 > 180 -> FAIL
    v, lines = judge(rows, 4, st, 180, 5)
    bad += v != "FAIL"
    print("ok  " if v == "FAIL" else "FAIL", lines[-1])
    # card 3 never sampled -> INCONCLUSIVE
    v, lines = judge([r for r in rows if r[1] != 3], 4, st, 250, 5)
    bad += v != "INCONCLUSIVE"
    print("ok  " if v == "INCONCLUSIVE" else "FAIL", lines[-1])
    # a 10 s gap in every series with max_gap 5 -> INCONCLUSIVE even though under the line
    v, lines = judge([(t * 10, i, u) for t, i, u in rows], 4, st, 250, 5)
    bad += v != "INCONCLUSIVE"
    print("ok  " if v == "INCONCLUSIVE" else "FAIL", lines[-1])
    print("mem_sampler self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    s = sub.add_parser("sample")
    s.add_argument("out")
    s.add_argument("--every-ms", type=int, default=500)
    j = sub.add_parser("judge")
    j.add_argument("csv")
    j.add_argument("--cards", type=int, required=True)
    j.add_argument("--stages", required=True)
    j.add_argument("--line", type=int, required=True)
    j.add_argument("--max-gap-s", type=float, default=5.0)
    a = p.parse_args(argv)
    if a.mode == "sample":
        return sample(a.out, a.every_ms)
    v, lines = judge(read_rows(a.csv), a.cards, parse_stages(a.stages), a.line, a.max_gap_s)
    print("\n".join(lines))
    return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 3}[v]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
