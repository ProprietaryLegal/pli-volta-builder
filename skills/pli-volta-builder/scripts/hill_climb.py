#!/usr/bin/env python3
# hill_climb.py: the automated optimization loop of PLI Volta Builder (phase 6, and phase 9's research loop).
#
# Derived in part from bench/hillclimb.py of https://github.com/0xSero/Inkling-Small-2-Sparks by 0xSero
# (Apache License 2.0; see CREDITS.md and NOTICE). Taken from it: the step / measure / status driver, a JSON state
# file plus an append-only JSONL history, an ordered candidate ladder whose entries each change ONE setting and say
# why, safety rails that refuse a candidate before it runs, a deferral when a precondition is missing, revert on a
# failed boot, quality as a hard gate before any speed score, and "a contended run is not comparable". Changed here:
# the code is rewritten and generic; the gates of the PLI Volta campaigns sit on top (see the docstring).
# Licensed under the Apache License, Version 2.0.
"""hill_climb.py : propose one change, measure it against a reference taken in the SAME run, keep it only if it
passed every gate, and loop; resumable, never repeats itself, records every loss.

  hill_climb.py init  DIR CONFIG.json   start a campaign folder from a config (copies it to DIR/climb.json)
  hill_climb.py rule  DIR               write the amendment for the next candidate BEFORE its data
                                        (DIR/amendments.md, with the UTC time and the prediction); nothing runs
  hill_climb.py step  DIR               run the next ruled candidate: reference and candidate in one run
                                        (order ABBA by default), judge it, record it
  hill_climb.py adopt DIR               run every candidate that passed alone, TOGETHER, against a same-run
                                        reference; on PASS the standing configuration becomes that set
  hill_climb.py status DIR              print the state
  hill_climb.py --self-test             a toy objective whose optimum is known by hand

THE GATES (what an automatic hill-climb lacks for a serving build, and the PLI campaigns required):
  1. Rule before data: `step` refuses a candidate whose amendment (lines and prediction) was not written first.
  2. One change per run, against a reference measured in the same run, never against a stored best score.
  3. Quality is judged by a strict judge inside the measure command (identity for exact changes, closeness for
     changes that move rounding); FAIL is a loss however fast; INCONCLUSIVE is never a win.
  4. A speed difference counts only beyond the run's own A/A band; a gain inside the band is WITHIN BAND.
  5. Every metric the config names must be present in every arm; a missing one is INCONCLUSIVE.
  6. Adopt only what passed alone AND passed again together (`adopt`), with no metric worse beyond its band.
  7. Losses are recorded with their numbers; a tried (base, change) pair is never run again unless the config
     marks the condition as changed (`retry_reason`).
  8. Owner's gates: a candidate touching a key in `owner_keys` (power, clocks, hardware, downloads, stopping a
     shared server, publishing) is not run: the loop stops with WAITING-OWNER and prints the question.
  9. One owner: a lock file with the PID; a second driver on the same folder refuses.

CONFIG (JSON):
  {"base": {"SETTING": "value", ...},                  # the standing configuration
   "metrics": {"decode_ms": {"units_per_task": 4000, "scale_s": 0.001},    # time per unit, lower is better;
               "read_ms_per_ktok": {"units_per_task": 120, "scale_s": 0.001}},  # seconds/task = value*units*scale
   "min_gain_s": 1.0,                                   # least seconds saved per task worth adopting
   "order": "ABBA",                                     # or "AB" with "bands": {"metric": band} from phase 4's A/A
   "owner_keys": ["POWER_W", "CLOCK_MHZ"],
   "rails": [["KV_BYTES", ">=", 18500000000]],          # checked on base+change before anything runs
   "measure_cmd": "bash run_arm.sh",                    # see MEASURE below
   "candidates": [{"id": "rel8192", "key": "EMPTY_CACHE_TOKENS", "value": "8192", "exact": true,
                   "why": "...", "predict": {"read_ms_per_ktok": -9}, "size_s_per_task": 3.0}]}
  Candidates run in the order given; order them by size_s_per_task per unit of effort (phase 5).

MEASURE: measure_cmd is run once per arm with the environment CLIMB_ARM (ref | cand | adopt), CLIMB_SETTINGS (JSON)
and every setting as a variable. It boots the arm on the TEST port, runs the cells, judges quality against the
accepted capture, stops the arm, and prints ONE JSON line:
  {"boot": "ok" | "fail", "quality": "PASS" | "FAIL" | "INCONCLUSIVE", "contended": false,
   "metrics": {"decode_ms": 25.1, "read_ms_per_ktok": 0.30}}
A non-zero exit, unparseable output, "contended": true (another user's traffic during the arm) are INCONCLUSIVE.
"""
import json
import os
import shlex
import subprocess
import sys
import time

STATUSES = ("PASS-ALONE", "FAIL", "INCONCLUSIVE", "WITHIN BAND", "BOOT-FAIL", "UNSAFE", "WAITING-OWNER",
            "SKIPPED-TRIED", "ADOPTED", "ADOPT-FAIL", "ADOPT-INCONCLUSIVE")


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def fingerprint(base, changes):
    return json.dumps({"base": base, "changes": changes}, sort_keys=True)


OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, "<": lambda a, b: a < b,
       "==": lambda a, b: a == b, "!=": lambda a, b: a != b}


def rails_ok(settings, rails):
    for key, op, bound in rails:
        if key not in settings:
            continue
        try:
            v = float(settings[key])
        except ValueError:
            return False, f"{key}={settings[key]!r} is not a number for rail {op} {bound}"
        if not OPS[op](v, float(bound)):
            return False, f"{key}={settings[key]} breaks the rail {key} {op} {bound}"
    return True, "ok"


def run_measure_cmd(cmd, arm, settings):
    env = dict(os.environ, CLIMB_ARM=arm, CLIMB_SETTINGS=json.dumps(settings))
    env.update({k: str(v) for k, v in settings.items()})
    r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, env=env)
    if r.returncode != 0:
        return {"boot": "fail" if "boot" in r.stdout.lower() else "unknown", "quality": "INCONCLUSIVE",
                "error": f"exit {r.returncode}"}
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"quality": "INCONCLUSIVE", "error": "output is not one JSON line"}


class Climb:
    def __init__(self, folder, measure=None):
        self.dir = folder
        self.cfg = json.load(open(os.path.join(folder, "climb.json")))
        sp = os.path.join(folder, "state.json")
        self.state = json.load(open(sp)) if os.path.exists(sp) else {
            "base": dict(self.cfg["base"]), "next": 0, "ruled": [], "passed": [], "tried": [], "adoptions": 0}
        self.measure = measure or (lambda arm, s: run_measure_cmd(self.cfg["measure_cmd"], arm, s))

    # -- persistence -------------------------------------------------------------------------------------------
    def save(self):
        write_atomic(os.path.join(self.dir, "state.json"), json.dumps(self.state, indent=1, sort_keys=True))

    def record(self, entry):
        entry = dict(entry, t=utc(), base=self.state["base"])
        with open(os.path.join(self.dir, "history.jsonl"), "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def lock(self):
        p = os.path.join(self.dir, "LOCK")
        if os.path.exists(p):
            pid = int(open(p).read().strip() or 0)
            try:
                os.kill(pid, 0)
                raise SystemExit(f"REFUSED: driver PID {pid} owns {self.dir} (one owner per campaign)")
            except ProcessLookupError:
                pass
        write_atomic(p, str(os.getpid()))

    def unlock(self):
        try:
            os.remove(os.path.join(self.dir, "LOCK"))
        except FileNotFoundError:
            pass

    # -- the loop ----------------------------------------------------------------------------------------------
    def current(self):
        c = self.cfg["candidates"]
        return c[self.state["next"]] if self.state["next"] < len(c) else None

    def rule(self):
        c = self.current()
        if c is None:
            return "EXHAUSTED: no candidate left; go to phase 9 (research) for new sized candidates"
        if c["id"] in self.state["ruled"]:
            return f"ALREADY RULED: {c['id']}"
        lines = [f"\n**Amendment ({utc()}, before its data): candidate `{c['id']}`: {c['key']}={c['value']}.**",
                 f"- WHY: {c.get('why', '(not given)')}. Size: {c.get('size_s_per_task', '?')} s per task (ESTIMATE).",
                 f"- ARMS: `ref` = the standing configuration; `cand` = ref with {c['key']}={c['value']} (one change); "
                 f"order {self.cfg.get('order', 'ABBA')}, same run.",
                 f"- LINES: quality {'identity' if c.get('exact', True) else 'closeness'} PASS by the strict judge "
                 f"(FAIL is a loss; INCONCLUSIVE is not a win); every metric of {sorted(self.cfg['metrics'])} present "
                 f"in every arm; seconds saved per task beyond the run's band and at least {self.cfg.get('min_gain_s', 0)}"
                 f" s; no metric worse beyond its band.",
                 f"- PREDICTED: {json.dumps(c.get('predict', {}))}.",
                 "- ADOPTION: only through `adopt`, together with every other candidate that passed alone."]
        with open(os.path.join(self.dir, "amendments.md"), "a") as f:
            f.write("\n".join(lines) + "\n")
        self.state["ruled"].append(c["id"])
        self.save()
        return f"RULED: {c['id']} (amendments.md)"

    def run_pair(self, ref_settings, cand_settings, cand_arm="cand"):
        """Measure in the configured order. Returns (verdict, detail)."""
        order = self.cfg.get("order", "ABBA")
        seq = ["ref", cand_arm, cand_arm, "ref"] if order == "ABBA" else ["ref", cand_arm]
        res = {"ref": [], cand_arm: []}
        for arm in seq:
            out = self.measure(arm, ref_settings if arm == "ref" else cand_settings)
            if out.get("boot") == "fail" and arm != "ref":
                return "BOOT-FAIL", {"arm": arm, "out": out}
            if out.get("quality") != "PASS" or out.get("contended"):
                word = "FAIL" if out.get("quality") == "FAIL" and arm != "ref" else "INCONCLUSIVE"
                why = "contended run" if out.get("contended") else f"{arm} quality {out.get('quality')}"
                return word, {"arm": arm, "why": why, "out": out}
            res[arm].append(out.get("metrics", {}))
        saved_s, worse, per = 0.0, [], {}
        for m, w in self.cfg["metrics"].items():
            r = [x.get(m) for x in res["ref"]]
            c = [x.get(m) for x in res[cand_arm]]
            if any(v is None for v in r + c):
                return "INCONCLUSIVE", {"why": f"metric {m} missing in an arm"}
            band = (max(r) - min(r)) if order == "ABBA" else self.cfg.get("bands", {}).get(m)
            if band is None:
                return "INCONCLUSIVE", {"why": f"no band for {m}: order AB needs bands from an A/A run"}
            d = sum(c) / len(c) - sum(r) / len(r)          # time per unit: negative is faster
            per[m] = {"ref": r, "cand": c, "delta": d, "band": band}
            if abs(d) > band:
                saved_s += -d * w["units_per_task"] * w.get("scale_s", 1.0)
                if d > 0:
                    worse.append(m)
        return "MEASURED", {"saved_s": saved_s, "worse": worse, "per_metric": per}

    def step(self):
        c = self.current()
        if c is None:
            return "EXHAUSTED: no candidate left; go to phase 9 (research)"
        if c["id"] not in self.state["ruled"]:
            return f"REFUSED: {c['id']} has no amendment yet; run `rule` first (rule before data)"
        base = self.state["base"]
        change = {c["key"]: c["value"]}
        fp = fingerprint(base, change)
        if fp in self.state["tried"] and not c.get("retry_reason"):
            word, detail = "SKIPPED-TRIED", {"why": "this change was already run on this base"}
        elif c["key"] in self.cfg.get("owner_keys", []):
            word, detail = "WAITING-OWNER", {"question": f"May I set {c['key']}={c['value']}? ({c.get('why', '')}) "
                                                         "This setting is the owner's."}
        else:
            cand = dict(base, **change)
            ok, why = rails_ok(cand, self.cfg.get("rails", []))
            if not ok:
                word, detail = "UNSAFE", {"why": why}
            else:
                word, detail = self.run_pair(base, cand)
                self.state["tried"].append(fp)
                if word == "MEASURED":
                    if detail["worse"]:
                        word = "FAIL"
                    elif detail["saved_s"] >= self.cfg.get("min_gain_s", 0) and detail["saved_s"] > 0:
                        word = "PASS-ALONE"
                        # one value per setting in the adopt set: keep the one that saved more
                        same = [p for p in self.state["passed"] if p["key"] == c["key"]]
                        if not same or detail["saved_s"] > max(p["saved_s"] for p in same):
                            self.state["passed"] = [p for p in self.state["passed"] if p["key"] != c["key"]]
                            self.state["passed"].append({"id": c["id"], "key": c["key"], "value": c["value"],
                                                         "saved_s": detail["saved_s"]})
                    else:
                        word = "WITHIN BAND"
        self.record({"kind": "candidate", "id": c["id"], "change": change, "status": word, "detail": detail,
                     "predict": c.get("predict")})
        if word != "WAITING-OWNER":
            self.state["next"] += 1
        self.save()
        return f"{word}: {c['id']} {json.dumps(detail, sort_keys=True)[:300]}"

    def adopt(self):
        passed = self.state["passed"]
        if not passed:
            return "NOTHING TO ADOPT"
        base = self.state["base"]
        together = dict(base, **{p["key"]: p["value"] for p in passed})
        ok, why = rails_ok(together, self.cfg.get("rails", []))
        if not ok:
            word, detail = "ADOPT-FAIL", {"why": "together " + why}
        else:
            word, detail = self.run_pair(base, together, cand_arm="adopt")
            if word == "MEASURED":
                best = max(p["saved_s"] for p in passed)
                if detail["worse"] or detail["saved_s"] < best * 0.97:
                    word = "ADOPT-FAIL"
                    detail["why"] = f"worse metric(s) {detail['worse']} or {detail['saved_s']:.2f} s < 97 % of the best single {best:.2f} s"
                else:
                    word = "ADOPTED"
            elif word in ("FAIL", "BOOT-FAIL"):
                word = "ADOPT-FAIL"
            else:
                word = "ADOPT-INCONCLUSIVE"
        self.record({"kind": "adopt", "set": passed, "status": word, "detail": detail})
        if word == "ADOPTED":
            self.state["base"] = together
            self.state["adoptions"] += 1
        self.state["passed"] = []
        self.save()
        return f"{word}: {[p['id'] for p in passed]} {json.dumps(detail, sort_keys=True)[:300]}"


# ---------------------------------------------------------------------------------------------------------------
def self_test():
    """A toy objective with a hand-known optimum.

    Settings x and y (integers). Time per unit (ms) t(x, y) = 10 + (x - 3)^2 + (y - 1)^2, so the optimum is
    x = 3, y = 1 with t = 10. The measured value wobbles by +0.1 / -0.1 on alternate reference arms, so an ABBA run's
    band is 0.2 ms. units_per_task 1000, scale 0.001: one ms per unit = one second per task.
    Base (0, 0): t = 10 + 9 + 1 = 20.
      A  x=3      -> t(3,0) = 11: 9 ms faster  -> 9 s/task      PASS-ALONE
      B  y=1      -> t(0,1) = 19: 1 ms faster  -> 1 s/task      PASS-ALONE
      C  y=2      -> fast (t = 5) but the quality judge says FAIL                           FAIL
      D  x=5      -> t(5,0) = 15: 5 s/task, same key as A, smaller: passes alone but A stays in the set
      E  POWER_W  -> the owner's key: not run                                              WAITING-OWNER
      F  BROKEN=1 -> the measure omits the metric                                          INCONCLUSIVE
      G  x=3 again on the same base                                                        SKIPPED-TRIED
      H  z=1      -> no effect: delta 0 within the band                                    WITHIN BAND
      I  KV=1     -> breaks the rail KV >= 2                                                UNSAFE
    adopt: base + {x:3, y:1} -> t = 10: 10 s/task >= 97 % of the best single (9): ADOPTED; new base (3, 1), t = 10.
    """
    import tempfile
    calls = {"ref": 0}

    def measure(arm, s):
        x, y = int(s.get("x", 0)), int(s.get("y", 0))
        if s.get("BROKEN") == "1" and arm != "ref":
            return {"boot": "ok", "quality": "PASS", "metrics": {}}
        if y == 2:
            return {"boot": "ok", "quality": "FAIL", "metrics": {"t_ms": 5.0}}
        t = 10 + (x - 3) ** 2 + (y - 1) ** 2
        if arm == "ref":
            calls["ref"] += 1
            t += 0.1 if calls["ref"] % 2 else -0.1
        return {"boot": "ok", "quality": "PASS", "metrics": {"t_ms": t}}

    cfg = {"base": {"x": "0", "y": "0", "KV": "4"}, "metrics": {"t_ms": {"units_per_task": 1000, "scale_s": 0.001}},
           "min_gain_s": 0.5, "order": "ABBA", "owner_keys": ["POWER_W"], "rails": [["KV", ">=", 2]],
           "candidates": [
               {"id": "A", "key": "x", "value": "3", "predict": {"t_ms": -9}},
               {"id": "B", "key": "y", "value": "1", "predict": {"t_ms": -1}},
               {"id": "C", "key": "y", "value": "2"},
               {"id": "D", "key": "x", "value": "5"},
               {"id": "E", "key": "POWER_W", "value": "200"},
               {"id": "F", "key": "BROKEN", "value": "1"},
               {"id": "G", "key": "x", "value": "3"},
               {"id": "H", "key": "z", "value": "1"},
               {"id": "I", "key": "KV", "value": "1"}]}
    want = {"A": "PASS-ALONE", "B": "PASS-ALONE", "C": "FAIL", "D": "PASS-ALONE", "E": "WAITING-OWNER",
            "F": "INCONCLUSIVE", "G": "SKIPPED-TRIED", "H": "WITHIN BAND", "I": "UNSAFE"}
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        json.dump(cfg, open(os.path.join(d, "climb.json"), "w"))
        # rule before data: step on an unruled candidate refuses
        out = Climb(d, measure).step()
        ok = out.startswith("REFUSED")
        bad += not ok
        print(("ok   " if ok else "FAIL ") + "unruled candidate refused: " + out[:70])
        for cid in "ABCDEFGHI":
            cl = Climb(d, measure)                 # a fresh object every time: resumes from state.json
            cl.rule()
            out = cl.step()
            if out.startswith("WAITING-OWNER"):    # the owner says no: skip it by hand, as a human would
                st = json.load(open(os.path.join(d, "state.json")))
                st["next"] += 1
                write_atomic(os.path.join(d, "state.json"), json.dumps(st))
            got = out.split(":")[0]
            ok = got == want[cid]
            bad += not ok
            print(("ok   " if ok else "FAIL ") + f"{cid}: {got} (want {want[cid]})")
        st = json.load(open(os.path.join(d, "state.json")))
        passed = {p["id"] for p in st["passed"]}
        ok = passed == {"A", "B"}
        bad += not ok
        print(("ok   " if ok else "FAIL ") + f"passed set keeps the better value per key: {sorted(passed)}")
        out = Climb(d, measure).adopt()
        st = json.load(open(os.path.join(d, "state.json")))
        t_final = 10 + (int(st["base"]["x"]) - 3) ** 2 + (int(st["base"]["y"]) - 1) ** 2
        ok = out.startswith("ADOPTED") and st["base"]["x"] == "3" and st["base"]["y"] == "1" and t_final == 10
        bad += not ok
        print(("ok   " if ok else "FAIL ") + f"adopt: {out.split(':')[0]}; base x={st['base']['x']} y={st['base']['y']}, "
              f"t = {t_final} ms (the hand-known optimum is 10)")
        hist = [json.loads(l) for l in open(os.path.join(d, "history.jsonl"))]
        losses = sum(1 for h in hist if h["status"] in ("FAIL", "INCONCLUSIVE", "UNSAFE", "WITHIN BAND"))
        ok = losses == 4 and len(open(os.path.join(d, "amendments.md")).read().split("**Amendment")) == 10
        bad += not ok
        print(("ok   " if ok else "FAIL ") + f"history keeps {losses} non-wins; 9 amendments written before their data")
        out = Climb(d, measure).step()
        ok = out.startswith("EXHAUSTED")
        bad += not ok
        print(("ok   " if ok else "FAIL ") + "ladder exhausted -> phase 9")
    print("hill_climb self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) < 2 or argv[0] not in ("init", "rule", "step", "adopt", "status"):
        print(__doc__)
        return 2
    cmd, d = argv[0], argv[1]
    if cmd == "init":
        os.makedirs(d, exist_ok=True)
        if os.path.exists(os.path.join(d, "climb.json")):
            print(f"REFUSED: {d} already holds a campaign")
            return 9
        cfg = json.load(open(argv[2]))
        write_atomic(os.path.join(d, "climb.json"), json.dumps(cfg, indent=1))
        print(f"INIT {d}: {len(cfg['candidates'])} candidate(s)")
        return 0
    cl = Climb(d)
    if cmd == "status":
        print(json.dumps(cl.state, indent=1, sort_keys=True))
        return 0
    cl.lock()
    try:
        out = {"rule": cl.rule, "step": cl.step, "adopt": cl.adopt}[cmd]()
    finally:
        cl.unlock()
    print(out)
    word = out.split(":")[0]
    return 0 if word in ("RULED", "ALREADY RULED", "PASS-ALONE", "ADOPTED", "EXHAUSTED", "NOTHING TO ADOPT") else \
        5 if word == "WAITING-OWNER" else 3 if "INCONCLUSIVE" in word else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
