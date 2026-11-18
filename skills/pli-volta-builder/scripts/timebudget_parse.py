#!/usr/bin/env python3
"""timebudget_parse.py : where the time goes, from profiler traces, and which candidate is worth the most.

A skeleton: it reads Chrome-trace JSON as the PyTorch profiler writes it ({"traceEvents": [...]}, complete events
with "ph": "X", "ts" and "dur" in microseconds, "cat" such as "kernel", "gpu_memcpy", "gpu_memset", "cuda_runtime",
"user_annotation"). Adapt the category and marker names to what YOUR engine's traces contain, and run every
pattern on a real trace first (scripts/log_patterns.py has the same rule for logs).

  timebudget_parse.py steps TRACE.json --marker REGEX [--host-calls cudaMalloc,cudaFree]
      For each user annotation whose name matches REGEX (one per engine step, e.g. a prompt chunk):
        step        the annotation's duration
        gpu busy    the UNION of kernel, copy and memset intervals inside the step
        gpu idle    step - gpu busy
        host calls  the UNION of the named runtime calls inside the step
        overlap     host calls INTERSECTED with gpu busy (time the card was working anyway)
        host-idle   host calls minus overlap: the most that removing those calls could save
      Prints per step and the medians.

  timebudget_parse.py kinds TRACE.json --map KINDS.json [--marker REGEX]
      Sums kernel time by kind; KINDS.json maps a kind to a regex over kernel names, first match wins
      ({"experts": "moe|qpn", "attention": "attn|flash", "allreduce": "nccl|allreduce"}); "other" collects the rest.

  timebudget_parse.py rank CANDIDATES.json
      Each candidate: {"name", "saving_s_per_unit", "units_per_task", "effort_days", "basis"}. Prints seconds saved
      per task (= saving x units) and per effort-day, ranked. "units_per_task" must come from the workload's
      MEASURED shape (decode rounds = generated tokens / tokens per round; prompt chunks; turns), not from
      requests x median answer.

Why intervals and not totals: in one campaign a hypothesis credited allocator calls with 16 to 19 % of a first read
by comparing their total time with the cards' idle total. Intersecting the intervals showed about half of that time
coincided with the cards working: the honest ceiling was about 9 %. The change was then measured on the cards at
+9.9 % on a 93,000-token read (MEASURED on a twelve-V100 server at 200 W, one run). Why measured units per task:
the same campaign first weighted its candidates by requests x median answer length and ranked decode too low; the
workload's generated tokens per task, counted directly, made one request's decode round the largest item.

`--self-test` checks the interval arithmetic and the ranking on hand-worked numbers.
"""
import argparse
import json
import re
import statistics
import sys

GPU_CATS = ("kernel", "gpu_memcpy", "gpu_memset")


def union(iv):
    """Merge [start, end) intervals; returns a sorted list of disjoint intervals."""
    out = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


def total(iv):
    return sum(e - s for s, e in iv)


def intersect(a, b):
    """Intersection length of two DISJOINT sorted interval lists."""
    i = j = 0
    acc = 0.0
    while i < len(a) and j < len(b):
        s, e = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if e > s:
            acc += e - s
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return acc


def clip(iv, s, e):
    return [(max(a, s), min(b, e)) for a, b in iv if min(b, e) > max(a, s)]


def events(path):
    doc = json.load(open(path))
    ev = doc["traceEvents"] if isinstance(doc, dict) else doc
    return [x for x in ev if x.get("ph") == "X" and "dur" in x]


def steps(ev, marker, host_calls):
    rx = re.compile(marker)
    marks = [x for x in ev if x.get("cat") == "user_annotation" and rx.search(x.get("name", ""))]
    gpu = [(x["ts"], x["ts"] + x["dur"]) for x in ev if x.get("cat") in GPU_CATS]
    host = [(x["ts"], x["ts"] + x["dur"]) for x in ev if x.get("cat") == "cuda_runtime" and x.get("name") in host_calls]
    rows = []
    for m in sorted(marks, key=lambda x: x["ts"]):
        s, e = m["ts"], m["ts"] + m["dur"]
        g, h = union(clip(gpu, s, e)), union(clip(host, s, e))
        busy, hc = total(g), total(h)
        ov = intersect(g, h)
        rows.append({"step": e - s, "gpu_busy": busy, "gpu_idle": (e - s) - busy, "host_calls": hc,
                     "overlap": ov, "host_idle": hc - ov})
    return rows


def kinds(ev, kmap, marker=None):
    rx = [(k, re.compile(v)) for k, v in kmap.items()]
    win = None
    if marker:
        m = [x for x in ev if x.get("cat") == "user_annotation" and re.search(marker, x.get("name", ""))]
        win = [(x["ts"], x["ts"] + x["dur"]) for x in m]
    out = {}
    for x in ev:
        if x.get("cat") != "kernel":
            continue
        if win and not any(s <= x["ts"] < e for s, e in win):
            continue
        k = next((k for k, r in rx if r.search(x.get("name", ""))), "other")
        out[k] = out.get(k, 0) + x["dur"]
    return out


def rank(cands):
    rows = []
    for c in cands:
        per_task = c["saving_s_per_unit"] * c["units_per_task"]
        rows.append((per_task, per_task / max(c.get("effort_days", 1), 1e-9), c["name"], c.get("basis", "")))
    return sorted(rows, key=lambda r: -r[1])


def self_test():
    bad = 0
    # Step from 0 to 100 us. GPU kernels [0,30) [20,50) [70,90) -> union [0,50) [70,90) = 70 busy, 30 idle.
    # Host calls [40,60) [80,100) -> 40. Overlap with GPU: [40,50) = 10 and [80,90) = 10 -> 20. Host-idle 20.
    ev = [{"ph": "X", "cat": "user_annotation", "name": "prefill_step", "ts": 0, "dur": 100},
          {"ph": "X", "cat": "kernel", "name": "moe_a", "ts": 0, "dur": 30},
          {"ph": "X", "cat": "kernel", "name": "attn_b", "ts": 20, "dur": 30},
          {"ph": "X", "cat": "gpu_memcpy", "name": "copy", "ts": 70, "dur": 20},
          {"ph": "X", "cat": "cuda_runtime", "name": "cudaMalloc", "ts": 40, "dur": 20},
          {"ph": "X", "cat": "cuda_runtime", "name": "cudaFree", "ts": 80, "dur": 20},
          {"ph": "X", "cat": "cuda_runtime", "name": "cudaLaunchKernel", "ts": 0, "dur": 5}]
    r = steps(ev, "prefill", {"cudaMalloc", "cudaFree"})[0]
    want = {"step": 100, "gpu_busy": 70, "gpu_idle": 30, "host_calls": 40, "overlap": 20, "host_idle": 20}
    ok = all(abs(r[k] - v) < 1e-9 for k, v in want.items())
    bad += not ok
    print("ok  " if ok else "FAIL", "steps:", r)
    # kinds: moe 30, attention 30, the memcpy is not a kernel
    k = kinds(ev, {"experts": "moe", "attention": "attn"})
    ok = k == {"experts": 30, "attention": 30}
    bad += not ok
    print("ok  " if ok else "FAIL", "kinds:", k)
    # rank: A saves 0.001 s per round x 5000 rounds = 5 s per task in 2 days -> 2.5 s/day;
    #       B saves 0.25 s per turn x 20 turns = 5 s per task in 1 day -> 5 s/day. B ranks first.
    rk = rank([{"name": "A", "saving_s_per_unit": 0.001, "units_per_task": 5000, "effort_days": 2},
               {"name": "B", "saving_s_per_unit": 0.25, "units_per_task": 20, "effort_days": 1}])
    ok = [x[2] for x in rk] == ["B", "A"] and abs(rk[0][0] - 5) < 1e-9 and abs(rk[1][1] - 2.5) < 1e-9
    bad += not ok
    print("ok  " if ok else "FAIL", "rank:", [(x[2], round(x[0], 3), round(x[1], 3)) for x in rk])
    print("timebudget_parse self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    s = sub.add_parser("steps")
    s.add_argument("trace")
    s.add_argument("--marker", required=True)
    s.add_argument("--host-calls", default="cudaMalloc,cudaFree")
    k = sub.add_parser("kinds")
    k.add_argument("trace")
    k.add_argument("--map", required=True)
    k.add_argument("--marker")
    r = sub.add_parser("rank")
    r.add_argument("candidates")
    a = p.parse_args(argv)
    if a.mode == "steps":
        rows = steps(events(a.trace), a.marker, set(a.host_calls.split(",")))
        if not rows:
            print(f"TIMEBUDGET INCONCLUSIVE: no annotation matches {a.marker!r} in this trace")
            return 3
        for i, row in enumerate(rows):
            print(f"step {i}: " + ", ".join(f"{k} {v / 1000:.2f} ms" for k, v in row.items()))
        print("medians: " + ", ".join(f"{k} {statistics.median(r[k] for r in rows) / 1000:.2f} ms" for k in rows[0]))
        return 0
    if a.mode == "kinds":
        out = kinds(events(a.trace), json.load(open(a.map)), a.marker)
        if not out:
            print("TIMEBUDGET INCONCLUSIVE: no kernel events")
            return 3
        tot = sum(out.values())
        for name, us in sorted(out.items(), key=lambda x: -x[1]):
            print(f"{name}: {us / 1000:.2f} ms ({100 * us / tot:.1f} %)")
        return 0
    for per_task, per_day, name, basis in rank(json.load(open(a.candidates))):
        print(f"{name}: {per_task:.2f} s per task, {per_day:.2f} s per task per effort-day ({basis})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
