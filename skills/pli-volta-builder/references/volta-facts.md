# Front-line facts: Volta (sm_70) and its neighbours

Read before any plan. Labels: PUBLISHED (vendor document), UPSTREAM (someone else's measured number, with its
source; true for the conditions it states), MEASURED (on the PLI Labs builds, conditions given), ESTIMATE (arithmetic
shown). Facts change: re-check a line before a decision rests on it, and add what you verify to the build's own
`AGENTS.md` section 0 with the date.

## The card

| Fact (Tesla V100 SXM2) | Value | Label, source |
|---|---|---|
| Streaming multiprocessors | 80 | PUBLISHED, [Volta whitepaper](https://images.nvidia.com/content/volta-architecture/pdf/volta-architecture-whitepaper.pdf) |
| Memory | 16 or 32 GB HBM2, about 900 GB/s peak | PUBLISHED, whitepaper |
| Measured read ceiling | about 879 GB/s read, 822 GB/s copy (V100-SXM2-16GB) | UPSTREAM, [v100-skinny](https://github.com/dnv2003/v100-skinny) results |
| Tensor cores | FP16 only: about 125 TFLOPS FP16 at 1530 MHz boost | PUBLISHED, whitepaper |
| Per SM | 64K 32-bit registers, 2,048 threads, 128 KB L1/shared (up to 96 KB shared, opt-in above 48 KB) | PUBLISHED, whitepaper; [CUDA programming guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/) compute capability table |
| L2 | 6 MB | PUBLISHED, whitepaper |
| NVLink 2 | up to six links per SXM2 card; on 4-card and 8-card boards the cards of one board are linked, boards are joined by PCIe | PUBLISHED, whitepaper; check your board with `nvidia-smi topo -m` |

## What sm_70 can and cannot do

- PUBLISHED ([PTX ISA](https://docs.nvidia.com/cuda/parallel-thread-execution/)): the only `mma.sync` shape is
  `m8n8k4` with FP16 inputs and FP16 or FP32 accumulate (and WMMA 16x16x16 on top of it). No `ldmatrix` (sm_75),
  no `cp.async` (sm_80), no `m16n8k16`, no BF16, no FP8, FP4 or INT8 MMA, no TMA, no `wgmma`. `dp4a`, `lop3` and
  warp shuffles exist. Kernels written for Ampere or Hopper need a rewrite, not a port: port ideas, not code.
- So every low-bit format (NVFP4, MXFP4, block FP8, GGUF quants, EXL3) is decoded in software into FP16 `mma.sync`
  operands. On Volta a low-bit format pays by cutting the BYTES read at decode-sized row counts, not by faster math.
  "FP4 cannot help on V100" is wrong: an NVFP4 W4A16 kernel ran at 679.5 GB/s, 77 % of the read ceiling, at one row
  (UPSTREAM, v100-skinny QPN2, `results/kernel_matched_20260819.csv`).
- No FlashAttention-2 on sm_70 upstream; the Volta forks carry their own attention paths.
- Toolchain: CUDA 13.0 dropped offline compilation for sm_70 and older (PUBLISHED, CUDA 13.0 release notes): build
  with CUDA 12.x. Check that your PyTorch wheel lists `sm_70` (`python -c "import torch;
  print(torch.cuda.get_arch_list())"`). Triton's upstream support for sm_70 is limited; the 1Cat-vLLM project uses a
  Triton fork for some Volta paths ([Peuqui/triton](https://github.com/Peuqui/triton)); prefer CUDA C++ for hot paths.

## The bandwidth law

- ESTIMATE: ridge point about 125 TFLOPS / 0.879 TB/s, roughly 140 FLOP per byte. A weight multiply with M rows
  does about 2M FLOP per weight byte in FP16 terms (more per byte for low-bit weights), so decode (M from 1 to a few
  dozen rows with drafting) sits far below the ridge: decode is bound by bytes read and by per-step overhead, never
  by math. Prompt reading (thousands of rows) is compute-bound.
- Speed of light for a decode change: bytes removed / ~720 GB/s per card (a realistic kernel ceiling), or FLOPs /
  125 TFLOPS for prompt reading. Under about 0.3 ms per round is not measurable end to end on these builds.
- In the PLI builds' measured decode round, weight bytes were NOT what dominated: kernel count, gaps between
  kernels, small glue operations and the index for long contexts were. Profile before you assume (phase 5).

## Many cards

- Tensor parallelism inside one NVLink board; pipeline parallelism across boards over PCIe. A pipeline step carries
  one request on the engines these builds use, so more slots keep more chats warm but do not batch decode.
- PCIe switches with ACS (Access Control Services) redirect enabled can hang card-to-card transfers until it is
  cleared (MEASURED on the twelve-card build). Check `lspci -vvv` for `ACSCtl` on the bridges above the cards; the
  launcher should refuse to start while a bridge redirects. A reboot can restore redirect unless a kernel
  parameter disables it.
- Probe every hand-off pair of cards (send and receive at the sizes the engine uses) before the first boot of a
  layout.
- Power: a power cap throttles SM clocks under load and does not lower the HBM clock. MEASURED on twelve V100s,
  150 W to 200 W at a 1,477 MHz clock cap: prompt reading +13.7 %, decode within 2 % (one run). Clock and power are
  the owner's settings.

## Serving traps on Volta (UPSTREAM unless labelled)

1. FP8 KV cache forced scalar paged attention on SM70: +4.82 ms per round (v100-skinny). Do not copy
   `--kv-cache-dtype fp8` from a model card written for newer cards.
2. A decode partition derived from `--max-model-len` taxes every round (up to 2.59 ms at 32,768; v100-skinny
   `results/partition_fix_20260819.md`).
3. Asynchronous scheduling on a two-stage V100 pipeline cost about a third of single-stream decode; sync
   scheduling gave +55 % ([1Cat-vLLM issue #852](https://github.com/1CatAI/1Cat-vLLM/issues/852)).
4. Dynamic FP8 small-shape tuning caused output differences ([1Cat-vLLM #1187](https://github.com/1CatAI/1Cat-vLLM/pull/1187)).
5. A block-FP8 dense path wins only up to about 16 rows; dispatch by row count ([#1021](https://github.com/1CatAI/1Cat-vLLM/pull/1021)).
6. A draft method corrupted output with its default sampler ([#1269](https://github.com/1CatAI/1Cat-vLLM/issues/1269)).
7. Greedy local drafting beat probabilistic drafting by 10 to 25 acceptance points at a sharp sampler setting
   (v100-skinny), but probabilistic drafting won at temperature 1.0 / top-p 1.0 on DeepSeek-V4
   ([#183](https://github.com/1CatAI/1Cat-vLLM/pull/183)): check the conditions before copying either.
8. Microbenchmarks mislead both ways on graphed decode (MEASURED; `lessons.md`).

## Neighbours (PUBLISHED; verify for your exact card)

| Generation | Cards | Compute capability | Tensor cores | Notes |
|---|---|---|---|---|
| Pascal | P100 (HBM2, ~732 GB/s), P40 (GDDR5, ~346 GB/s) | 6.0 / 6.1 | none | P100 has fast FP16; P40 has very slow FP16 and fast INT8 `dp4a`. No `mma.sync`. CUDA 13 dropped them too. Check whether your engine fork supports them at all before planning |
| Volta | V100 SXM2 / PCIe, Titan V | 7.0 | FP16 `m8n8k4` | this file |
| Turing | T4 (~320 GB/s), RTX 20 series, Quadro RTX | 7.5 | FP16 and INT8/INT4 MMA (`m16n8k8`, `m8n8k16`), `ldmatrix` | 1Cat-vLLM has Turing work (for example #1278); many Ampere-era kernels port more easily than to Volta, but `cp.async` is still missing |

Sources: [CUDA GPUs compute capability list](https://developer.nvidia.com/cuda-gpus), each card's datasheet, the PTX
ISA's per-instruction target requirements.
