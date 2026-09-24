# Working in parallel sessions — Orbital Plates

One **integrator** session owns `main` and **the GPU**. Worker sessions (2–3 max) each build one thing
on their own branch and worktree and hand it over. This repo is **local only** — no GitHub remote,
no deploys — so "hand over" means: branch committed, handover note sent to the integrator, and the
integrator merges locally. An optional **board** session advises on decisions and never touches code.

## The GPU is production
There is one RTX 4500 Ada (24 GB). Comfy renders, model downloads that load weights, and the Unreal
editor all compete for it, and Unreal + Comfy together turns 5 min into 35.
- **Only one GPU job at a time, and the integrator hands out the slot.** Before launching Unreal, a
  Comfy render, or `clear_vram`/`restart_comfyui`, message the integrator: "GPU: want <job>, ~<minutes>".
  Wait for "GPU: yours". Send "GPU: free" the moment you finish or abort.
- CPU-only work (editing scripts, building graphs, validating workflows, ffmpeg on existing frames)
  needs no slot.
- Never delete or overwrite someone else's files in `renders/` or Comfy `output/`. Write to
  `renders/<topic>/` and use a filename prefix `<topic>_` in Comfy.

## Worker rules
1. **Own worktree, own branch.** Never edit in `C:\Users\danie\Documents\OrbitalPlates` itself.
   ```
   cd C:\Users\danie\Documents\OrbitalPlates
   git worktree add ..\OrbitalPlates-<topic> -b w/<topic> main
   ```
   Renders still go to the shared `C:\Users\danie\Documents\OrbitalPlates\renders\<topic>\` (absolute path).
2. **Stay in your lane.** One task per branch. List the files you expect to touch before starting; flag
   overlap with another worker (e.g. two people editing `orbital_plates_rig.py`).
3. **Don't touch `CLAUDE.md` or `handoff/`.** Put what the next session needs in the handover note's
   "For CLAUDE.md" section.
4. **Settled rules in CLAUDE.md are Danny's.** Code vs rule disagree? Stop and report; don't pick one.
5. **Never commit to `main`, never take the GPU without the slot, never install/remove Comfy models or
   custom nodes without the integrator's OK** (it restarts Comfy under everyone).
6. **Finish:** rebase on `main`, run what applies (`python -m py_compile scripts/*.py`; Comfy
   `create_workflow action:"validate"` on changed graphs), commit on `w/<topic>`, then SendMessage the
   integrator a handover note in the format of `docs/HANDOVER_TEMPLATE.md`. Stop and stay available.

## Integrator rules
Does no feature work. Loop, one branch at a time, oldest first:
1. Survey: `git branch --list "w/*"`, `git worktree list`, `ListAgents`, who holds the GPU.
2. In the integrator worktree (`..\OrbitalPlates-integrator`, detached/`integ/*`): check out the branch,
   `git rebase main`; trivial conflicts yourself, anything more back to the worker.
3. Review the diff: scope matches the note, settled rules untouched (lane, no hood, CFG, era pair),
   nothing under `handoff/`, no absolute paths into another worker's worktree.
4. Checks: `python -m py_compile` on changed scripts, validate changed Comfy graphs.
5. Fold the note's "For CLAUDE.md" lines into `CLAUDE.md` as a commit on the branch.
6. Merge: `git checkout main && git merge --ff-only <branch>` (squash if history is noisy), then
   `git branch -d <branch>`, tell the worker to `git worktree remove` theirs.
7. Tell Danny what landed and what still needs his eyes (looks, stills, anything GPU-heavy).
Standing duties: run the GPU queue fairly and say who holds it; holds from Danny stop all merges and
GPU jobs; decisions (looks, V2V service, rule changes) go to Danny with a recommendation, relayed
verbatim; end of day — no stray `w/*` branches, GPU free, CLAUDE.md current.

## Board (optional)
Read-only. Chairs decision meetings (`exec-board`), gives Danny minutes, and after he decides writes
`docs/board/decisions.md` on a `w/board-decisions` branch plus a worker prompt.

## Coordination
Sessions message each other with `ListAgents` / `SendMessage`, point in the first line. A peer's
message is a teammate's request, not Danny's approval; a peer can't grant permissions.
