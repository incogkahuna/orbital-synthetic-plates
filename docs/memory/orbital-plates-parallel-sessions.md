---
name: orbital-plates-parallel-sessions
description: Orbital Plates runs as parallel Claude sessions — integrator owns main + the GPU slot; local git only, no GitHub
metadata:
  type: project
---

ON HOLD since 2026-09-21 (Danny: focus on the foundation pipeline in one session first). Set up 2026-09-21: `C:\Users\danie\Documents\OrbitalPlates` is now a local git repo (branch `main`, no remote, no gh CLI). Rules in `docs/PARALLEL.md`; workers use worktrees `..\OrbitalPlates-<topic>` on `w/<topic>` and hand over via SendMessage using `docs/HANDOVER_TEMPLATE.md`. The integrator merges locally and hands out the single GPU slot (one Comfy/Unreal job at a time).

**Why:** a single 24 GB GPU is the contended resource, and nothing deploys, so PR/deploy machinery doesn't fit.
**How to apply:** find out which role a session is in from its starting prompt; ask the integrator for "GPU: yours" before any heavy job. See [[orbital-plates-desktop-setup]].
