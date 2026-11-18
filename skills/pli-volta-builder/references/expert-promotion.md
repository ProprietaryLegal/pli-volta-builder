# Lever: mixed precision by measured expert use ("expert promotion")

When a mixture-of-experts model does not fit the cards at the precision wanted, do not compress every expert the
same way. Most decode work lands on a minority of experts. Count which experts the owner's own workload routes to,
keep those at the higher precision, compress the rest, and judge how close the result is to the full higher-precision
model. This is the technique behind Volta Max uPLIft (its public README describes the result: the experts that
carried most of the decode routes kept at NVIDIA's NVFP4 precision, the rest from smaller IQ2-class records, every
expert on the cards).

## When to use it

Phase 2 shows that every routed expert at the higher precision does not fit under the memory line, and the owner
wants more quality than an all-compressed build gives (or the speed of holding everything on the cards rather than
reading part of it from host memory). Ask first whether more cards are an option (phase 2's card-count table): the
cleanest answer to "does not fit" is more memory.

## The recipe

1. **Two packs of the same experts.** A higher-precision one (for example a vendor's NVFP4 pack) and a smaller one
   (for example an IQ2-class GGUF). Check they are the same model revision. If the higher-precision pack is a
   lossless conversion of the official weights (its card or your own check says so), say so; if you fold its scales
   into another format for the kernel, prove the fold exact on real tensors (values bit-equal) before relying on it.
2. **Count routes on the owner's real workload.** Run the server (any build that routes the same way: the router
   is part of the trunk, check it is the same precision) with a per-layer, per-expert route counter while it serves
   the owner's real requests, or a replay of them, on the owner's machine. Count decode routes and prompt routes
   separately: decode is what the promoted experts speed and protect. Check that counts taken on one engine or
   precision transfer to the target: the router's inputs change slightly with precision; compare the top-ranked
   experts of two counts and say how much they overlap.
3. **Rank by use per byte.** Each promoted expert costs (higher-precision bytes minus compressed bytes) per card.
   Rank experts by decode routes per extra byte, layer by layer or globally, and promote in that order until each
   stage's cards reach the memory line (with the KV cache, graphs and working memory of the slot count and context
   the workload needs already counted). Stages differ in what else they hold: fill each stage to its own line.
4. **Write the tier map** (which expert is promoted, per layer and stage) as a private file the launcher reads; the
   engine logs, per rank, how many experts it placed in each tier and a digest of the map, and the boot check
   compares them with the plan.
5. **Report the share of the work at the higher precision**: the fraction of decode routes that land on promoted
   experts, measured with the route counters on texts of each kind, and say whether each text was in the sample the
   counts came from (in-sample) or not (out-of-sample). Never present an in-sample share as general.
6. **Judge closeness against the full higher-precision model** with the strict judges, by a rule written before the
   data: next-token agreement and log-probability distance (or KL on shared tokens) against a reference that holds
   every expert at the higher precision (for example a layout that reads the experts that do not fit from host
   memory: slow but exact), on public prompts of several kinds, with the reference repeated against itself as the
   noise floor. Report it beside the all-compressed build's distance to the same reference; that comparison is the
   lever's own before and after, not a ranking of builds. A reading path that differs from the decode path (for
   example compressed experts used while reading a prompt) is a separate configuration: its quality is not
   established until it has its own closeness run.
7. **Re-count when the workload changes** (a new kind of task, a new prompt template): the promotion is fitted to the
   workload it was counted on.

## What stays private

The route counts, the tier map and anything that would let someone reconstruct them (per-expert counts, which
experts were promoted) are the owner's data: they describe what the owner's workload does. Keep them on the owner's
machines, out of every repository, model card, log and report that may be published. Aggregates are publishable:
how many experts per stage are promoted, the share of decode routes on promoted experts by kind of text, and the
closeness figures.

## Where it fits in the campaign

Phase 2 sizes it (how many experts fit at the higher precision per stage). Phase 3 can launch the all-compressed
recipe first. The promotion is then a phase 6 candidate with closeness lines (it moves rounding on purpose), its own
build tree, and its own reference arm. A later build with more cards may hold every expert at the higher precision;
the promoted build stays useful as the option for fewer cards.
