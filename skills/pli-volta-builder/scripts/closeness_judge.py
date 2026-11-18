#!/usr/bin/env python3
"""closeness_judge.py REF.json ARM.json --need-first N --max-dlp X [--early 3 --gap 0.9 --max-early 2]

For a change that is ALLOWED to move rounding (a new reduction order, a new chunk cut, a different split count),
token identity is the wrong test. This judge asks: how long does the arm follow the reference, and how close are
its chosen-token log-probabilities before it parts?

A capture is like identity_judge.py's, and every record ALSO carries, for each generated token:
    "logprobs":      [float]          the log-probability of the chosen token
    "top_ids":       [[int, ...]]     the reference's top-k candidate ids at that position
    "top_logprobs":  [[float, ...]]   their log-probabilities
(all three arrays as long as token_ids).

Per prompt:
  first divergence  first position where the ids differ; if none, min(len) and the prompt is CENSORED (it ended
                    before it could part: report it as such, it is not evidence of closeness beyond its length).
  gap               at the first divergence: the reference's logprob of its own token minus its logprob of the
                    arm's token ("outside top-k" when the arm's token is not in the reference's list: a lower bound).
  mean |dlp|        mean |reference logprob - arm logprob| of the chosen tokens before the divergence.

Lines (thresholds are fixed in the plan BEFORE the data; pass them on the command line):
  JUNK   more than --max-early prompts part at a position <= --early with gap > --gap nats: the change broke
         something (this is how a scheduling defect showed: junk from token 1). Verdict FAIL.
  HOLDS  median first divergence >= --need-first AND median mean |dlp| <= --max-dlp. Verdict PASS.
  else   FAIL.
Strict completeness first, as identity_judge.py: missing/extra/repeated ids, misaligned or non-finite arrays,
different prompts -> INCONCLUSIVE (exit 3), never a figure, never a pass.

Know what the reference is. A reference captured in the OLD arithmetic cannot judge a change that alters the
arithmetic on purpose: a fair line needs a reference in the arm's own arithmetic, or an independent higher-precision
reference, or a teacher-forced comparison (same histories, compare next-token decisions). See
references/testing-method.md.

Exit: 0 PASS, 1 FAIL, 3 INCONCLUSIVE, 2 usage. `--self-test` runs hand-worked cases.
"""
import argparse
import json
import math
import statistics
import sys


def load(path):
    with open(path) as f:
        doc = json.load(f)
    return doc["prompts"] if isinstance(doc, dict) and "prompts" in doc else doc


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def record_gaps(name, it):
    k = it.get("id")
    t = it.get("token_ids")
    if not isinstance(t, list) or not all(isinstance(v, int) for v in t):
        return [f"{name} {k!r}: token_ids missing"]
    out = []
    if not isinstance(it.get("prompt_sha256"), str):
        out.append(f"{name} {k!r}: prompt_sha256 missing")
    for f in ("logprobs", "top_ids", "top_logprobs"):
        if not isinstance(it.get(f), list) or len(it[f]) != len(t):
            out.append(f"{name} {k!r}: {f} missing or not one per token")
    if out:
        return out
    if not all(_finite(v) for v in it["logprobs"]):
        out.append(f"{name} {k!r}: a logprob is not finite")
    for ids, lps in zip(it["top_ids"], it["top_logprobs"]):
        if not ids or len(ids) != len(lps) or not all(_finite(v) for v in lps):
            out.append(f"{name} {k!r}: a top list is empty, unpaired or not finite")
            break
    return out


def complete(ref_items, arm_items):
    reasons, maps = [], []
    for name, items in (("reference", ref_items), ("arm", arm_items)):
        m = {}
        if not isinstance(items, list) or not items:
            reasons.append(f"{name}: empty or not a list")
            items = []
        for it in items:
            if not isinstance(it, dict) or "id" not in it:
                reasons.append(f"{name}: a record without an id")
                continue
            if it["id"] in m:
                reasons.append(f"{name}: id {it['id']!r} twice")
            m[it["id"]] = it
            reasons += record_gaps(name, it)
        maps.append(m)
    ref, arm = maps
    reasons += [f"arm: missing {k!r}" for k in sorted(set(ref) - set(arm), key=str)]
    reasons += [f"arm: extra {k!r}" for k in sorted(set(arm) - set(ref), key=str)]
    for k in set(ref) & set(arm):
        if ref[k].get("prompt_sha256") != arm[k].get("prompt_sha256"):
            reasons.append(f"{k!r}: different prompts")
    return reasons, ref, arm


def per_prompt(r, a):
    rt, at = r["token_ids"], a["token_ids"]
    n = min(len(rt), len(at))
    first = next((i for i in range(n) if rt[i] != at[i]), None)
    censored = first is None
    if censored:
        first = n
    dl = [abs(r["logprobs"][i] - a["logprobs"][i]) for i in range(first)]
    mean_dlp = sum(dl) / len(dl) if dl else 0.0
    gap = None
    if not censored:
        ids, lps = r["top_ids"][first], r["top_logprobs"][first]
        own = r["logprobs"][first]
        gap = own - lps[ids.index(at[first])] if at[first] in ids else math.inf
    return first, censored, gap, mean_dlp


def judge(ref_items, arm_items, need_first, max_dlp, early=3, gap_nats=0.9, max_early=2):
    reasons, ref, arm = complete(ref_items, arm_items)
    if reasons:
        return "INCONCLUSIVE", reasons
    lines, firsts, dlps, n_early = [], [], [], 0
    for k in sorted(ref, key=str):
        first, censored, gap, mean_dlp = per_prompt(ref[k], arm[k])
        firsts.append(first)
        dlps.append(mean_dlp)
        if gap is not None and first <= early and gap > gap_nats:
            n_early += 1
        g = "-" if gap is None else ("outside top-k" if gap == math.inf else f"{gap:.3f}")
        lines.append(f"{k}: first divergence {first}{' CENSORED' if censored else ''}, gap {g}, mean |dlp| {mean_dlp:.4f}")
    med_first, med_dlp = statistics.median(firsts), statistics.median(dlps)
    if n_early > max_early:
        verdict, word = "FAIL", f"JUNK ({n_early} early divergences with gap > {gap_nats})"
    elif med_first >= need_first and med_dlp <= max_dlp:
        verdict, word = "PASS", "HOLDS"
    else:
        verdict, word = "FAIL", "DOES NOT HOLD"
    lines.append(f"CLOSENESS {verdict}: {word}; median first divergence {med_first} (need {need_first}), "
                 f"median mean |dlp| {med_dlp:.4f} (max {max_dlp}); early divergences {n_early}")
    return verdict, lines


def self_test():
    def rec(k, ids, lps, tops):
        return {"id": k, "prompt_sha256": "s" + k, "token_ids": ids, "logprobs": lps,
                "top_ids": [t[0] for t in tops], "top_logprobs": [t[1] for t in tops]}
    T = ([1, 2], [-0.1, -2.5])   # a reference top list: id 1 at -0.1, id 2 at -2.5
    # Reference prompt x: ids 1,1,1,1,1 with logprobs -0.1 each.
    ref = [rec("x", [1] * 5, [-0.1] * 5, [T] * 5)]
    bad = 0

    def check(name, arm, need, mx, want, expect_line=None):
        nonlocal bad
        got, lines = judge(ref, arm, need, mx)
        ok = got == want and (expect_line is None or expect_line in lines[-1] or expect_line in lines[0])
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: want {want}, got {got}: {lines[-1]}")
    # Same ids, logprobs differ by 0.02 each: censored at 5, mean |dlp| = 0.02.
    # need_first 4 -> 5 >= 4, 0.02 <= 0.05 -> PASS
    check("close", [rec("x", [1] * 5, [-0.12] * 5, [T] * 5)], 4, 0.05, "PASS", "x: first divergence 5 CENSORED")
    # Parts at position 3 (id 2 instead of 1). Gap = -0.1 - (-2.5) = 2.4 > 0.9 at position 3 <= 3: one early
    # divergence; max_early 2 so not JUNK. median first = 3 < need 4 -> FAIL "DOES NOT HOLD".
    check("parts early", [rec("x", [1, 1, 1, 2, 1], [-0.1] * 5, [T] * 5)], 4, 0.05, "FAIL", "gap 2.400")
    # Mean |dlp| before the divergence: positions 0..2 differ by 0.3 -> 0.3 > 0.05 -> FAIL
    check("drifts", [rec("x", [1, 1, 1, 2, 1], [-0.4] * 5, [T] * 5)], 3, 0.05, "FAIL", "mean |dlp| 0.3000")
    # Arm token 7 is outside the reference's top list -> gap "outside top-k"
    check("outside", [rec("x", [7, 1, 1, 1, 1], [-0.1] * 5, [T] * 5)], 1, 0.05, "FAIL", "outside top-k")
    # Missing logprobs on the arm -> INCONCLUSIVE
    a = rec("x", [1] * 5, [-0.1] * 5, [T] * 5)
    del a["logprobs"]
    check("incomplete", [a], 4, 0.05, "INCONCLUSIVE")
    # JUNK: three prompts all parting at token 1 with gap 2.4; max_early 2 -> FAIL JUNK
    ref3 = [rec(k, [1] * 5, [-0.1] * 5, [T] * 5) for k in "abc"]
    arm3 = [rec(k, [1, 2, 1, 1, 1], [-0.1] * 5, [T] * 5) for k in "abc"]
    got, lines = judge(ref3, arm3, 1, 1.0)
    ok = got == "FAIL" and "JUNK (3 early" in lines[-1]
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} junk: {lines[-1]}")
    print("closeness_judge self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    p = argparse.ArgumentParser()
    p.add_argument("ref")
    p.add_argument("arm")
    p.add_argument("--need-first", type=float, required=True)
    p.add_argument("--max-dlp", type=float, required=True)
    p.add_argument("--early", type=int, default=3)
    p.add_argument("--gap", type=float, default=0.9)
    p.add_argument("--max-early", type=int, default=2)
    a = p.parse_args(argv)
    verdict, lines = judge(load(a.ref), load(a.arm), a.need_first, a.max_dlp, a.early, a.gap, a.max_early)
    for line in lines:
        print(line)
    if verdict == "INCONCLUSIVE":
        print("CLOSENESS INCONCLUSIVE: the captures cannot be compared; this is not a pass")
    return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 3}[verdict]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
