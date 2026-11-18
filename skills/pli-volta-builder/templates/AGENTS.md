# AGENTS.md: rules for every agent working on <build name>

Read README.md, docs/ARCHITECTURE.md, documents/plans/PLAN.md (section 9 holds every window's rule, prediction and
result) and docs/measurements.md. Before kernel or speed work also read
documents/plans/KERNEL-AND-OPTIMIZATION-PLAN.md. Every command that starts, stops, moves or installs anything, and who
may run it, is in docs/OPERATIONS.md. The sections "Building kernels", "Upstream sources", "Kernel research records"
and "Lever status" at the end are also in CLAUDE.md with identical text; a test fails if the copies differ.

## 0. Front-line facts (read before any plan or build)

Checked <date> against the primary sources named on each line. Labels: MEASURED, UPSTREAM, PUBLISHED, ESTIMATED,
UNVERIFIED (check before relying on it).

**Rule: upstream-overlap check before any build.** Every plan row, window arm and helper brief lists the rows of this
section it touches and says, for each: adopted, partly, not, or duplicates (naming our patch). If the engine fork or a
kernel repository already built or measured it, start from their code and number. Never answer a capability question
from first principles without reading this section. If a brief is more than a week old, re-list the open pull
requests first.

### 0.1 Lineage and authorship
### 0.2 The model and the standing configuration (with MEASURED figures and their conditions)
### 0.3 Formats and where each runs on this card
### 0.4 The card's roofline (PUBLISHED, UPSTREAM, ESTIMATED)
### 0.5 Kernel repositories (UPSTREAM tables)
### 0.6 Engine pull requests and issues on our path
| # | Status (gh, date) | What it does | Numbers and conditions (UPSTREAM) | Relevance: adopted / partly / not / duplicates |
|---|---|---|---|---|
### 0.7 Known traps
### 0.8 What is open on this build

## 1. The host and this build's place on it
Own tree (never write another build's tree); boards and order; select cards by UUID in private config, never print
one; the crash rule; power and clocks are the owner's.

## 2. Data boundary
Never commit or copy into the repository: weights, wheels, captures, prompts, generated text, user material, logs,
tokens or keys, GPU identifiers, traffic figures other than aggregates. Run the boundary check before every commit
and push.

## 3. Git
Who commits and pushes (the owner), branches for helpers, explicit paths only, no `git add -A`, no stash.

## 4. Checkpoints and reporting
A resumable progress file per helper; reports start with the verdict; every number labelled; `date -u` before any
time.

## 5. Changes to the build
The standing configuration changes only by a PLAN amendment, written before its data, updating README, measurements,
changelog, section 0.2 and the lever table in one commit; the serving record becomes stale. Engine changes only as
kits; every new switch default-off; a kit's CPU test goes through the server's real entry point.

## 6. Operating rules
6.0 What the build is optimized for (the workload's shape, aggregates only, and the owner's words on priorities).
6.1 Rules (one owner; the owner's word for installs; rule before data; patterns meet a real log first; nothing booted
twice; the stop rules; public text only in test prompts; the pair rule; ports; the "never met a server" list; times
from the clock; users' notice; test windows need no permission; crash rule; never edit a running script).

## Building kernels
<copy from the skill's references/kernel-building.md, adapted with this build's figures>

## Upstream sources of our optimizations
<three tables: layout/engine/weights; levers inherited, with their upstream source and our commit; kernel, recipe and
research references; plus the sweep list>

## Kernel research records
<table: record, path, what it holds>

## Lever status on this build
| Lever | Status (adopted / rejected / candidate / closed) | Result (window, date) |
|---|---|---|
