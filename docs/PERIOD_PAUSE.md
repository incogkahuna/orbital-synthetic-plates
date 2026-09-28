# Period work: paused 2026-09-28 (resume here)

Paused so we can focus on AJ's modern-day Hollywood night test (front and rear cameras). Everything needed to pick
the 1980s dusk set back up is below. Git tag: `period-pause-2026-09-28`.

## Where it stood
- Pipeline: Unreal depth → `scripts/lane_lines.py` (lane markings, optional car-edge direction cue) →
  `scripts/ltx_3dreal.py --lora union` (LTX-2.3 + Union-Control, 361/168 context windows, guide 0.55) → Magnific Topaz 2K.
  Full write-up: `docs/STATUS_2026-09-26.md` and the "Sunset Plates Process" artifact.
- Best plates so far (v3, v15 world): `deliverables/ltx3dreal/lanes_C{5,1,7}_v15_depthlines_union_60s_v3_00001.mp4`;
  C5 at 2K: `deliverables/magnific/2026-09-27_v3/`. Danny: "insanely good".
- Open issue being fixed when paused: **cars facing the wrong way.** Unreal had almost no cars on the far (north) side
  and sparse kerb parking, so the AI invented cars in random directions; and depth can't show front vs back.
  - Done: `orbital_plates_rig.py` now parks both kerbs densely (5.6–9 m spacing, 15% gaps, only along the camera path);
    far-kerb cars (`Traffic_ParkedFar*`, offset −16.3 m) face west with that side's traffic; each oncoming lane gets its
    own stream 25–70 m apart. `cesium_c1_run.py` re-plans `Traffic_Oncoming*` each run.
  - Done: Unreal render **v16** (276 cars) for C5/C1/C7: `renders/Cesium_C*_v16_png`, beauty `renders/Beauty_C*_v16_png`,
    car-free depth `renders/Cesium_C*_v16nc_png` (check it exists; the nc run follows the v16 run).
  - Next: `lane_lines.py C5 v16 v16nc renders/lanes_C5_v16 --frames 1441 [--car_edges 0.5]`, a 10 s LTX test with
    and without `--car_edges`, **stills to Danny**, then 60 s for C5/C1/C7 with `prompts/ltx_union_1980s_C*_v3.txt`.
- Other open items: sign text gibberish; C7 cars read newer (note: the LTX distilled model runs at cfg 1, where the
  negative prompt is ignored, so only positive wording works); Day-to-Night IC-LoRA needs `hf auth login` on AMD5;
  1955 needs a 1950s car pack; joins remain (~7/min), and a bigger GPU would allow one window per minute.
