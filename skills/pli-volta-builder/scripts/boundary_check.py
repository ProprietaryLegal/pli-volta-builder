#!/usr/bin/env python3
"""boundary_check.py TREE [--deny DENY.txt] [--max-bytes 1048576] : the data-boundary check before a commit or a
publish. One run of this plus one human (or independent) privacy read is the check; then publish.

Flags, per file and line:
  size       a file over --max-bytes (weights, captures and logs do not belong in a repository; reference them by
             path and sha256)
  extension  weight, archive, array and capture formats (.safetensors .gguf .bin .pt .pth .npz .npy .pkl .tar .gz
             .tgz .zip .zst .7z .jsonl)
  gpu-id     a GPU UUID (GPU-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) or MIG UUID
  ip         an IPv4 address other than 127.0.0.1 and 0.0.0.0
  email      an e-mail address, except GitHub noreply addresses
  home-path  an absolute home path (/home/<name>/, /Users/<name>/, C:\\Users\\<name>\\)
  secret     common token shapes (ghp_, github_pat_, hf_, sk-, AKIA..., "PRIVATE KEY")
  deny       any regex from DENY.txt (one per line, case-insensitive; # comments): YOUR host names, people's and
             clients' names, private repository names, private paths, session and agent names. KEEP DENY.txt OUT
             OF THE REPOSITORY: it is itself private.
A line that contains the marker "boundary: allow" is skipped (use it sparingly, in documentation of the rule only).

Exit 0 CLEAN, 1 HITS (every hit printed), 2 usage. The tree is walked whole (hidden folders too, but not .git).
`--self-test` builds a temporary tree with one planted item per rule and checks each is found.
"""
import argparse
import os
import re
import sys
import tempfile

EXT = {".safetensors", ".gguf", ".bin", ".pt", ".pth", ".npz", ".npy", ".pkl", ".tar", ".gz", ".tgz", ".zip",
       ".zst", ".7z", ".jsonl"}
RULES = [
    ("gpu-id", re.compile(r"\b(GPU|MIG)-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")),
    ("ip", re.compile(r"\b(?!127\.0\.0\.1\b)(?!0\.0\.0\.0\b)(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("home-path", re.compile(r"(/home/[a-z_][\w.-]*/|/Users/[\w.-]+/|C:\\Users\\[\w.-]+\\)")),
    ("secret", re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|\bhf_[A-Za-z0-9]{25,}|\bsk-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|PRIVATE KEY-----)")),  # boundary: allow (a planted test value)
]
ALLOW = "boundary: allow"


def scan(tree, deny, max_bytes):
    hits = []
    for root, dirs, files in os.walk(tree):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, tree)
            if os.path.getsize(path) > max_bytes:
                hits.append(f"{rel}: size {os.path.getsize(path)} bytes")
            if os.path.splitext(name)[1].lower() in EXT:
                hits.append(f"{rel}: extension")
            for rx in deny:
                if rx.search(rel):
                    hits.append(f"{rel}: deny (in the path) {rx.pattern}")
            try:
                with open(path, encoding="utf-8") as f:
                    lines = f.readlines()
            except (UnicodeDecodeError, OSError):
                hits.append(f"{rel}: not readable as text (binary?)")
                continue
            for n, line in enumerate(lines, 1):
                if ALLOW in line:
                    continue
                for rule, rx in RULES:
                    if rx.search(line):
                        hits.append(f"{rel}:{n}: {rule}")
                for rx in deny:
                    if rx.search(line):
                        hits.append(f"{rel}:{n}: deny {rx.pattern}")
    return hits


def load_deny(path):
    if not path:
        return []
    out = []
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(re.compile(line, re.I))
    return out


def self_test():
    planted = {
        "a.md": "the card GPU-1a2b3c4d-1111-2222-3333-444455556666 failed\n",  # boundary: allow (a planted test value)
        "b.md": "reach it on 192.168.1.20 or 127.0.0.1\n",  # boundary: allow (a planted test value)
        "c.md": "write to someone@example.com; commits as 1+x@users.noreply.github.com\n",  # boundary: allow (a planted test value)
        "d.md": "the log is in /home/alice/logs\n",  # boundary: allow (a planted test value)
        "e.md": "token ghp_ABCDEFGHIJKLMNOPQRSTUVWX12\n",  # boundary: allow (a planted test value)
        "f.md": "served from host bigbox\n",
        "w.safetensors": "x",
        "ok.md": "nothing private here; version 1.2.3; port 8000\n",
    }
    want = {"a.md:1: gpu-id", "b.md:1: ip", "c.md:1: email", "d.md:1: home-path", "e.md:1: secret",
            "f.md:1: deny bigbox", "w.safetensors: extension"}
    with tempfile.TemporaryDirectory() as d:
        for k, v in planted.items():
            open(os.path.join(d, k), "w").write(v)
        open(os.path.join(d, "big.txt"), "w").write("x" * 2000)
        hits = set(scan(d, [re.compile("bigbox", re.I)], 1000))
    want.add("big.txt: size 2000 bytes")
    missing, extra = want - hits, hits - want
    for h in sorted(want):
        print(("ok   found " if h in hits else "FAIL missed ") + h)
    for h in sorted(extra):
        print("FAIL unexpected " + h)
    ok = not missing and not extra
    print("boundary_check self-test:", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    p = argparse.ArgumentParser()
    p.add_argument("tree")
    p.add_argument("--deny")
    p.add_argument("--max-bytes", type=int, default=1048576)
    a = p.parse_args(argv)
    hits = scan(a.tree, load_deny(a.deny), a.max_bytes)
    for h in hits:
        print(h)
    if hits:
        print(f"BOUNDARY HITS: {len(hits)}; fix each before any commit or publish")
        return 1
    print("BOUNDARY CLEAN" + ("" if a.deny else " (no deny list given: your private names were NOT checked)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
