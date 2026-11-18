#!/usr/bin/env python3
"""log_patterns.py certify PATTERNS.json LOG [LOG ...] : run every pattern a check will apply to a boot's log
against REAL logs of that kind of boot, BEFORE the check guards a window.

PATTERNS.json is a list of patterns the driver or a witness uses:
    [{"name": "ranks",  "regex": "TP rank \\d+ ready", "expect": 12},
     {"name": "oom",    "regex": "(?i)out of memory", "expect": 0, "except": "card limit set to"},
     {"name": "unknown-env", "regex": "Unknown .* environment variable", "expect": "any"}]
  expect   an integer (exact count per log), "any" (report only), or ">=N".
  except   an optional regex; a line that matches it is not counted (a line the pattern must NOT catch, such as
           the card limit's own announcement that contains the words "out of memory").

certify prints, per log and pattern, the count and up to three matching lines, and ends
    CERTIFIED     every pattern met its expectation on every log
    NOT CERTIFIED with the patterns that did not (exit 1)
    INCONCLUSIVE  a log is empty or unreadable, or no pattern file entry (exit 3)
A pattern that has never matched a real log line is listed as UNTESTED unless its expectation is 0, so a
pattern that can never fire is visible.

Why: in one campaign a check that had never met a real log stopped a test arm five times: an out-of-memory
pattern matched the card limit's own announcement; a new kit printed a second "rank" line per worker and doubled the
rank count; process titles blanked the workers' /proc environment the witness read; a probe replayed answers
without their reasoning so every turn was read cold; an engine warning about an unregistered environment variable
failed a witness. Each cost a boot. Run this on copies of real logs, on a machine that is not serving.

`--self-test` runs hand-made logs through hand-counted patterns.
"""
import json
import re
import sys


def count(pattern, lines):
    rx = re.compile(pattern["regex"])
    ex = re.compile(pattern["except"]) if pattern.get("except") else None
    hits = [l for l in lines if rx.search(l) and not (ex and ex.search(l))]
    return hits


def meets(expect, n):
    if expect == "any":
        return True
    if isinstance(expect, str) and expect.startswith(">="):
        return n >= int(expect[2:])
    return n == int(expect)


def certify(patterns, logs):
    """logs: {name: [lines]}. Returns (verdict, lines). Pure."""
    out = []
    if not patterns:
        return "INCONCLUSIVE", ["no patterns given"]
    for name, lines in logs.items():
        if not lines:
            return "INCONCLUSIVE", [f"{name}: empty or unreadable log"]
    failed, ever = [], {p["name"]: 0 for p in patterns}
    for lname, lines in logs.items():
        for p in patterns:
            hits = count(p, lines)
            ever[p["name"]] += len(hits)
            ok = meets(p.get("expect", "any"), len(hits))
            if not ok:
                failed.append(f"{p['name']} on {lname}")
            out.append(f"{lname}: {p['name']}: {len(hits)} (expect {p.get('expect', 'any')}) {'ok' if ok else 'MISMATCH'}")
            for h in hits[:3]:
                out.append(f"    | {h.rstrip()[:200]}")
    untested = [n for n, c in ever.items() if c == 0 and next(p for p in patterns if p["name"] == n).get("expect") not in (0, "0")]
    for n in untested:
        out.append(f"UNTESTED: pattern {n!r} matched no line of any real log")
    if failed:
        out.append("NOT CERTIFIED: " + "; ".join(failed))
        return "NOT CERTIFIED", out
    if untested:
        out.append("NOT CERTIFIED: untested pattern(s) " + ", ".join(untested))
        return "NOT CERTIFIED", out
    out.append("CERTIFIED: every pattern met its expectation on every real log")
    return "CERTIFIED", out


def self_test():
    log = [
        "INFO worker 0: TP rank 0 ready\n",
        "INFO worker 1: TP rank 1 ready\n",
        "INFO card limit set to 31998 MiB (out of memory guard)\n",
        "WARNING Unknown engine environment variable detected: ENGINE_NEW_SWITCH\n",
        "INFO worker 1: TP rank 1 ready (second line from a new kit)\n",
    ]
    bad = 0
    # ranks: lines 1, 2 and 5 match "TP rank \d+ ready" -> 3, expected 2 -> NOT CERTIFIED (the doubled-rank lesson)
    v, lines = certify([{"name": "ranks", "regex": r"TP rank \d+ ready", "expect": 2}], {"boot": log})
    bad += v != "NOT CERTIFIED" or "ranks: 3" not in lines[0]
    print("ok  " if v == "NOT CERTIFIED" else "FAIL", "doubled rank line:", lines[0].strip())
    # oom without except: line 3 matches -> 1, expected 0 -> NOT CERTIFIED (the false out-of-memory lesson)
    v, lines = certify([{"name": "oom", "regex": "(?i)out of memory", "expect": 0}], {"boot": log})
    bad += v != "NOT CERTIFIED"
    print("ok  " if v == "NOT CERTIFIED" else "FAIL", "oom pattern catches the limit's announcement:", lines[0].strip())
    # oom with except "card limit set to": 0 hits -> CERTIFIED
    v, lines = certify([{"name": "oom", "regex": "(?i)out of memory", "expect": 0, "except": "card limit set to"}], {"boot": log})
    bad += v != "CERTIFIED"
    print("ok  " if v == "CERTIFIED" else "FAIL", "oom pattern with exception:", lines[-1])
    # the unregistered-variable warning, expected exactly once when the switch is set -> CERTIFIED
    v, lines = certify([{"name": "unknown-env", "regex": "Unknown .* environment variable", "expect": 1}], {"boot": log})
    bad += v != "CERTIFIED"
    print("ok  " if v == "CERTIFIED" else "FAIL", "expected warning:", lines[0].strip())
    # a pattern that never matches anything with expect ">=1" -> NOT CERTIFIED and listed UNTESTED
    v, lines = certify([{"name": "never", "regex": "no such line", "expect": "any"}], {"boot": log})
    bad += v != "NOT CERTIFIED" or not any(l.startswith("UNTESTED") for l in lines)
    print("ok  " if v == "NOT CERTIFIED" else "FAIL", "untested pattern:", [l for l in lines if l.startswith("UNTESTED")])
    v, _ = certify([{"name": "x", "regex": "x"}], {"boot": []})
    bad += v != "INCONCLUSIVE"
    print("ok  " if v == "INCONCLUSIVE" else "FAIL", "empty log -> INCONCLUSIVE")
    print("log_patterns self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) < 3 or argv[0] != "certify":
        print(__doc__)
        return 2
    patterns = json.load(open(argv[1]))
    logs = {}
    for path in argv[2:]:
        try:
            logs[path] = open(path, errors="replace").readlines()
        except OSError:
            logs[path] = []
    v, lines = certify(patterns, logs)
    print("\n".join(lines))
    return {"CERTIFIED": 0, "NOT CERTIFIED": 1, "INCONCLUSIVE": 3}[v]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
