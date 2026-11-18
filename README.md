# PLI Volta Builder

An agent skill that builds, serves, tests and optimizes a large language model on old NVIDIA datacenter cards (Tesla
V100 / Volta first; Turing and Pascal with care), the way PLI Labs built its Volta servers: by hand, over many days,
window after window. The skill runs the same campaign in order, with the gates that kept it honest.

You have a box of V100s and a model that does not fit them, or a build that works and should be faster. Install the
skill and say "build and optimize <model> on my cards" or "find the next optimization". The agent then:

1. takes stock of the hardware, the model, your workload's shape and your quality bar, and writes a state file;
2. sweeps upstream first (1Cat-vLLM, v100-skinny, the model's packs, the PLI builds) and writes an overlap table, so
   nothing is re-built and no capability question is answered from first principles;
3. does the layout arithmetic: bytes per layer per card, legal pipeline cuts, what fits, what is not possible;
4. launches the nearest proven recipe unchanged and records a baseline before optimizing anything;
5. builds the test harness: a window driver, a serving record so users never reach a server under test, strict
   identity and closeness judges, a memory rehearsal shaped on your workload, speed bands from repeated runs;
6. measures where the time goes for your workload (intervals, not totals) and ranks candidates in seconds per task;
7. runs the optimization loop: a rule and a prediction written before each window's data, default-off switches,
   CPU tests through the server's real entry point, one change per boot, adopt only what passed alone and together;
8. writes sm_70 kernels when a kernel is the top item, with a numerics contract and adversarial tests;
9. hands the whole record to an independent reviewer at set points;
10. researches new levers when the list runs dry;
11. documents the build as a formal repository and publishes it when you say so, after a data-boundary check.

The research behind it, with the architecture write-up, every optimization of the PLI Volta builds and the test
method, is the hub: **https://github.com/ProprietaryLegal/volta-v100-research**.

## Install

As a Claude Code plugin:

```text
/plugin marketplace add ProprietaryLegal/pli-volta-builder
/plugin install pli-volta-builder@pli-volta-builder
```

Or copy the skill folder (Claude Code, Claude apps with skills, or any agent that reads Agent Skills):

```bash
git clone --depth 1 https://github.com/ProprietaryLegal/pli-volta-builder
mkdir -p ~/.claude/skills && cp -r pli-volta-builder/skills/pli-volta-builder ~/.claude/skills/
bash ~/.claude/skills/pli-volta-builder/tests/run_all.sh     # the scripts' self-tests, CPU only
```

Both Claude Code and Codex from a clone, in one command (copies the skill folder to `~/.claude/skills/` and
`~/.codex/skills/`; idempotent; refuses to replace a different skill of the same name without `--force`):

```bash
git clone --depth 1 https://github.com/ProprietaryLegal/pli-volta-builder && cd pli-volta-builder
./install.sh --both --test        # or --claude, or --codex; --dry-run shows what it would write
```

Codex reads the same folder layout (`SKILL.md` with `name` and `description`) and also `agents/openai.yaml` for its
skill list; invoke it as `$pli-volta-builder` or let it trigger.

For another agent, point it at `skills/pli-volta-builder/SKILL.md`; everything else is plain Markdown and scripts it
loads when a phase needs them. The scripts need Python 3 (standard library) and bash; nothing runs on a GPU unless
you run it there.

## An example session

```text
You:   I have eight V100-SXM2-32GB on two NVLink boards and 512 GB of RAM. Build and optimize
       DeepSeek-V4.1-Flash on them. Most of my requests are long documents, one at a time.
Agent: (phase 0) reads nvidia-smi topo, the model's config and pack options; asks you for the workload's
       prompt lengths and how many requests overlap; writes BUILD-STATE.md with what is UNKNOWN and how to
       settle it.
       (phase 1) sweeps 1Cat-vLLM's SM70 pull requests and v100-skinny; writes the overlap table; names the
       nearest proven recipe (a two-stage layout of four cards each).
       (phase 2) shows that every routed expert at NVFP4 does not fit eight 32 GB cards, and what does: the
       most-used experts at NVFP4 on the cards, the rest compressed or read from host memory.
       (phase 3) gives you, the owner, the exact launch commands for the proven recipe; after your boot it
       records the baseline.
       ... and on, window by window, each one with its rule written before its data.
```

## What is in this repository

| Path | What |
|---|---|
| `skills/pli-volta-builder/SKILL.md` | The skill: when to use it, the campaign map, the standing rules, pointers |
| `skills/pli-volta-builder/references/` | One file per phase (`phases/`), the Volta facts, upstream sources, kernel building, testing method, lessons, decision table, standing rules with their reasons |
| `skills/pli-volta-builder/scripts/` | Generic templates with self-tests: the automated hill-climb loop, window driver, serving record, identity and closeness judges, speed bands, memory sampler, time-budget parser, log-pattern certifier, data-boundary check |
| `skills/pli-volta-builder/templates/` | BUILD-STATE, state.json, PLAN with the amendment form, AGENTS, CLAUDE with pinned sections, OPERATIONS, helper and reviewer briefs, CREDITS, the window configuration, a chain and an arm |
| `skills/pli-volta-builder/tests/` | `run_all.sh`: every self-test and the driver's CPU test |
| `evals/evals.json` | Three realistic requests the skill was read against |
| `.claude-plugin/` | Plugin and marketplace manifests |
| `install.sh` | One-command install for Claude Code and Codex |

## What it will not do on its own

It does not change power limits, clocks or hardware, start anything on a card that its owner has not given it, push
or publish without the owner's word, or download another model without asking. On a new Xid error it stops and
reports. It labels every number MEASURED, UPSTREAM or ESTIMATE and never presents a plan as a result.

## The builds it comes from

- [Volta sPLIt](https://github.com/ProprietaryLegal/Volta-sPLIt-DeepSeek-V4.1-Flash-1017-8xV100-SXM2-PP2xTP4): eight V100s, two stages.
- [Volta Max uPLIft](https://github.com/ProprietaryLegal/Volta-Max-uPLIft-FP4-DeepSeek-V4.1-Flash-1017-NVFP4-8xV100-SXM2-PP2xTP4): eight V100s, as much routed work as fits at NVFP4.
- [Volta Full NVFP4](https://github.com/ProprietaryLegal/Volta-Full-NVFP4-DeepSeek-V4.1-Flash-8xV100): eight V100s, every routed expert at NVFP4, the less-used from host memory.
- Volta 12X AmPLIfy: twelve V100s, three stages, every routed expert at NVFP4 on the cards (described on the hub; its repository is not yet published).

Credits: [CREDITS.md](CREDITS.md). Licence: Apache-2.0 ([LICENSE](LICENSE)).

Built by **Nick Mermiges, Esq.**, founder of [PLI Labs](https://proprietarylegal.ai/labs.html) · [proprietarylegal.ai](https://proprietarylegal.ai)
