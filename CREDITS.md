# Credits

The method in this skill was worked out on PLI Labs' Volta builds; the engines, kernels and much of the knowledge
they stand on are other people's work. This skill copies no third-party code; it points to their work and tells the
agent to start from it.

| Whose | Work | Link | Role in the skill |
|---|---|---|---|
| 1CatAI and contributors | 1Cat-vLLM, the vLLM fork for Volta and Turing (SM70 kernels, DeepSeek-V4/V4.1, pull requests by many authors, among them yangzhuxinyzx, Peuqui, kezboard233, rivetphilbot and squibloads) | https://github.com/1CatAI/1Cat-vLLM | The engine family; phase 1 reads its pull requests first |
| Dennis Vertzyas (dnv2003) | v100-skinny: QPN2 (NVFP4 W4A16) and QPN8 (FP8 W8A16) Volta kernels, measured read ceilings, serving traps | https://github.com/dnv2003/v100-skinny | Kernel design and Volta facts (`references/volta-facts.md`) |
| vLLM project | vLLM | https://github.com/vllm-project/vllm | The engine underneath |
| SGLang project | SGLang | https://github.com/sgl-project/sglang | Ideas for overlap and scheduling |
| Peuqui | Triton fork used by Volta paths | https://github.com/Peuqui/triton | Toolchain note |
| Phil Tompkins (philbert440) | An earlier DeepSeek-V4.1 stack on V100s | https://github.com/philbert440/deepseek-v4.1-v100 | Upstream sweep list |
| 0rand, Elevatormusic and the TensorFold contributors | TensorFold and DGX Spark recipes | https://github.com/0rand, https://github.com/Elevatormusic/TensorFold | Ideas from other hardware |
| ggml-org | GGUF and its quantization formats | https://github.com/ggml-org/ggml | Formats |
| DeepSeek | DeepSeek-V4.1-Flash, DeepGEMM, FlashMLA | https://huggingface.co/deepseek-ai, https://github.com/deepseek-ai | The model the builds served; kernel ideas |
| NVIDIA | Volta architecture whitepaper, PTX ISA, CUDA documentation, the NVFP4 pack of DeepSeek-V4.1-Flash-1017 | https://docs.nvidia.com/cuda/ | Facts about the card; the expert weights of the NVFP4 builds |
| gilby | volta-nvfp4 | https://github.com/gilby/volta-nvfp4 | Upstream sweep list |
| 0xSero | `bench/hillclimb.py` of Inkling-Small-2-Sparks: the hill-climb driver design (step / measure / status, JSON state and JSONL history, one-setting candidate ladder with reasons, safety rails, revert on boot failure, quality as a hard gate, contended runs not comparable). Adapted (rewritten, generic, with our gates on top) in `skills/pli-volta-builder/scripts/hill_climb.py` under Apache-2.0 | https://github.com/0xSero/Inkling-Small-2-Sparks (Apache-2.0) | The automated loop of phase 6 (`references/hill-climb-loop.md`) |
| 0xSero | Sweep outcome states (valid, rejected, unsupported, unrun, infrastructure-invalid) and frozen run manifests: the idea only, no code (the repository has no licence file) | https://github.com/0xSero/omarchy-local-intelligence | Recording losses and run identity |
| 0xSero | Median-of-repeats speed sweeps on public prompt text: the practice, no code copied | https://github.com/0xSero/inkling2-exl3 (MIT) | Testing method |
| Anthropic | The Agent Skills format and skill-creator guidance | https://github.com/anthropics/skills | The skill's structure |

PLI Labs' own: the campaign method (phases, gates, the amendment form, the pair rule, the lessons), the scripts in
`skills/pli-volta-builder/scripts/`, and the builds listed in the README.
