# Plan: a detailed Unreal world for the plates (v2+)

**Why.** Wan paints what the depth pass gives it. v1's worst problems — cars drawn backward, invented traffic,
mush on the right, empty foreground — come from a world of boxes. More real geometry = fewer guesses and more
frame-to-frame stability. Danny, 2026-09-24: "build a scene so there is a lot more information for the depth
map to paint on."

## Principles
1. **Shape, not surface.** The depth pass sees geometry only — no materials, textures or text. Simple geometry in
   the right place carries most of the value; only cars need real models.
2. **Real positions first, rules second.** Place things where OpenStreetMap says they are; fill the rest with
   rules based on how LA streets are actually built (spacing, kerb offsets), never uniform random scatter.
3. **Timeless or per-era.** Depth at strength 0.8 is followed closely, so a modern silhouette reads as modern
   even in 1955. Every prop is either timeless (poles, hydrants, benches, palms) or swapped per era.
4. **Near field wins.** Depth spreads 1–200 m across one greyscale ramp; detail within ~30 m of the camera is what
   survives. Spend effort on the kerb, sidewalk and ground-floor facades.
5. **Reproducible.** Everything comes from a script, a data file and a seed. Same inputs, same world.

## Data (in the repo)
- `refs/osm_sunset_labrea_gower.json`: OSM buildings, roads, footways, crossings, signals, bus stops (ODbL — credit OpenStreetMap).
- `refs/osm_sunset_pois.json`: 110 businesses/amenities around the route.
- `refs/route_frontage.json` (from `scripts/osm_frontage.py`): everything in the route's own frame
  (x = m east along our lane from La Brea, y = m south of the lane).
  - 112 frontage buildings (53 N / 59 S), ~1.6 km of frontage per side, heights for 100, median setback ~16 m
    from the centreline (≈ 5 m sidewalk)
  - 23 bus stops, 16 signals, 7 stops, 3 hydrants, 3 bins, 2 billboards within 40 m
  - 51 businesses within 45 m (restaurants, cafes, banks, …) → where signs and entrances go
  - 275 service roads → driveway gaps in kerb parking

## Layers, in build order
| # | Layer | What | Source | Depth value |
|---|---|---|---|---|
| 1 | **Cars** | Real period car meshes, one kit per era (1950s: rounded fenders, fins; 1980s: boxy sedans, wagons, pickups). Parked cars follow real parking (gaps at driveways, bus stops, hydrants). | **Fab (Danny's account)**; interim: better procedural proxies with hood/cabin/trunk/wheel gaps | Highest — fixes backward cars, "mush", era read |
| 2 | **Storefront band** | Along each frontage building's street face: awnings and canopies, recessed entries (at OSM business positions), window insets with pilasters/mullions, sign boards over entries, blade signs, parapets; rooftop signs on some | Scripted boxes from `route_frontage.json` | High — the side cameras stare at this all plate |
| 3 | **Kerb & sidewalk furniture** | Real: bus stops (bench + sign pole + shelter per era), signals, stop signs, hydrants, bins. Rules: street trees/palms every 10–15 m, parking meters every ~6 m at the kerb, utility poles + overhead wires (denser in 1955), newspaper racks/mailboxes near corners | Scripted primitives + real positions | High for C3/C5/C7 near field |
| 4 | **Kerb profile** | Real kerb height (15 cm), driveway aprons at service roads, kerb returns at cross streets | Scripted | Medium — reads as a real edge |
| 5 | **Distance & sky** | OSM massing stays; add a sky mask (far = sky) so the sky can be generated once and held | Depth threshold | Fixes sky flicker (v2 list #3) |
| 6 | Pedestrians (optional) | Standing/walking silhouettes at bus stops and storefronts | Scripted capsules or Fab | Low–medium; Wan adds people anyway — Danny's call |

**Era switch:** `CONFIG["era"]` in the rig picks the car kit, awning/canopy mix, wire density and bus-stop shelter.

## How it runs
- New `Content/Python/world_dress.py`, flag-run like `cesium_c1_run.py`, reads `refs/route_frontage.json`,
  builds everything under an outliner folder `Dressing/`, instanced meshes where counts are high.
- Test per layer: re-render depth for C5 + C3 (30 s is enough), one Wan still each, side by side with v1 at the
  same frames. Each layer is kept only if it helps.

## What the first dressing tests showed (2026-09-24, 1955, seed 1234, neutral prompt, A/B at 33 frames)
- **Silhouette decides what Wan paints.** Smooth round shapes on poles become **round neon signs**: a sphere
  canopy turned into a giant sign (v9d), a disc palm crown into a sign on a pole, and even clusters of small
  clumps became sign clusters (v9e). **Frond-crown palms read as real palms** (v9e). Leafy trees need real meshes.
- **The prompt has to name what the geometry is.** Adding "leafy street trees and palm trees along the sidewalks"
  turned some blobs into trees and gave C3 a real tree-lined street; it could not rescue near-camera clumps.
- **Storefront band works on the side views** (C3): awnings, pilasters and sign boards become shopfronts.
- **Parked-car facing still flips between seeds** with box proxies: real car meshes are the fix, not prompts.
- Neutral prompt confirmed: clean true-to-life dusk colour, no grain.
- **v9f (palms 85–90%, leafy trees rare) is the keeper**: C5 reads as a palm-lined Sunset Blvd with no phantom
  signs; C3 gets a tree-lined street. Sheets: `plates/dress_ab_1955*.png`.

## Car models: what to pick on Fab (Danny's account)
Only the **shape** matters (depth pass), so cheap low/mid-poly models are fine; textures and interiors are wasted.
- **Needed per era, 5–8 body types:**
  - 1955: 4-door sedans (Chevy Bel Air / Ford Fairlane class), a 2-door hardtop, a station wagon, a pickup
    (Ford F-100 class), a delivery van/panel truck, a city bus (GM "old look").
  - 1980s: boxy sedans (Chevy Caprice / Ford LTD / Crown Vic class), a compact (Honda Accord / Toyota Corolla
    class), a station wagon with wood panel, a pickup, a van (Ford Econoline class), an RTD bus (GMC RTS).
- **Must-haves:** real-world scale (or easy to scale), single static mesh or a few parts, clear front vs back,
  UE-ready FBX/uasset, Fab **Standard** licence (covers rendered output). Wheels as part of the mesh is fine.
- **Avoid:** branded logos (not needed and a clearance risk), modern cars (read as modern at depth strength 0.8).
- **Search terms:** "1950s car pack low poly", "vintage american car", "classic sedan 1955", "retro pickup truck",
  "1980s car pack", "80s sedan", "boxy station wagon", "vintage bus", "old city bus".
- Once imported under `/Game/Vehicles/<era>/`, the rig swaps proxies for them by `CONFIG["era"]` (built
  2026-09-24: `car_library()` / `dress_car()` in `orbital_plates_rig.py`; optional `manifest.json` per era folder
  for yaw / length / moving-vs-parked).

### AI-use flag (checked 2026-09-24): most period cars on Fab are off-limits
Every Fab listing carries a seller flag, **"Allows usage with AI"** (`isAiForbidden` in Fab's listing data).
NoAI assets may not be used as input to generative AI, and our pipeline renders the car and feeds the depth to Wan,
so **only AI-allowed listings qualify**. Of 272 car/bus/truck listings scanned, 79 allow AI. Almost every good period pack is
NoAI: Dekogon Retro Cars VOL.2 and VOL.3, lyoshko 1980s Cars Pack, the Leartes 1950s NYC megapack, FinalFormStudio
Classic Cars, ROH3D 1970s muscle car, and Leon Media generic classics. Studio licence tier = **Professional** (org over $100k revenue).
Final licence call is Danny's / the studio's.

**Shortlist (AI allowed, unbranded, American shapes):**

| Era | Listing | Seller | Pro price | Format | Fab listing id |
|---|---|---|---|---|---|
| 1955 | Mid-Century Classic Sedan – Generic Vintage Car | ROH3D | $49.99 | OBJ | 1bee1f4f-bd84-46ad-972e-a02e0a11d4a1 |
| 1955 | Mid-Century Classic Family Wagon – Generic | ROH3D | $49.99 | OBJ | 0c5388e0-1206-4e9e-b47e-50050a263d25 |
| 1955 | Vintage American-Style Coupe – Generic (late-50s, fins) | ROH3D | $49.99 | OBJ | c0e1cb7b-4e69-46d0-a007-5a5b9af2907a |
| 1980s | 1980s Classic Pickup Truck "Torvo" | andersonfo | $4.99 | FBX | bd5df33f-8138-4aa8-95ea-9cb1d42319a5 |
| 1980s | Vintage 1970s Classic Sedan (GLB) | CGDeluxe | $9.99 | OBJ/GLB | 2bb097f9-e909-465d-8eba-5c6f792ffc7d |
| 1980s | Van Classic | DmytroZavora | $14.99 | FBX | d83d2f36-aa61-42df-9de1-5bbe164cb524 |
| both | Bus (low poly, "for Unreal") | Pasquill3D | $10.99 | FBX | 846b0dd1-aebd-497e-a940-b236dfaa411b |

Links: `https://www.fab.com/listings/<id>`. 1955 set: about $150. 1980s set: about $40, but thin on the key boxy
full-size sedan (Caprice / LTD class). Gap filler: generate the missing body types as meshes from our own period stills
with an image-to-3D model (TRELLIS is MIT-licensed). Only the silhouette matters for depth.

## Needs from Danny
1. **Car models on Fab** (his Epic account; purchases are his call). Search terms and a shortlist to come.
2. Era rules sign-off (e.g. 1955 overhead wires everywhere, 1980s bus shelters).
3. Pedestrians: yes / no / later.
