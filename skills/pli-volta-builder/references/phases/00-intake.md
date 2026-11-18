# Phase 0: Intake

**Entry:** a request to build, serve or optimize a model on old cards, and no `BUILD-STATE.md` for it yet.

**Goal:** know the hardware, the model, the workload and the quality bar well enough to do the arithmetic of phase 2
and to rank candidates in phase 5. Everything you cannot learn now is written down as UNKNOWN with the command or
question that will settle it.

## Collect (read-only commands; ask the owner only what the machine cannot tell you)

Hardware
- Generation first: the compute capability (`nvidia-smi --query-gpu=name,compute_cap --format=csv`). Volta is
  7.0. If it is anything else, tell the user plainly that the pinned facts in `volta-facts.md` and the sm_70 kernel
  rules do not apply, and that phase 1 will establish this card's facts from its vendor documents and the engine
  fork's support for it. The rest of the method applies unchanged.
- Cards: model, memory per card, count. `nvidia-smi --query-gpu=index,name,memory.total,power.limit,clocks.max.sm --format=csv`
  (index, never UUID, in any file you may share).
- Topology: `nvidia-smi topo -m` (which cards share NVLink, which only PCIe), `lspci -tv` (switches, host bridges),
  ACS state on the bridges above the cards (`sudo lspci -vvv | grep -i acsctl`).
- Host: RAM size and speed (`free -g`, `dmidecode -t memory` if allowed), CPU cores, NVMe for weights, whether a
  second, smaller machine with the same card generation exists for rehearsals.
- Power and clocks: the current limits; who may change them (the owner).
- Software: driver version, CUDA toolkit, the engine fork and its commit if one runs already.

Model
- Geometry from the checkpoint's `config.json`: layers, hidden size, attention type, experts (routed and shared, top-k,
  expert width), vocabulary, drafter or MTP layers, maximum positions.
- Formats available: the author's checkpoint, vendor re-packs (NVFP4, MXFP4, FP8), community quants (GGUF, EXL3,
  AWQ); their bytes per weight and which tensors each keeps at full precision (read each `quantization_config`).
- What the engine fork already supports for this model (phase 1 confirms).

Workload (aggregates only; never copy a user's text)
- Prompt length per request: median, 90th percentile, maximum.
- New tokens per turn on a continued chat; how often a request begins with the previous request's whole prompt.
- Generated tokens per task, reasoning included, counted directly (not requests x median answer).
- Concurrency: share of time with one, two, three or more requests running.
- Requests per task; gaps between a conversation's requests.
- If no measurement exists, say so and plan to instrument the router or client first; until then rank candidates
  with the uncertainty written next to each.

Quality bar
- bit-identical to a reference build; close (closeness lines on public prompts); or free (any speed-up the owner
  accepts after seeing a quality comparison). Write which reference stands for "the model" (phase 4).

Owner's settings
- Who owns the server; the users and the notice they get before a stop; the serving port and the test port; the
  memory line (the most a card may hold under serving); the owner's number for parallel helpers.
- If the owner has no memory line, propose one and record it as the owner's decision once agreed: the PLI builds kept
  410 to 512 MiB free on 32 GB V100s (lines of 31,998 and 32,100 MiB of 32,510), and judged serving candidates
  against a ceiling about 300 MiB below the line. Smaller cards need a proportionally similar margin; a card that
  also drives a display needs more.

## Writes

- `BUILD-STATE.md` from `templates/BUILD-STATE.md` (the human-readable state) and `state.json` (the machine-readable
  copy: `phase`, `owner`, `serving`, `test_port`, `memory_line_mib`, `cards`, `layout`, `workload`, `quality_bar`, `unknowns`, `next`).
- The build's `AGENTS.md` and `CLAUDE.md` from the templates, with section 0 (front-line facts) started.

## Gate to phase 1

Every field filled or marked UNKNOWN with its settling command. The owner named (and, if this session is not the owner,
how the owner's word reaches it).

## Without the hardware at hand

Write the full command list above into `BUILD-STATE.md` under "to run on the machine", fill what the user told you,
and go on to phase 1 (it needs only the network) and phase 2 (it needs only numbers).
