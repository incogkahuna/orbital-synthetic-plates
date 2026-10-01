# Modern Hollywood night test (AJ, week of 2026-10-05)

Front (C1) and rear (C5) plates, Sunset Blvd eastbound from La Brea, present day, **night**. Period work is paused:
`docs/PERIOD_PAUSE.md`, tag `period-pause-2026-09-28`.

## Goal
Look like the real street, not an invented one (Danny, 2026-10-01). Three layers, all approved:
1. **Real geometry: Google Photorealistic 3D Tiles** (studio signed off 2026-10-01). `run_options.json`
   `"google_tiles": true` (`overnight_batch.ps1 -Google`) shows the Google tileset, hides Cesium World Terrain and OSM
   extrusions, samples lane heights from the Google road (cache `Saved/cesium_route_raw_google.json`), and skips the
   invented storefronts/sidewalk props. Only overhead wires are added. Traffic is still Unreal (both kerbs parked, oncoming streams).
2. **Landmark-aware prompts.** `refs/route_landmarks_osm.json` (OSM: named places and cross streets, with distance along
   the route). `scripts/landmark_prompts.py C1|C5 <secs> <segments> <base.txt> <out.json>` names what each camera
   actually sees in each time segment (left and right flipped for the rear). `ltx_3dreal.py --segments out.json` feeds
   one prompt per segment; LTXVContextWindows (`split_conds_to_windows`) gives each window the prompt for its centre.
   In 60 s the front camera passes In-N-Out and IHOP (0–6 s), the motel strip and Raising Cane's (14–20 s), Highland and
   Chick-fil-A (22 s), Catalina Jazz Club, the Hollywood Reporter Building and the LA Recording School (31–39 s), and Blessed Sacrament (47 s).
   2 min adds the Cinerama Dome (~95 s), Sunset & Vine (105 s), the Palladium (121 s) and Sunset Gower Studios (~137 s).
3. **Real-photo references** (Wikimedia Commons, freely licensed; shortlist → Danny approves → download). Planned use:
   Magnific image generation with the Unreal frame for structure and a real photo for style, making keyframes that
   LTX animates through (look lock and fewer visible joins).

## Status
- 10 s night test on the v16 (invented-street) geometry: good night look, cars face the right way, lanes correct.
- Cars: Dekogon retro meshes until **City Sample Vehicles** is in Danny's Fab library.
- Length: **60 s first** (Danny, 2026-10-01); 2 min is the ideal and the pipeline has no length limit (about 1.5 h GPU per camera at 2 min).
- Open: billboard text gibberish.
