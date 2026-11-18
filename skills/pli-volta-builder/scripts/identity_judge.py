#!/usr/bin/env python3
"""identity_judge.py REF.json ARM.json : are two answer captures token-identical? STRICT.

A capture is a JSON object {"prompts": [record, ...]} (or a bare list of records). A record is
    {"id": str, "prompt_sha256": str, "token_ids": [int, ...], "finish_reason": str (optional)}
Write one per prompt, greedy decoding, from public prompts only.

Verdicts (exit code):
  PASS (0)          the same set of ids on both sides, each id once, every pair equal: same prompt digest,
                    EQUAL LENGTH, equal ids, and the same finish reason where both record one.
  FAIL (1)          every pair is comparable and at least one differs (the first differing position is printed).
  INCONCLUSIVE (3)  anything that makes the comparison incomplete: a missing, extra or repeated id, a record
                    without a prompt digest or token ids, a finish reason the reference has and the arm lacks,
                    an empty capture. INCONCLUSIVE is never a pass.
  usage error (2)

Why strict: an earlier judge compared answers only through the shorter one, so an answer cut one token short
read as "identical". An independent review found it by deleting one token from each of twelve real reference
answers and getting "identical 12 of 12". Equal length and the full key set are part of identity.

Run `identity_judge.py --self-test` to check the judge on hand-made captures.
"""
import json
import sys

FINISH = "finish_reason"


def load(path):
    with open(path) as f:
        doc = json.load(f)
    items = doc["prompts"] if isinstance(doc, dict) and "prompts" in doc else doc
    if not isinstance(items, list):
        raise ValueError(f"{path}: expected a list of prompt records")
    return items


def gaps(name, items):
    """Reasons the capture itself is incomplete, and {id: record}."""
    reasons, by_id = [], {}
    if not items:
        reasons.append(f"{name}: empty capture")
    for it in items:
        if not isinstance(it, dict) or "id" not in it:
            reasons.append(f"{name}: a record without an id")
            continue
        k = it["id"]
        if k in by_id:
            reasons.append(f"{name}: id {k!r} occurs twice")
        by_id[k] = it
        if not isinstance(it.get("prompt_sha256"), str):
            reasons.append(f"{name}: {k!r} has no prompt_sha256")
        t = it.get("token_ids")
        if not isinstance(t, list) or not all(isinstance(v, int) and not isinstance(v, bool) for v in t):
            reasons.append(f"{name}: {k!r} has no integer token_ids")
    return reasons, by_id


def judge(ref_items, arm_items):
    """(verdict, lines). Pure."""
    r_gaps, ref = gaps("reference", ref_items)
    a_gaps, arm = gaps("arm", arm_items)
    reasons = r_gaps + a_gaps
    for k in sorted(set(ref) - set(arm), key=str):
        reasons.append(f"arm: missing id {k!r}")
    for k in sorted(set(arm) - set(ref), key=str):
        reasons.append(f"arm: id {k!r} the reference lacks")
    for k in sorted(set(ref) & set(arm), key=str):
        if FINISH in ref[k] and FINISH not in arm[k]:
            reasons.append(f"{k!r}: the reference records a finish reason, the arm does not")
    if reasons:
        return "INCONCLUSIVE", reasons
    lines, differ = [], 0
    for k in sorted(ref, key=str):
        r, a = ref[k], arm[k]
        if r["prompt_sha256"] != a["prompt_sha256"]:
            return "INCONCLUSIVE", [f"{k!r}: the two captures used different prompts"]
        rt, at = r["token_ids"], a["token_ids"]
        first = next((i for i, (x, y) in enumerate(zip(rt, at)) if x != y), None)
        if first is None and len(rt) != len(at):
            first = min(len(rt), len(at))
            why = f"length differs ({len(rt)}, {len(at)})"
        elif first is not None:
            why = f"token differs at position {first}"
        elif FINISH in r and FINISH in a and r[FINISH] != a[FINISH]:
            first, why = len(rt), f"finish reason differs ({r[FINISH]}, {a[FINISH]})"
        else:
            lines.append(f"{k}: identical ({len(rt)} tokens)")
            continue
        differ += 1
        lines.append(f"{k}: DIFFERENT, {why}")
    n = len(ref)
    verdict = "FAIL" if differ else "PASS"
    lines.append(f"IDENTITY {verdict}: identical {n - differ} of {n}")
    return verdict, lines


EXIT = {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 3}


def self_test():
    def rec(k, ids, fin="stop", sha="p" ):
        return {"id": k, "prompt_sha256": sha + k, "token_ids": ids, "finish_reason": fin}
    ref = [rec("a", [1, 2, 3]), rec("b", [4, 5])]
    cases = [
        # same ids, same lengths -> PASS, "identical 2 of 2"
        ("equal", ref, [rec("a", [1, 2, 3]), rec("b", [4, 5])], "PASS"),
        # 'a' cut one token short: prefix agrees, length 3 vs 2 -> FAIL (the old judge said identical)
        ("cut short", ref, [rec("a", [1, 2]), rec("b", [4, 5])], "FAIL"),
        # one token changed at position 1 -> FAIL
        ("changed", ref, [rec("a", [1, 9, 3]), rec("b", [4, 5])], "FAIL"),
        # 'b' missing -> INCONCLUSIVE, never PASS
        ("missing", ref, [rec("a", [1, 2, 3])], "INCONCLUSIVE"),
        # extra id 'c' -> INCONCLUSIVE
        ("extra", ref, [rec("a", [1, 2, 3]), rec("b", [4, 5]), rec("c", [6])], "INCONCLUSIVE"),
        # 'a' twice -> INCONCLUSIVE
        ("repeated", ref, [rec("a", [1, 2, 3]), rec("a", [1, 2, 3]), rec("b", [4, 5])], "INCONCLUSIVE"),
        # same ids, finish 'stop' vs 'length' -> FAIL
        ("finish", ref, [rec("a", [1, 2, 3]), rec("b", [4, 5], fin="length")], "FAIL"),
        # empty arm -> INCONCLUSIVE
        ("empty", ref, [], "INCONCLUSIVE"),
    ]
    bad = 0
    for name, r, a, want in cases:
        got, lines = judge(r, a)
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: want {want}, got {got}")
    got, lines = judge(ref, cases[1][2])
    assert "DIFFERENT, length differs (3, 2)" in lines[0], lines
    got, lines = judge(ref, cases[2][2])
    assert "token differs at position 1" in lines[0], lines
    print("identity_judge self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) != 2:
        print(__doc__)
        return 2
    verdict, lines = judge(load(argv[0]), load(argv[1]))
    for line in lines:
        print(line)
    if verdict == "INCONCLUSIVE":
        print(f"IDENTITY INCONCLUSIVE: {len(lines)} reason(s); this is not a pass")
    return EXIT[verdict]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
