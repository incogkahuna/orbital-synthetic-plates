# Plate issues — tracked across versions

Danny's review notes, turned into issues. Status: **open** → **fix in test** → **verified vN** (checked at the same
timestamps in a new render). Every version gets a report card against this list.

## Standing rules from Danny (not bugs — constraints every version must meet)
- **R1 No camera shake, ever.** The plate replaces the real world seen from a moving car: the car moves, the world
  does not jitter. Real-world physics only. (2026-09-24)
- **R2 Neutral real-life look.** No film stock, grain, grade, vignette; grading happens through the lens on set.
- **R3 Overhead wires only occasionally** — don't go crazy. (2026-09-24)
- **R4 Traffic should vary and behave naturally.** Cars in the next lane over occasionally pass the camera car;
  no car hovering or rocking forward and back. (2026-09-24)

## v1 review (Danny, 2026-09-24) — plates in deliverables/v1/

| ID | Plate | When | Issue | Likely cause | Planned fix | Status |
|---|---|---|---|---|---|---|
| P1 | 1980s C5 | from ~10 s | Headlight reflections on the road become very saturated and colourful | Drift: each window seeds the next with generated frames, colour compounds | Re-anchor windows / colour-match to window 0; negative "oversaturated, neon reflections" | **improved** (v11 A/B: colour lock holds the dusk palette to 19 s; road glare still bright) |
| P2 | 1980s C5 | every stitch | Big dark square in the sky, flickers at each temporal stitch | Sky has no depth (black) so each window reinvents it; stitch seam | Stable sky layer (generate once, hold); stitch review | **improved, new artifact** (v11 A/B: sky lock v1 kills the flicker and blotches but freezes whatever Wan painted into depth-sky on first sight → ghost smears of rooftops/palms. Sky lock v2 = lock low frequencies only, offline test promising; needs an in-loop run) |
| P3 | 1980s C5, 1955 C7 | ~10 s+, ~15 s | Road light reflections flash bright colours like police lights | Same as P1, plus "neon/headlights" in the prompt | P1 fix + negative "police lights, flashing, strobing lights" | **improved** (no cop-light flashing in either v11 run with the new negatives; B calmer) |
| P4 | all | throughout | Street lamps cast no light on the road | Depth has no lighting; prompt never asks for lamp pools | Prompt: lamps on, pools of light on the road; later a lighting cue from Unreal's lit pass | open |
| P5 | 1955 C3 | ~8 s (few frames), ~15–18 s | Plate stops moving (freeze) | **Confirmed:** C3 faces flat featureless walls, depth barely changes (15 s: depth motion 0.93 vs ~2.5–7 normal), Wan gets no motion cue | Street dressing (pilasters, awnings, signs, palms) gives moving detail — built in v9f | fix in test |
| P6 | all | throughout | Camera shake (violates R1) | **Confirmed Wan-side:** the depth skyline moves 0 px frame-to-frame (median; C5 and C3 v8), so the Unreal camera is steady — Wan invents the shake | Negative "camera shake, handheld, wobble"; window anchoring (P1); stabilise-in-post only as last resort | open |
| P7 | 1955 C7 | throughout | Blue car on the left keeps moving forward and back | Car nearly matching our speed and/or Wan re-placing it per window | Traffic model with real relative speeds and smooth passing (R4) | open |
| P8 | 1980s C7 | throughout | Sky: blurry sections, flickering dark streaks | Same as P2 | Stable sky layer | open |
| P9 | 1980s C7 | ~18 s | Smears on frame left, like water on a lens | Late-window degradation (drift) | P1 re-anchoring | open |
| P10 | 1980s C5 v11 A | 2–6 s | The first car passing us looks terrible: smeared, box-like, changes shape as it goes by (Danny, 2026-09-24: "ok" otherwise) | The closest car is a plain box proxy filling a third of the frame at 832×480; Wan re-invents its detail every frame | Next phase: real Fab car meshes, then a fidelity pass (SeedVR2 / higher-res) | next phase |

## Found by Claude
| ID | Plate | When | Issue | Likely cause | Planned fix | Status |
|---|---|---|---|---|---|---|
| C1 | all | throughout | Every parked car has its lights on | Prompt says headlights on for the whole scene | Prompt: only moving traffic lit, parked cars dark | open |
| C2 | C5 | first ~1 s | Parked car at left drawn backward (tail lights) | Box proxies don't show facing; varies by seed | Real period car meshes (Fab) | open |
| C3 | all | late (15 s+) | Quality drifts: colour/contrast climb, smears build | Window chaining compounds errors | = P1 | open |
| C4 | 1955 C5 | all | Film-stock look | Rendered before the neutral prompt (v1 is mixed) | Neutral prompt — verified in stills 2026-09-24 | fix in test |
| C5 | C5 near field | — | Round shapes on poles become neon signs | Wan reads silhouettes | Palm-led planting, frond crowns (v9f); no spheres anywhere (v12, Danny) | **verified v12** |
| C6 | 1980s C5 v14 60 s | 15 s → 30 s+ | **Long-run collapse.** Clean and the best look yet at 5 s (real Dekogon cars); translucent buildings in the sky by 15 s; abstract colour-block breakdown by 30 s, unusable to 60 s | Window chaining compounds errors: each of 35 windows is seeded by the last one's output. Sky/colour locks may feed their own artifacts back in | Anchor every window to a clean window-0 frame (VACE reference, `PLATES_ANCHOR=1`). **Diagnostics 09-25 (30 s, sheet renders/drift_fix_plate1_D1_D2_5s_15s_29s.png):** anchor stops the structural collapse. D1 anchor + masked colour/sky locks: stable colour but see-through rectangles where Wan paints sky over Cesium buildings. D2 anchor only: best look to ~20 s, colour drift returns by 29 s. Next: D3 = anchor + global, partial, time-smoothed colour match (no masks), 60 s. Longer term see RESEARCH_PHOTOREAL.md | **improved**, D3 running |
