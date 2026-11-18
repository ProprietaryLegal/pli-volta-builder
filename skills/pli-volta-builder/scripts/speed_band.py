#!/usr/bin/env python3
"""speed_band.py : is a speed difference real, or inside the natural wobble between boots?

Two modes.

  speed_band.py band  --ref 25.10,25.30 --arm 24.60,24.70 [--lower-is-better]
      REF are the same metric from >= 2 reference runs taken in the SAME window, at the SAME power limit
      (an A/A pair: two boots, or two passes, of the unchanged build). The band is the spread of the reference
      runs: max(REF) - min(REF). The arm's median is compared with the reference's median:
        FASTER / SLOWER   the difference is larger than the band, in that direction
        WITHIN BAND       it is not (report it; do not call it a win or a loss)
        INCONCLUSIVE      fewer than two reference runs or no arm run (a band cannot be measured from one run)
      Use ms per decode round (lower is better) rather than tok/s when a drafter's acceptance varies with the
      text: tok/s mixes the round time with the acceptance, and acceptance wobbles more between boots.

  speed_band.py abba  --pairs A1,B1,B2,A2[,A3,B3,B4,A4...] [--lower-is-better]
      ABBA order cancels a slow drift over a session. Each block of four gives one paired delta
      ((B1 + B2) - (A1 + A2)) / 2. Reports every block's delta and their mean; with two or more blocks it also
      says whether all deltas point the same way (a sign test in words, not a p-value).

Why: a tolerance tighter than the A/A spread turns noise into verdicts. On a small test bed the same engine bytes
booted twice gave different greedy answers; on the large build the round time drifted about 0.4 ms over a session.
Exit: 0 a decision (FASTER/SLOWER/WITHIN BAND, or ABBA computed), 3 INCONCLUSIVE, 2 usage.
"""
import argparse
import statistics
import sys


def band(ref, arm, lower_is_better):
    if len(ref) < 2 or not arm:
        return "INCONCLUSIVE", f"need >= 2 reference runs and >= 1 arm run (got {len(ref)}, {len(arm)})"
    width = max(ref) - min(ref)
    rm, am = statistics.median(ref), statistics.median(arm)
    d = am - rm
    if abs(d) <= width:
        word = "WITHIN BAND"
    else:
        better = d < 0 if lower_is_better else d > 0
        word = "FASTER" if better else "SLOWER"
    return word, f"{word}: arm median {am:g} vs reference median {rm:g} (diff {d:+g}); band {width:g} from {len(ref)} reference runs"


def abba(values, lower_is_better):
    if len(values) < 4 or len(values) % 4:
        return "INCONCLUSIVE", "ABBA needs blocks of four values: A, B, B, A"
    deltas = []
    for i in range(0, len(values), 4):
        a1, b1, b2, a2 = values[i:i + 4]
        deltas.append(((b1 + b2) - (a1 + a2)) / 2)
    mean = sum(deltas) / len(deltas)
    same = all(x < 0 for x in deltas) or all(x > 0 for x in deltas)
    good = (mean < 0) == lower_is_better
    note = "" if len(deltas) < 2 else (" ; every block points the same way" if same else " ; blocks disagree in sign")
    return "ABBA", (f"ABBA: B minus A per block {', '.join(f'{x:+g}' for x in deltas)}; mean {mean:+g} "
                    f"({'B better' if good and mean != 0 else 'B worse' if mean != 0 else 'no change'}){note}")


def self_test():
    bad = 0
    cases = [
        # ref 25.1, 25.3: band 0.2, median 25.2. arm 24.6, 24.7: median 24.65, diff -0.55 -> beyond band, lower=better -> FASTER
        (band([25.1, 25.3], [24.6, 24.7], True), "FASTER", "diff -0.55"),
        # arm median 25.3: diff +0.1 <= 0.2 -> WITHIN BAND
        (band([25.1, 25.3], [25.3], True), "WITHIN BAND", "diff +0.1"),
        # tok/s, higher better: ref 100, 102 (band 2, median 101); arm 97 -> diff -4 -> SLOWER
        (band([100, 102], [97], False), "SLOWER", "diff -4"),
        # one reference run -> INCONCLUSIVE
        (band([100], [97], False), "INCONCLUSIVE", "need >= 2"),
        # ABBA: A1 30, B1 29.6, B2 29.7, A2 30.1 -> ((29.6+29.7)-(30+30.1))/2 = (59.3-60.1)/2 = -0.4
        (abba([30, 29.6, 29.7, 30.1], True), "ABBA", "-0.4"),
        (abba([30, 29.6, 29.7], True), "INCONCLUSIVE", "blocks of four"),
    ]
    for (word, text), want, frag in cases:
        ok = word == want and frag in text
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {text}")
    print("speed_band self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


def floats(s):
    return [float(x) for x in s.split(",") if x.strip()]


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("band")
    b.add_argument("--ref", required=True)
    b.add_argument("--arm", required=True)
    b.add_argument("--lower-is-better", action="store_true")
    c = sub.add_parser("abba")
    c.add_argument("--pairs", required=True)
    c.add_argument("--lower-is-better", action="store_true")
    a = p.parse_args(argv)
    word, text = band(floats(a.ref), floats(a.arm), a.lower_is_better) if a.mode == "band" else abba(floats(a.pairs), a.lower_is_better)
    print(text)
    return 3 if word == "INCONCLUSIVE" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
