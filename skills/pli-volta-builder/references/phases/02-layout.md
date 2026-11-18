# Phase 2: Layout arithmetic

**Entry:** phases 0 and 1 done (geometry, cards, formats, upstream layouts known).

**Goal:** decide what fits where, with the arithmetic shown, and say plainly what is NOT possible on these cards.

## Do

1. **Bytes per layer.** For each tensor kind (attention, dense or shared MLP, routed experts, norms, embeddings,
   head, drafter, index and cache structures), bytes = parameters x bits per weight / 8, plus scales (for example
   NVFP4: 4-bit codes plus one FP8 scale per 16 codes plus a per-tensor scale, about 4.5 bits per weight; MXFP4: one
   power-of-two scale per 32 codes, about 4.25). Read the real size from the pack's files when you can: an
   engine's on-card record may be padded or repacked (one NVFP4 expert record measured 4,874,240 bytes per card on
   four-way tensor parallelism, MEASURED in the engine code of the twelve-card build).
2. **Per card.** Under tensor parallelism of t, most weights divide by t; some are replicated (check the engine).
   Add per card: the KV cache for the context and slot count you plan, CUDA graphs, the allocator's working memory
   for a prompt chunk, the drafter, communication buffers. Subtract from the physical card size the owner's memory
   line, not the card size.
3. **Legal stage cuts.** A pipeline stage can only start where the engine allows (shared caches, index sources,
   cross-layer state). Read the model's code and the upstream layout pull requests; list the legal cut points. The
   last stage usually carries the head and the drafter: it holds fewer layers.
4. **Enumerate layouts** that fit: stages x tensor-parallel width, cut points, what stays at full precision, what is
   compressed, what sits in host memory (exact but slow: each miss crosses PCIe). Tensor parallel inside an NVLink
   board, pipeline across boards. Cards with no NVLink at all pay for every tensor-parallel all-reduce over PCIe on
   every layer: keep both the best tensor-parallel and the best pipeline layout as candidates and let phase 3's
   baseline (or the upstream recipe's figures for that card) decide.
5. **Answer the card-count what-ifs first, as a table**, before any build: for 8, 10, 12 (or whatever counts the
   owner could reach) cards, what fits at each precision, the share of experts at the higher precision, the host
   memory left for lookup tables, and a speed ESTIMATE with its basis. Owners ask these before they buy or rewire.
   If the model does not fit at the precision wanted, consider mixed precision by measured expert use
   (`../expert-promotion.md`).
6. **Show what is not possible**, with the arithmetic (for example: "every routed expert at NVFP4 is 278.9 GiB of
   records; eight 32 GB cards hold 254 GiB; it does not fit on eight cards; twelve hold it at 24.40 / 24.40 / 20.92
   GiB per card on three stages", ARITHMETIC from the twelve-card build's plan).
7. **Choose** the layout with margin under the memory line at the slot count and context the workload needs, and
   the board order (which board holds which stage; keep the first hand-off inside one PCIe switch where possible).
8. Estimate speed only as an ESTIMATE with its basis (an upstream figure on a similar layout, scaled with the
   arithmetic shown).

## Writes

PLAN.md sections 1 to 5 (`templates/PLAN.md`): the answer in one paragraph, the facts with labels, the candidate
layouts table, memory per card for the chosen one, which board holds which stage, what the engine must change (the
kit) to run it.

## Gate to phase 3

One chosen layout whose per-card arithmetic ends under the memory line with a stated margin, every legal-cut claim
cited to code or an upstream pull request, and the list of engine changes needed (empty is best: then phase 3 can
launch the upstream recipe as is).
