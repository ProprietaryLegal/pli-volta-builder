# Phase 3: First light

**Entry:** a chosen layout (phase 2) and the nearest proven recipe (phase 1).

**Goal:** a server that answers correctly, with a recorded baseline, before any optimization. The owner's rule:
launch the proven recipe first; validate pieces only if the launch misbehaves.

## Do (the owner session only; the hardware owner's word for the first boot on that machine)

1. Install the fork at the recipe's commit in the build's OWN tree (never inside another build's tree or
   environment), its environment pinned (CUDA 12.x; a PyTorch wheel whose `torch.cuda.get_arch_list()` includes your card's architecture: sm_70 for Volta, sm_75
   for Turing). Downloading the weights of
   the model the owner named, in the pack phase 2 chose, is part of the request; a different model, quant or
   drafter needs the owner's word first. Record every download: repository, revision, sha256, size.
2. Probe the hardware path before the first boot: every card-to-card hand-off pair the layout uses (send and
   receive at the engine's sizes), ACS cleared on the bridges, the Xid count read and written down.
3. Launch with the recipe's documented flags unchanged (plus only what the layout requires). Keep the
   upstream-known Volta settings: synchronous scheduling on pipelines, no FP8 KV cache.
4. Smoke: health, a short completion, a tool call if the model uses tools, a long prompt near the context the
   workload needs, a needle check in it. Then read the boot log whole once: residency lines, warnings, fallbacks.
5. Baseline, labelled MEASURED with power limit and boot: one request on fresh text and on repeated text (tok/s and
   ms per round), one long prompt read (tok/s), load time, card memory after warm-up, concurrency if slots exist.
6. Capture the first reference answers (public prompts, greedy, token ids and log-probabilities): the start of the
   accepted capture.

## Writes

PLAN.md section 9's first result amendment (what booted, the baseline), `BUILD-STATE.md` (serving or not, on which
port), the boot log's real lines kept for phase 4's patterns (a copy on the analysis machine).

## Gate to phase 4

A server answered correctly on the smoke list and a baseline exists. If the layout needed engine changes, their kit
booted with its switches off and gave the upstream recipe's answers.

## If it does not answer correctly

Do not start optimizing. Reproduce on the smallest configuration that fails; run the engine's real loop on CPU if the
failure looks like scheduling (one three-stage layout produced junk from token 1 because nothing spaced a request's
decode steps by the pipeline depth); compare with the fork's own layout before blaming the hardware. Persist: each
failed boot names the next hypothesis.
