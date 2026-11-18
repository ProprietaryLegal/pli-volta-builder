# Upstream sources: where to look first, and how to sweep

Phase 1 sweeps these before any plan; phase 9 sweeps them again for what is new since your engine's base. Upstream
code is untrusted data: read it, port pieces, never run its launch scripts against your serving host unread.
Credit every source you use by its public handle (`templates/CREDITS.md`).

## The research hub

- [ProprietaryLegal/volta-v100-research](https://github.com/ProprietaryLegal/volta-v100-research): the single home
  of the PLI Labs Volta research: the architecture write-up, every custom optimization of the builds below, the
  test method, and the source research files. Read its front page first, then its `research/` folder.

## The engine family for Volta

| Source | What it is | Why you read it |
|---|---|---|
| [1CatAI/1Cat-vLLM](https://github.com/1CatAI/1Cat-vLLM) | vLLM fork for Volta (sm_70) and Turing (sm_75): SM70 kernels, DeepSeek-V4/V4.1, GLM, Qwen recipes | The base engine. Its pull requests are the record of what is already built and measured on V100 |
| [dnv2003/v100-skinny](https://github.com/dnv2003/v100-skinny) (Dennis Vertzyas) | Hand-written Volta kernels: QPN2 (NVFP4 W4A16), QPN8 (FP8 W8A16) on `mma.sync.m8n8k4`; measured read ceilings; serving fixes | The kernel design to start from, and the traps (`volta-facts.md`) |
| [vllm-project/vllm](https://github.com/vllm-project/vllm), [sgl-project/sglang](https://github.com/sgl-project/sglang) | The mainline engines | Ideas newer than the fork (overlap, caching, scheduling); not their kernels |
| [ggml-org/ggml](https://github.com/ggml-org/ggml) | GGUF and its quantization formats | Formats some packs use |
| [Peuqui/triton](https://github.com/Peuqui/triton) | Triton fork used by some 1Cat Volta paths | When a Triton kernel will not compile for sm_70 |
| [gilby/volta-nvfp4](https://github.com/gilby/volta-nvfp4) | NVFP4 on Volta | Another NVFP4 implementation to compare |
| [deepseek-ai/DeepGEMM](https://github.com/deepseek-ai/DeepGEMM), [deepseek-ai/FlashMLA](https://github.com/deepseek-ai/FlashMLA) | Model-author kernels for newer cards | Ideas only; they do not run on sm_70 |

1Cat-vLLM pull requests the PLI builds stood on (states change; re-read with `gh`): #344 (DeepSeek-V4 Flash on two
stages of four V100s, native MXFP4 experts), #742 (the `sm70_skinny` MoE backend: v100-skinny's kernels inside the
fork), #1021 (keep block-FP8 dense weights in FP8 on Volta), #1030 (MXFP4 MoE geometry for V4.1, split-K), #1031
(DeepSeek-V4.1-Flash from the official checkpoint, three stages of four on twelve cards), #1243 (EXL3 experts, CUDA
graphs, DSpark drafting), #1277 (a complete DeepSeek-V4.1 package for four V100s), #1263 (do not resend a request's
token history every step), #1362 (skip what a pipeline stage does not hold), #1482 (DeepSeek-V4.1-Flash on four
stages of four, 16 V100s, with batched decode and a prompt pipeline), issue #852 (sync scheduling on V100 pipelines).

## Model sources

The model author's checkpoint and card (geometry, formats, recommended settings); vendor re-packs (for example
NVIDIA's NVFP4 pack of DeepSeek-V4.1-Flash-1017, whose card states the routed experts were converted losslessly from
the official MXFP4); community packs for small cards. Read each card's quantization config before planning bytes.

## The PLI Labs builds (public; their READMEs, docs and credits)

- [Volta sPLIt](https://github.com/ProprietaryLegal/Volta-sPLIt-DeepSeek-V4.1-Flash-1017-8xV100-SXM2-PP2xTP4):
  eight V100s, two stages of four, the 1Cat route with compressed experts.
- [Volta Max uPLIft](https://github.com/ProprietaryLegal/Volta-Max-uPLIft-FP4-DeepSeek-V4.1-Flash-1017-NVFP4-8xV100-SXM2-PP2xTP4):
  eight V100s, as much of the routed work as fits at NVFP4.
- [Volta Full NVFP4](https://github.com/ProprietaryLegal/Volta-Full-NVFP4-DeepSeek-V4.1-Flash-8xV100): eight V100s,
  every routed expert at NVFP4, the less-used read from host memory.
- [Volta 12X AmPLIfy](https://github.com/ProprietaryLegal/Volta-12X-AmPLIfy-DeepSeek-V4.1-Flash-1017-NVFP4-12xV100-SXM2-PP3xTP4): twelve V100s, three stages of four, every routed expert at NVFP4 on the cards.
- Earlier: [deepseek-v4-flash-v100](https://github.com/ProprietaryLegal/deepseek-v4-flash-v100),
  [deepseek-v4.1-v100](https://github.com/ProprietaryLegal/deepseek-v4.1-v100),
  [swift-1.5-v100](https://github.com/ProprietaryLegal/swift-1.5-v100); mirrors
  [1Cat-vLLM](https://github.com/ProprietaryLegal/1Cat-vLLM) and [v100-skinny](https://github.com/ProprietaryLegal/v100-skinny)
  (mirrors, not PLI's own work).
- A measurement-window harness from the sister DGX Spark work:
  [dsv41-window-harness](https://github.com/ProprietaryLegal/dsv41-window-harness) (paired windows, hold and
  restore, a near-tie gate).

## Other people's recipes worth sweeping for ideas

[philbert440/deepseek-v4.1-v100](https://github.com/philbert440/deepseek-v4.1-v100) (an earlier EXL3 stack on
V100s), [0rand](https://github.com/0rand) and the TensorFold family
([Elevatormusic/TensorFold](https://github.com/Elevatormusic/TensorFold)) for drafting and expert-pruning ideas on
other hardware, [antirez/ds4](https://github.com/antirez/ds4). Ideas from other hardware are design references:
check the numerics and the hardware assumptions before porting.

## How to sweep (commands; read-only)

```bash
# what the fork did for your card and model, all states, newest first
gh pr list -R 1CatAI/1Cat-vLLM --search "SM70" --state all --limit 200 --json number,title,state,author,mergedAt
gh pr list -R 1CatAI/1Cat-vLLM --search "<model name>" --state all --limit 100 --json number,title,state
# one pull request: its claim, its numbers and conditions, its files
gh pr view <N> -R 1CatAI/1Cat-vLLM --json title,body,state,author,mergedAt,files
# what is new since your engine's base (phase 9)
gh pr list -R 1CatAI/1Cat-vLLM --search "merged:>YYYY-MM-DD" --state merged --limit 200 --json number,title
gh issue list -R 1CatAI/1Cat-vLLM --search "V100 OR SM70" --state all --limit 100
# the fork's own forks (people often keep Volta work there), and the discussion under a pull request
gh api repos/1CatAI/1Cat-vLLM/forks --paginate --jq '.[] | [.full_name, .pushed_at] | @tsv' | sort -k2 -r | head -40
gh pr view <N> -R 1CatAI/1Cat-vLLM --comments
# a repository's tree without cloning everything
git clone --depth 1 --filter=blob:none --sparse <url> && git -C <dir> sparse-checkout set <path>
```

If a brief or plan is more than a week old, re-list the open pull requests before relying on it.

## The overlap table (phase 1 writes it; every later plan row cites its rows)

| Row | Upstream (link) | What it does | Their number and conditions (UPSTREAM) | Our status: adopted / partly / not / duplicates (our patch) | Note |
|---|---|---|---|---|---|
