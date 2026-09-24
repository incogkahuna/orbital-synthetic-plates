---
name: orbital-plates-winning-look
description: Comfy settings + geometry path Danny loved for Orbital plates (2026-09-21)
metadata: 
  node_type: memory
  type: project
  originSessionId: 50952775-cf93-4c2b-a6b6-c924cb508250
  modified: 2026-09-22T00:38:54.847Z
---

Danny called the Cesium v1 stills (renders\stills_cesium_v1.png) "incredible". Recipe: Cesium Sunset Blvd depth (another session's work) → Wan 2.2 Fun-VACE 14B fp8 two-stage (high steps 0-10 → low steps 10-20), uni_pc/simple, CFG 3.5, shift 8, **depth strength 0.8, NO reference image**, era + **dusk/magic hour** carried in the prompt, 33 frames, keep the last. Builder: scripts\make_still_graph.py (`--noref --video=depth_C1_cesium.mp4`).

**Why:** a mismatched reference image made the cars mash and pulled the perspective off. Danny's priority is perspective ("perspective is everything" for LED-wall plates). He likes dusk and wants the time of day kept.

**How to apply:** start any new era/still from this recipe. Real period photos go in as a keyframe-first or style-LoRA path, not a raw reference_image (Danny approved that plan and is gathering images). Related: [[orbital-plates-desktop-setup]], [[orbital-plates-working-style]]

Convention: `C:\Users\danie\Documents\OrbitalPlates\current_best_draft\` holds only the current best plates, as copies from deliverables\. When Danny names a new best, replace its contents rather than adding versions. It started with 1955/1980s_C5_cesium_v5_5s.mp4 on 2026-09-21.
