#!/usr/bin/env python3
"""speed_band.py : is a speed difference real, or inside the natural wobble between boots?

Two modes.

  speed_band.py band  --ref 25.10,25.30 --arm 24.60,24.70 [--lower-is-better] [--cutoff-pct 1.8]
      REF are the same metric from >= 2 reference runs taken in the SAME window, at the SAME power limit
      (an A/A pair: two boots, or two passes, of the unchanged build). The band is the larger of the spread of
      the reference runs, max(REF) - min(REF), and the ADOPTION CUTOFF: 1.8 % of the reference median (the
      owner's figure, 2026-11-24; `--cutoff-pct` names another). The arm's median is compared with the reference's:
        FASTER / SLOWER   the difference is larger than the band, in that direction
        WITHIN BAND       it is not (report it; do not call it a win or a loss; a gain under the cutoff is
                          real only if it is also outside the spread, and is still not adopted)
        INCONCLUSIVE      fewer than two reference runs or no arm run (a band cannot be measured from one run)
      Use ms per decode round (lower is better) rather than tok/s when a drafter's acceptance varies with the
      text: tok/s mixes the round time with the acceptance, and acceptance wobbles more between boots.

  speed_band.py abba  --pairs A1,B1,B2,A2[,A3,B3,B4,A4...] [--lower-is-better] [--cutoff-pct 1.8]
      ABBA order cancels a slow drift over a session. Each block of four gives one paired delta
      ((B1 + B2) - (A1 + A2)) / 2. Reports every block's delta and their mean, whether the mean clears the
      cutoff (1.8 % of the mean of the A values), and with two or more blocks whether all deltas point the
      same way (a sign test in words, not a p-value).

Why: a tolerance tighter than the A/A spread turns noise into verdicts, and a gain smaller than the cutoff is not
worth a kit, a boot and a requalification (the owner set 1.8 % on 2026-11-24 after the twelve-card build's read cells
measured A/A spreads of 0.6 to 1.0 %). On a small test bed the same engine bytes
booted twice gave different greedy answers; on the large build the round time drifted about 0.4 ms over a session.
Exit: 0 a decision (FASTER/SLOWER/WITHIN BAND, or ABBA computed), 3 INCONCLUSIVE, 2 usage.
"""
import argparse
import statistics
import sys


CUTOFF_PCT = 1.8  # the adoption cutoff, percent of the reference (owner, 2026-11-24)


def band(ref, arm, lower_is_better, cutoff_pct=CUTOFF_PCT):
    if len(ref) < 2 or not arm:
        return "INCONCLUSIVE", f"need >= 2 reference runs and >= 1 arm run (got {len(ref)}, {len(arm)})"
    spread = max(ref) - min(ref)
    rm, am = statistics.median(ref), statistics.median(arm)
    cutoff = abs(rm) * cutoff_pct / 100
    width = max(spread, cutoff)
    d = am - rm
    if abs(d) <= width:
        word = "WITHIN BAND"
    else:
        better = d < 0 if lower_is_better else d > 0
        word = "FASTER" if better else "SLOWER"
    source = "the A/A spread" if spread >= cutoff else f"the {cutoff_pct:g} % cutoff"
    return word, (f"{word}: arm median {am:g} vs reference median {rm:g} (diff {d:+g}); band {width:g} = {source} "
                  f"(spread {spread:g} from {len(ref)} reference runs, cutoff {cutoff:g})")


def abba(values, lower_is_better, cutoff_pct=CUTOFF_PCT):
    if len(values) < 4 or len(values) % 4:
        return "INCONCLUSIVE", "ABBA needs blocks of four values: A, B, B, A"
    deltas, a_values = [], []
    for i in range(0, len(values), 4):
        a1, b1, b2, a2 = values[i:i + 4]
        deltas.append(((b1 + b2) - (a1 + a2)) / 2)
        a_values += [a1, a2]
    mean = sum(deltas) / len(deltas)
    cutoff = abs(sum(a_values) / len(a_values)) * cutoff_pct / 100
    same = all(x < 0 for x in deltas) or all(x > 0 for x in deltas)
    good = (mean < 0) == lower_is_better
    note = "" if len(deltas) < 2 else (" ; every block points the same way" if same else " ; blocks disagree in sign")
    clears = f"beyond the {cutoff_pct:g} % cutoff ({cutoff:g})" if abs(mean) > cutoff else f"within the {cutoff_pct:g} % cutoff ({cutoff:g}): not adopted"
    return "ABBA", (f"ABBA: B minus A per block {', '.join(f'{x:+g}' for x in deltas)}; mean {mean:+g} "
                    f"({'B better' if good and mean != 0 else 'B worse' if mean != 0 else 'no change'}; {clears}){note}")


def self_test():
    bad = 0
    cases = [
        # ref 25.1, 25.3: spread 0.2, median 25.2, cutoff 1.8 % of 25.2 = 0.4536 -> band 0.4536 (the cutoff).
        # arm 24.6, 24.7: median 24.65, diff -0.55 -> beyond band, lower=better -> FASTER
        (band([25.1, 25.3], [24.6, 24.7], True), "FASTER", "diff -0.55"),
        # arm median 25.3: diff +0.1 <= 0.4536 -> WITHIN BAND
        (band([25.1, 25.3], [25.3], True), "WITHIN BAND", "diff +0.1"),
        # arm 24.9: diff -0.3, outside the spread 0.2 but inside the cutoff 0.4536 -> WITHIN BAND (not adopted)
        (band([25.1, 25.3], [24.9], True), "WITHIN BAND", "diff -0.3"),
        # tok/s, higher better: ref 100, 102 (spread 2, median 101, cutoff 1.818 -> band 2, the spread); arm 97 -> diff -4 -> SLOWER
        (band([100, 102], [97], False), "SLOWER", "band 2 = the A/A spread"),
        # ref 100, 100.5 (spread 0.5, median 100.25, cutoff 1.8045 -> band 1.8045); arm 102 -> +1.75 -> WITHIN BAND; arm 102.5 -> +2.25 -> FASTER
        (band([100, 100.5], [102], False), "WITHIN BAND", "diff +1.75"),
        (band([100, 100.5], [102.5], False), "FASTER", "band 1.8045 = the 1.8 % cutoff"),
        # a stricter cutoff on the command line: 3 % of 100.25 = 3.0075 -> arm 102.5 (+2.25) WITHIN BAND
        (band([100, 100.5], [102.5], False, cutoff_pct=3), "WITHIN BAND", "cutoff 3.0075"),
        # one reference run -> INCONCLUSIVE
        (band([100], [97], False), "INCONCLUSIVE", "need >= 2"),
        # ABBA: A1 30, B1 29.6, B2 29.7, A2 30.1 -> ((29.6+29.7)-(30+30.1))/2 = (59.3-60.1)/2 = -0.4;
        # cutoff 1.8 % of mean A 30.05 = 0.5409 -> within the cutoff
        (abba([30, 29.6, 29.7, 30.1], True), "ABBA", "-0.4"),
        (abba([30, 29.6, 29.7, 30.1], True), "ABBA", "within the 1.8 % cutoff (0.5409)"),
        # A1 30, B1 29.4, B2 29.5, A2 30.1 -> (58.9-60.1)/2 = -0.6 -> beyond 0.5409
        (abba([30, 29.4, 29.5, 30.1], True), "ABBA", "beyond the 1.8 % cutoff (0.5409)"),
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
    b.add_argument("--cutoff-pct", type=float, default=CUTOFF_PCT, help="adoption cutoff, percent of the reference median (default 1.8)")
    c = sub.add_parser("abba")
    c.add_argument("--pairs", required=True)
    c.add_argument("--lower-is-better", action="store_true")
    c.add_argument("--cutoff-pct", type=float, default=CUTOFF_PCT, help="adoption cutoff, percent of the mean A value (default 1.8)")
    a = p.parse_args(argv)
    word, text = (band(floats(a.ref), floats(a.arm), a.lower_is_better, a.cutoff_pct) if a.mode == "band"
                  else abba(floats(a.pairs), a.lower_is_better, a.cutoff_pct))
    print(text)
    return 3 if word == "INCONCLUSIVE" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
