# Orbital Synthetic Plates — handoff 03 (Cesium geometry + first plates, 2026-09-21/22)

Read `HANDOFF_01_original_brief.md` (project, rules, learned settings) and
`HANDOFF_02_setup_done.md` (machine, paths, install state) first. This file covers the
desktop session that produced the first plates Danny approved.

## What got built

**Geometry (a second Claude session did this, see `docs/memory/orbital-cesium-primary-path.md`)**
- Cesium for Unreal on real Sunset Blvd, eastbound from La Brea. Cesium is now the primary path;
  the box-street placeholder is retired.
- Geometry versions: v1 flat ground → v2 kerbs + sidewalks → v3 real-size car proxies (the
  fix that mattered) → v4 streetlights, signal masts, kerb gaps at cross streets →
  v5 rear + side cameras with following traffic.
- **The bug worth remembering:** the sequence keyed only location and rotation, so unkeyed Scale
  rendered every traffic proxy as a 1 m cube with a cabin on top. Wan read those as kiosks and
  sign boards, and drew the kerb around them. Keying scale fixed it.

**Restyle (this session)**
- Wan 2.2 Fun-VACE 14B fp8, two-stage: high-noise KSamplerAdvanced steps 0-10 →
  low-noise steps 10-20, uni_pc / simple, **CFG 3.5**, shift 8, 832x480.
- **Depth strength 0.8, NO reference image.** A mismatched reference still (a different street)
  made the cars mash and pulled the perspective off. Era and dusk go in the prompt instead.
- Per-camera prompt text (forward / rear / left / right) in `scripts/make_still_graph.py`.
- Windowed long runs: `scripts/run_era.py`. 49-frame windows, 8-frame overlap; the overlap frames
  are fed back as VACE control frames with `control_masks` 0 (keep), so windows continue instead
  of restarting, then crossfaded. ~6.4 min per window on a 4500 Ada (~2 h per 30 s per camera).

## Where it got to
- Stills approved on the Cesium street for 1955 and 1980s, forward + rear + both profiles.
- 5 s motion tests: forward (v4) and rear (v5) for both eras. Window joins hold; Danny's verdict
  was "impressed but not production quality": some flicker and small frame jumps, which he expects
  a stronger finishing model to clean up.
- Current best plates live in `plates/` here and in `OrbitalPlates\current_best_draft\` on the
  desktop (rear camera, 5 s, both eras). That folder always holds the current best — replace, don't
  version.

## Camera priority (Danny corrected this, it matters)
In process work the camera faces the actors, so the wall shows what is BEHIND and BESIDE the car:
**C5 rear > C3 / C7 side profiles > C4 / C6 rear three-quarters > C1 forward (least used).**
Rear plates need following traffic; side views have the fastest parallax and the worst flicker.

## Open items
1. **Flicker / temporal polish.** Options, cheapest first: 16-frame overlaps; a second low-strength
   pass over a finished clip; a temporally consistent upscaler; a commercial V2V finishing pass
   (Runway Aleph / Luma Modify — Danny has not said which he has).
2. **Ring consistency.** Every camera is generated independently, so the overlaps between the 9
   angles will not match. Untested. Options: one wide panoramic plate cut into 9, or condition each
   camera on its neighbour's shared edge.
3. **Throughput.** ~2 h per 30 s per camera at 480p on one 4500 Ada. A 2-minute 9-camera plate is
   ~72 h. Needs cloud GPUs and/or the 4-step Lightning LoRA (which ignores the negative prompt —
   the hood came back last time it was used).
4. **Period photo references.** Candidate list with rights notes in `refs/period/CANDIDATES.md`;
   nothing downloaded yet. Plan: keyframe-first or a style LoRA, never a raw `reference_image`.
5. **Side-view misread:** in 1955 the passing car on C7 faces three-quarters toward camera instead
   of side-on. Minor.
6. A stray floating box near La Brea shows in C5 for the first ~10 s of the v5 render.

## Rules that have not changed
Right-hand lane with traffic, no hood or any part of the camera car, 9 angles at 23.976 fps,
2-minute MVP plate, demo pair 1955 + 1980s LA on the same route.
Never run the Unreal editor and a Comfy render at the same time.
