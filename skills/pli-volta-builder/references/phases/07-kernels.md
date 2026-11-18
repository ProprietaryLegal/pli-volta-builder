# Phase 7: Kernels

**Entry:** the top-ranked candidate is time inside a kernel (or between kernels) that no upstream kernel covers at
your shapes.

**Do:** follow `../kernel-building.md` in order: upstream kernels first; size by speed of light and by the
measured interval; the order of attack (capacity-sized work, then kernel count and gaps, then bytes); the sm_70
budget; the numerics contract written first; adversarial unit tests and compute-sanitizer; a default-off switch;
then the window of phase 6 decides.

**Writes:** the kernel source in the build's kit, its tests, its row in the lever table (switch, source, contract,
result), and an upstream pull request when it works (with its measured numbers and conditions).

**Gate:** none of its own: the kernel is a phase 6 candidate like any other, and only the end-to-end window decides.

**Inventory first.** Before the first kernel on a new layout, write a kernel inventory: which kernel runs each part
of decode and of a prompt chunk at this build's shapes (row counts per stage, tensor-parallel width, formats), and
the gaps where a shape falls between dispatch ranges. The PLI builds keep one per build (on the hub's research
pages): it is the map for this phase.
