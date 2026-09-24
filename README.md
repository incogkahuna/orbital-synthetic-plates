# Orbital Synthetic Plates

AI-generated driving plates for LED-wall car process work, with period accuracy: the same real
route in any era. Geometry first — Unreal (Cesium real-world tiles) renders a nodal 9-camera ring
driving Sunset Blvd; MRQ writes depth EXRs; ComfyUI (Wan 2.2 Fun-VACE 14B) restyles the depth into
a period plate.

## Start here
| Read | For |
|---|---|
| [docs/HANDOFF_01_original_brief.md](docs/HANDOFF_01_original_brief.md) | The project, the rules, settings learned the hard way |
| [docs/HANDOFF_02_setup_done.md](docs/HANDOFF_02_setup_done.md) | The desktop machine: paths, installs, models |
| [docs/HANDOFF_03_cesium_and_first_plates.md](docs/HANDOFF_03_cesium_and_first_plates.md) | Latest: Cesium geometry, the working recipe, open items |
| [docs/memory/](docs/memory/) | Standing notes carried between sessions |

## What is in here
- `scripts/` — the pipeline. `orbital_plates_rig.py` (Unreal rig, sequences, MRQ), `cesium_c1_run.py`
  (headless render), `exr_to_png.py` (depth EXR → PNG), `make_still_graph.py` (builds and submits the
  Comfy graph), `run_era.py` (windowed long runs), `overlay.py` (depth edges over a still, for
  checking perspective).
- `unreal/` — the Unreal project's own source: `Content/Python`, `Config`, `.uproject`. Not the
  11 GB project folder.
- `comfy_workflows/` — API-format graphs.
- `refs/` — framing references and the period-photo candidate list (with rights notes; no photos
  downloaded).
- `plates/` — the current best plates plus the comparison sheets.

## The recipe that works
Cesium depth video → Wan 2.2 Fun-VACE 14B fp8, two-stage high-noise → low-noise, uni_pc/simple,
**CFG 3.5**, shift 8, **depth strength 0.8, no reference image**, era and dusk in the prompt,
832×480. Long runs use 49-frame windows with 8-frame overlaps fed back as kept control frames.

## Not in here
The Unreal project binaries and cache, model weights, EXR renders and intermediate frames. Those
live on the desktop under `C:\Users\danie\Documents\OrbitalPlates`.
