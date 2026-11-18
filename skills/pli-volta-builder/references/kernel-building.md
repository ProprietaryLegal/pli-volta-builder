# Building kernels for sm_70

When phase 5's time budget names a kernel as the place the time goes, and no upstream kernel already covers the
shape (phase 1's table), write one. These rules come from the kernel campaigns of the PLI Volta builds; the facts
they rest on are in `volta-facts.md`.

## Before writing a line

1. **Upstream first.** v100-skinny's QPN kernels, the 1Cat-vLLM SM70 kernels and their pull requests. Start from
   their code and their measured number.
2. **Size it.** Speed of light = bytes moved / ~720 GB/s per card for decode-shaped work, FLOPs / ~125 TFLOPS for
   prompt-shaped work. Convert to milliseconds per decode round (or per prompt chunk) against the MEASURED round of
   your build, and to seconds per task with the workload's units (`scripts/timebudget_parse.py rank`). Under about
   0.3 ms per round is not measurable end to end: do not build it alone.
3. **Order of attack.** Remove work that grows with capacity or context first (on the PLI builds, reducing the
   long-context index over only its live prefix was the largest single kernel win); then cut kernels and the gaps
   between them (a decode round ran about two thousand kernels; bubbles cost milliseconds per stage); then cut bytes.
   Never add chains of small torch operations per layer: one such design added about 50 operations per layer and
   cost +6.9 ms per round.
4. **Size a fusion by the kernels it removes,** not by launch gaps: under CUDA-graph replay kernels start about
   0.3 microseconds apart, and profiled small kernels read about 1.8 times their real length. Subtract the work that
   moves into the fused kernel.

## Writing it

- sm_70 has `mma.sync.m8n8k4` (FP16 in, FP16 or FP32 accumulate), WMMA, `dp4a`, `lop3`, shuffles. It has no
  `cp.async`, `ldmatrix`, TMA, `wgmma`, BF16, FP8/FP4 or INT8 MMA. Port ideas, not code.
- Budget: at most 96 KB shared memory per SM (opt-in above 48 KB), at most 255 registers per thread, zero spills
  (check `-Xptxas -v`), hot loops under about 12 KiB of instructions, grids sized for 80 SMs.
- For low-bit weights at decode row counts: decode the weights in registers into FP16 fragments, prepack the
  weights once into fragment order (the v100-skinny design), keep no persistent FP16 copy, and dispatch by row
  count (a kernel that wins at 1 to 8 rows can lose at 32).
- Pin the toolchain: CUDA 12.x; the PyTorch build your engine uses (its C++ ABI); build the extension with the
  serving environment's Python while nothing serves from that environment; keep the replaced library as
  `<lib>.pre-<change>` for rollback.
- Every new kernel goes behind a default-off switch, and the switch-off path is proven unchanged (identity against
  the accepted capture with the switch off).

## The numerics contract (write it before the code)

- Same reduction order as what it replaces: bitwise equal is the bar (identity judge).
- Another reduction order: state the tolerance, and pass the end-to-end closeness lines (greedy identical, or flips
  only at traced near-ties). Autotuned configurations are numerics changes; dynamic tuning has caused output
  differences upstream.

## Testing it

- Adversarial unit tests: every row count from 1 to (draft depth + 1) and the prompt-chunk sizes; every pipeline
  stage and layer role; ragged K; sizes 0, 1 and maximum; outputs into fresh NaN-poisoned buffers; compare with a
  plain reference implementation in higher precision.
- `compute-sanitizer` with memcheck, racecheck and synccheck.
- An AI-written kernel can reward-hack a weak harness (return early, read the reference's buffer, special-case the
  test shapes). Review the kernel against the tests, and test shapes the author did not see.
- Then the end-to-end window: one boot with the switch off, one with it on, same window; ABBA when the predicted
  gain is near the band; quiet CPU; an untimed warm-up request after each boot. Only the end-to-end result decides;
  never drop or keep a kernel on its microbenchmark alone.

## Recording it

Each kernel's row in the build's lever table: switch name, upstream source or "own", the numerics contract, the
end-to-end result with its window, and its state (adopted, rejected with numbers, candidate). Send what works back
upstream as a pull request with its measured numbers and conditions.
