---
name: orbital-cesium-primary-path
description: Orbital Plates — Cesium real-street geometry is now THE primary path (box street abandoned); how the C1 run works
metadata: 
  node_type: memory
  type: project
  originSessionId: 5601c557-bc52-4c78-866e-63a8beaa551d
  modified: 2026-09-22T00:09:14.006Z
---

2026-09-21: Danny made Cesium geometry the primary path ("initial pass and logic were entirely wrong"). Box placeholder street is retired.

- Route: Sunset Blvd eastbound, La Brea → Gower (2.08 km, straight). Right-hand through lane 6.6 m S of OSM centreline.
- Level /Game/OrbitalPlates/Cesium/PlatesCesium: World Terrain (ion 1) + OSM Buildings (96188); Google 3D (2275207) hidden + suspended, never render (ToS).
- Run: touch Saved/run_cesium_c1.flag, launch editor → Content/Python/cesium_c1_run.py traces terrain heights (async sampler NOT exposed to Python; line-trace fallback, cached in Saved/cesium_route_raw.json), builds rig, renders C1 to Saved/PlateRenders/Cesium, quits.
- Gotchas: after a flag run, CHECK no UnrealEditor/CrashReportClient is left (17:07 run relaunched an editor that sat open during Comfy). tileset load progress = get_editor_property("load_progress"); set_relative_location takes 3 args in Python.
- A peer session ("Orbital Synthetic Plates continuation") owns Comfy/Wan stills; coordinate via SendMessage.

**Why:** real building masses and ground height anchor the perspective, which the box street never did.
**How to apply:** build new routes/eras on this level, not PlatesMain. Related: [[orbital-plates-working-style]], [[orbital-plates-parallel-sessions]]
