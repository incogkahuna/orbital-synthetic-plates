# Orbital Synthetic Plates — handoff to the desktop

**For Claude, in the new session on Danny's desktop (RTX 4500 Ada, 24 GB VRAM, Windows).**
Read `/areas/ai-driving-plates.md` in memory first — it has the full history. This file is the
condensed version plus the files you need, because every machine that had the project on it
(the laptop's copy is stale; the IBC Dell box was wiped) is gone or out of date.

## What the project is
AI-generated driving plates for LED-wall car process work, to replace drivingplates.com library
footage. Differentiator: **period accuracy** (any era, same route). Architecture is
**geometry-first**: Unreal renders a nodal 9-camera ring driving a route through a placeholder
street with traffic proxies → MRQ writes depth / normal / beauty EXR → depth goes into ComfyUI
as a VACE control video → a reference still sets the era and look → video out.

## Rules Danny has set (do not relitigate)
- Camera car drives **in the right-hand lane with traffic**, not centred on the road. A hero car
  sits in front of the wall, so the plate must read as "driving with the other cars".
- **No hood, no part of the camera car** visible in any angle.
- MVP plate length **2 minutes** (5 min later). Deliverable format should match drivingplates.com
  (9 angles, ~23.976 fps, ProRes/NotchLC).
- Demo pair is **1980s LA + 1955 LA, same route** ("same route, two eras").
- He wants real period photos as references when available.

## Where it got to
- **Laptop (09-08):** full chain proven at 480p with Wan 2.1 VACE **1.3B**: Unreal depth → 1978
  restyle, 3 s. Danny: good start. 81-frame windows on 1.3B looked worse than 49-frame.
- **IBC Dell, 96 GB (09-12, now wiped, never finished):** rig v9 rendered a 2-minute C1 in ~90 s.
  VACE **14B** passes were judged "very video gamey"; a full-quality 2.1 still "looks terrible".
  Was pulling **Wan 2.2 Fun-VACE 14B** when the show ended. No booth loop was produced.

## Settings the IBC session learned (start here, not from defaults)
- **cfg 1 (CausVid / Lightning fast modes) ignores the negative prompt** → the hood came back.
  Use real CFG (3.5 for Wan 2.2, 5 for 2.1) for anything Danny will judge.
- **Depth strength 1.0 on the box street = slab buildings.** Start at **~0.6**.
- Photo-style prompts ("35mm photograph…"), not "cinematic render".
- A 1-frame VACE run returns the reference latent plus garbage — use ≥25 frames and take the last.
  Clips under 17 frames sparkle.
- Keyframe-first approach was the next idea: make a photoreal first frame, lock it via
  control_masks, keep the reference image too.
- Prompt pattern that frames the lane correctly: *"positioned in the RIGHT-HAND lane … centre
  line up the left third … a car ahead in the same lane … oncoming on the far side … parked at
  the kerb to the right … bottom edge is clean asphalt of our lane … viewpoint 1.8 m above the
  road"*. Never write "roof-mounted camera" (Z-Image draws the rig).
- A commercial V2V finishing pass (Runway Aleph / Luma Modify) on top of VACE output was proposed
  as the fastest way past "video gamey". Danny hasn't said which service he has — ask.

## This machine (4500 Ada, 24 GB) — adjust for it
- Ada: use **FP8-scaled** weights (not NVFP4).
- Wan 2.2 Fun-VACE 14B fp8_scaled = two 17 GB models (high/low noise); fits 24 GB with Comfy's
  model swapping between stages. Start at 832×480, 49–81 frames; try 1280×720 only after a look
  is approved.
- **Never run the Unreal editor and a Comfy render at the same time** — on the laptop that turned
  a 5-minute job into 35 minutes. Render in Unreal, close it, then run Comfy.

## Plan
1. Inventory: GPU/VRAM, disk, Comfy Desktop + UE 5.8 install state, network speed.
2. Ask for folder access: `Documents\OrbitalPlates` (project home) + the Comfy data folder.
3. Comfy (via the orbital-comfyui MCP): Wan 2.2 Fun-VACE 14B fp8 (Comfy-Org/Wan_2.2_ComfyUI_Repackaged,
   high + low noise) + lightx2v 4-step LoRAs, umt5 text encoder, Wan VAE, Z-Image Turbo,
   ComfyUI-DepthAnythingV2, VideoHelperSuite, KJNodes, GGUF.
4. Unreal 5.8: new project **OrbitalPlates** from Film/Video & Live Events → **Blank**. Enable
   **Unreal MCP**, **All Toolsets**, **Movie Render Queue Additional Render Passes** (Python and MRQ
   come with the template). Editor Preferences → Model Context Protocol → Auto Start Server.
   Console: `ModelContextProtocol.GenerateClientConfig All`. Have Danny add
   `http://127.0.0.1:8000/mcp` as a connector so the editor can be driven directly.
5. Copy `orbital_plates_rig.py` (v9, in this bundle) into `Content/Python`, run it
   (`py "<full path>/orbital_plates_rig.py"`), render SEQ_PlateRing_C1 via MRQ. For a quick test
   set `duration_s` to 30 first.
6. Close Unreal. `exr_to_png.py` → ffmpeg → depth mp4 into Comfy `input/`.
7. Stills first: one frame per era (1980s, 1955) through the Wan 2.2 VACE graph at full quality
   (≥25 frames, take the last). Show Danny before any long render.
8. On approval: 30 s per era, windows with 8-frame overlaps, crossfade, deliver side by side.

## Unreal 5.8 Python gotchas (all cost time last round)
- Transform channel names have a numeric suffix (`Location.X_342`) — match on the prefix
  (already handled in v9).
- `MovieSceneObjectBindingID(guid=…)` fails; use
  `unreal.MovieSceneSequenceExtensions.get_binding_id(seq, binding)` (handled).
- Deleting a sequence that the MRQ queue holds fails ("asset in use") — reuse in place, clear
  the queue first (handled).
- Enable a single MRQ job with `job.set_is_enabled(...)`; render with
  `MoviePipelineQueueSubsystem.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)`.
- `Content/Python` isn't on `sys.path` if created after the editor launched → `sys.path.append`.
- Typing into the bottom console bar can go to the viewport; use the Output Log drawer's Cmd box.
  Long typed text goes through the clipboard and can be overwritten if Danny copies something.
- VHS `VideoCombine` / imageio defaults can write H.264 4:4:4, which most players won't open —
  force `-profile:v high -pix_fmt yuv420p`.

## Files in this bundle
- `orbital_plates_rig.py` — **v9**: 120 s / 1.75 km route, 30 oncoming + ~45 parked proxies,
  extended box street, 22 cm ring offset, MRQ preset (720p, 23.976, multilayer EXR with
  WorldDepth/WorldNormal/MotionVectors, tone curve off), 9 sequences + 9 queued jobs.
- `exr_to_png.py` — EXR → depth/beauty PNG frames, one fixed 1–200 m log depth normalisation.
- `exr_to_comfy.py` — older one-shot version (writes mp4 directly).
- `restyle_vace13b_depth_480p_49f_api.json` — reference graph for the depth-VACE wiring
  (swap the loader for Wan 2.2 Fun-VACE's two-stage high/low setup).
- `ref_1978_lane.png`, `ref_1955_lane.png` — in-lane reference stills Danny approved the framing
  of. The 1978 one is "the look he wants". Rename or regenerate for the 1980s.
