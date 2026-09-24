# Orbital Synthetic Plates

AI-generated, period-accurate driving plates for LED-wall car process work. Geometry-first:
Unreal renders a nodal 9-camera ring driving a route → MRQ writes depth/normal/beauty EXR →
depth feeds ComfyUI (Wan 2.2 Fun-VACE 14B) as a control video → a reference still sets the era.
Full background: `handoff/HANDOFF.md`.

**Parallel sessions: read `docs/PARALLEL.md`. One integrator owns `main` and the GPU.**

## Layout
- `scripts/` — `orbital_plates_rig.py` (Unreal rig, v9), `exr_to_png.py`, `exr_to_comfy.py`
- `comfy_workflows/` — API-format Comfy graphs
- `refs/` — approved reference stills (`ref_1978_lane.png` is "the look")
- `handoff/` — original handoff bundle, read-only archive
- `renders/`, `deliverables/` — outputs, git-ignored, shared by all sessions
- Comfy: `C:\Users\danie\AppData\Local\Comfy-Desktop\ComfyUI-Installs\OrbitalPlates`
  (models/input/output under `...\Comfy-Desktop\ComfyUI-Shared\`). Unreal 5.8.2.

## Settled rules (Danny's — do not change without him)
- Camera car in the **right-hand lane with traffic**, not centred.
- **No hood / no part of the camera car** in any angle.
- MVP plate **2 minutes**; deliverable matches drivingplates.com (9 angles, 23.976 fps, ProRes/NotchLC).
- Demo pair: **1980s LA + 1955 LA, same route**. Real period photos as refs when available.
- Real CFG for anything Danny judges (3.5 Wan 2.2 / 5 Wan 2.1) — cfg 1 ignores the negative prompt.
- Depth strength ~0.6 to start; photo-style prompts; ≥25 frames per VACE run.
- **Plates look like life, not like film.** No film stock, grain, faded/warm grade, vignette or retro filter —
  the era comes only from content (cars, signs, clothes, street furniture). Grading and filtering happen on set,
  through the lens. Time of day (dusk) is lighting, not a grade, and stays.
- **Camera at driver eye level: 1.5 m** (`camera_height_cm` 150), not roof height.
- **Never run Unreal and a Comfy render at the same time.**
- Show Danny stills before any long render.

## Open decisions (Danny's)
- Which commercial V2V finishing service, if any (Runway Aleph / Luma Modify).
