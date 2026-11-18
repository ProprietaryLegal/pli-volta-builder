#!/usr/bin/env python3
"""serving_record.py write|check CONFIG.json RECORD.json : the pair rule's record.

The pair rule: a configuration is checked IN FULL on the test port (boot checks, identity against the accepted
capture, the memory rehearsal shaped on the workload) and only then served on the public port, by a boot that sends
no request. The record ties that full check to the exact bytes and settings it checked. While the record matches,
a return from a test window may boot the serving configuration directly; any change of engine kit, profile,
switches, slot count or memory limit makes it stale and the full check is owed again.

CONFIG.json names what defines the serving configuration:
    {"files": ["engine/kit/MANIFEST", "run/profile.yaml"],     # hashed (sha256 of the bytes)
     "settings": {"SLOTS": "4", "CARD_LIMIT_MIB": "31998"},    # compared as strings
     "ignore_lines": ["port:"]}                                 # profile lines left out of the hash (the port)
Paths are relative to CONFIG.json's folder.

  write  computes the fingerprint and writes RECORD.json. Run it ONLY after the full check passed.
  check  recomputes it and compares: MATCH (exit 0) or STALE with every differing item (exit 36).
         A missing or unreadable record or file is INCONCLUSIVE (exit 3): the full check is owed.

`--self-test` builds a temporary configuration and walks write / match / change / stale by hand.
"""
import hashlib
import json
import os
import sys
import tempfile


def fingerprint(config_path):
    base = os.path.dirname(os.path.abspath(config_path))
    cfg = json.load(open(config_path))
    ignore = tuple(cfg.get("ignore_lines", []))
    files = {}
    for rel in cfg.get("files", []):
        with open(os.path.join(base, rel), "rb") as f:
            lines = f.read().splitlines(keepends=True)
        kept = b"".join(l for l in lines if not l.decode("utf-8", "replace").lstrip().startswith(ignore)) if ignore else b"".join(lines)
        files[rel] = hashlib.sha256(kept).hexdigest()
    return {"files": files, "settings": {k: str(v) for k, v in cfg.get("settings", {}).items()}}


def compare(rec, now):
    diffs = []
    for kind in ("files", "settings"):
        a, b = rec.get(kind, {}), now.get(kind, {})
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                diffs.append(f"{kind[:-1]} {k}: record {str(a.get(k))[:16]} now {str(b.get(k))[:16]}")
    return diffs


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) != 3 or argv[0] not in ("write", "check"):
        print(__doc__)
        return 2
    mode, cfg, rec_path = argv
    try:
        now = fingerprint(cfg)
    except (OSError, ValueError) as e:
        print(f"SERVING RECORD INCONCLUSIVE: cannot fingerprint the configuration ({e}); the full check is owed")
        return 3
    if mode == "write":
        with open(rec_path, "w") as f:
            json.dump(now, f, indent=1, sort_keys=True)
        print(f"SERVING RECORD WRITTEN: {len(now['files'])} file(s), {len(now['settings'])} setting(s)")
        return 0
    try:
        rec = json.load(open(rec_path))
    except (OSError, ValueError):
        print("SERVING RECORD INCONCLUSIVE: no readable record; the full check is owed")
        return 3
    diffs = compare(rec, now)
    if diffs:
        print("SERVING RECORD STALE: the full check is owed before this configuration serves")
        print("\n".join("  " + d for d in diffs))
        return 36
    print("SERVING RECORD MATCH: the serving boot may run without a new full check")
    return 0


def self_test():
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "profile.yaml"), "w").write("port: 8001\nmax-num-seqs: 4\n")
        cfg = {"files": ["profile.yaml"], "settings": {"SLOTS": 4}, "ignore_lines": ["port:"]}
        cp, rp = os.path.join(d, "c.json"), os.path.join(d, "r.json")
        json.dump(cfg, open(cp, "w"))
        steps = []
        steps.append(("write", main(["write", cp, rp]), 0))
        steps.append(("match", main(["check", cp, rp]), 0))
        # changing only the port line must still MATCH (the port is ignored by design)
        open(os.path.join(d, "profile.yaml"), "w").write("port: 8000\nmax-num-seqs: 4\n")
        steps.append(("port only", main(["check", cp, rp]), 0))
        # one slot more in the profile -> STALE 36
        open(os.path.join(d, "profile.yaml"), "w").write("port: 8000\nmax-num-seqs: 5\n")
        steps.append(("profile changed", main(["check", cp, rp]), 36))
        open(os.path.join(d, "profile.yaml"), "w").write("port: 8000\nmax-num-seqs: 4\n")
        cfg["settings"]["SLOTS"] = 5
        json.dump(cfg, open(cp, "w"))
        steps.append(("setting changed", main(["check", cp, rp]), 36))
        os.remove(rp)
        steps.append(("no record", main(["check", cp, rp]), 3))
    for name, got, want in steps:
        bad += got != want
        print(f"{'ok  ' if got == want else 'FAIL'} {name}: exit {got} (want {want})")
    print("serving_record self-test:", "PASS" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
