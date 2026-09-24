# v1 plate kickout (2026-09-23/24, AMD5)

Danny named this batch **v1**. Six 20 s plates, 481 frames each at 23.976 fps, 832×480.
Files (not in git, too big): `deliverables\v1\<era>_<cam>_cesium_v8_20s.mp4` + `v1_review_grid_6up.mp4`.

## Settings
- Geometry: Cesium Sunset Blvd eastbound (La Brea → Gower), depth **v8** = directional car proxies
  (long hood / short trunk / windshield step) + camera at **1.5 m** driver eye level. Depth renders are 120 s.
- Model: Wan 2.2 Fun-VACE 14B **bf16** (faster than fp8 on the A6000: 281 s vs 293 s per 33-frame still),
  two-stage high→low noise 0-10/10-20, uni_pc/simple, CFG 3.5, shift 8, depth strength 0.8, no reference image.
- Windows: 49 frames, 8-frame overlap fed back as kept control frames, crossfaded. 12 windows per plate,
  ~436-466 s per window, **91-95 min per 20 s plate**. Queue ran 22:08 → 07:18 with no failures.
- Prompt: 1955 C5 used the old film-stock prompt (Kodachrome, grain). **The other five used the neutral
  "real-life capture" prompt**, which went in while the queue ran. v1 is therefore mixed.

## What Danny saw (1955 C5)
- Every parked car has its lights on — the era prompt says headlights are on for the whole scene.
- Cars on the right turn to mush in the final frames.
- Severe flicker, mostly in the sky.

## What the QA frames show (2 s / 10 s / 19 s)
- **Drift over the plate.** At 10 s most angles hold up (1980s C7 and 1955 C5 best). By 19 s saturation and
  contrast climb and smears build at the bottom of frame (1955 C5 sky swirls, 1980s C5 road smear, 1955 C7
  foreground). Cause: each window is seeded with the previous window's last 8 *generated* frames, so errors
  compound window after window.
- **Sky flicker.** The depth pass has no sky (black = infinitely far), so every window reinvents it.
- 1955 C3 briefly reads a gap between buildings as an alley; side views change most per frame.

## v2 list
1. **Look:** neutral real-life capture only (rule in CLAUDE.md); parked cars unlit, only moving traffic lit.
2. **Stop the drift:** re-anchor windows instead of chaining generated frames forever — e.g. colour-match each
   window to window 0, keep fewer carried frames, or re-seed from a fixed keyframe every N windows.
3. **Stable sky:** generate the sky once and hold it (mask by depth = far), so windows can't change it.
4. **Detailed world in Unreal:** period car models per era (fronts, lights), storefront depth (awnings,
   canopies, recessed entries), sidewalk clutter via PCG, sign shapes. Timeless or per-era shapes only.
5. **Higher-grade passes:** SeedVR2 7B restore/upscale (downloaded, `scripts\upscale_plate.py`), LTX-2.5 with
   depth/edge control (needs Danny's HF licence acceptance), Qwen 2.1 hero keyframes (research licence — test only).
6. **Nebula fleet:** 4 idle GPUs overnight (t2w 96 GB, nev/amd2/amd3 48 GB). Needs Wilder: a plates lane or
   GPU leases + Wan models on workers. Agent API needs a `NEBULA_AGENT_TOKEN`.
