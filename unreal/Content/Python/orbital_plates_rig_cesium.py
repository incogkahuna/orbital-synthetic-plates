"""
orbital_plates_rig_cesium.py (v10)  —  the v9 rig on the REAL route, in /Game/OrbitalPlates/Cesium/PlatesCesium.

Wraps orbital_plates_rig.py (unchanged) and swaps in:
  * the drive spline = our lane on Sunset Blvd EB (La Brea -> Gower), from OpenStreetMap
    (refs/sunset_route_lanes.json), seated on Cesium World Terrain via height sampling;
  * real lane offsets for traffic (adjacent EB lane, two oncoming lanes, kerb parking);
  * no box street (OSM Buildings + terrain are the world);
  * its own content root, so the placeholder level's sequences/MRQ jobs are untouched.

Run from Tools > Execute Python Script with PlatesCesium open. Height sampling is async: the
build finishes a few seconds later — watch the Output Log for "[OrbitalPlates/Cesium] rig done".
"""
import json, os, sys, random
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.append(HERE)
import orbital_plates_rig as rig

LANES_JSON = os.path.join(os.path.expanduser("~"), "Documents", "OrbitalPlates", "refs", "sunset_route_lanes.json")
# lateral offsets RELATIVE TO OUR LANE (cm, + = right/kerb side). Our lane is 6.8 m right of the OSM centreline.
OFF = {"parked": 360.0, "adjacent_eb": -340.0, "oncoming_1": -850.0, "oncoming_2": -1190.0}
DURATION_S = 30.0          # quick test; 120 for the MVP plate

rig.CONFIG.update({
    "content_root": "/Game/OrbitalPlates/Cesium",
    "build_placeholder_world": False,
    "duration_s": DURATION_S,
})
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    unreal.log(f"[OrbitalPlates/Cesium] {m}")


def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


# ---------------------------------------------------------------- traffic on real lanes
def ensure_traffic_real():
    rnd = random.Random(1985)
    length = rig.CONFIG["placeholder_route_length_cm"]
    v = rig.CONFIG["speed_mps"]
    plan = [("Traffic_Lead", 0.0, 3500.0, v), ("Traffic_Lead2", 0.0, 9000.0, v * 0.97)]
    for i in range(6):                                   # adjacent EB lane, a little faster/slower
        plan.append((f"Traffic_Adjacent{i+1:02d}", OFF["adjacent_eb"], 2000.0 + i * rnd.uniform(4000, 9000), v * rnd.uniform(0.9, 1.1)))
    for i in range(30):                                  # oncoming, two lanes
        lane = OFF["oncoming_1"] if i % 2 == 0 else OFF["oncoming_2"]
        plan.append((f"Traffic_Oncoming{i+1:02d}", lane, 8000.0 + i * rnd.uniform(6000, 11000), -v * rnd.uniform(0.8, 1.15)))
    x, i = 1200.0, 0
    while x < length and i < 60:                         # kerb parking with gaps
        if rnd.random() > 0.25:
            plan.append((f"Traffic_Parked{i+1:02d}", OFF["parked"], x, 0.0)); i += 1
        x += rnd.uniform(600, 2400)
    out = [(rig.ensure_proxy(label), off, start, spd) for label, off, start, spd in plan]
    log(f"traffic: {len(out)} proxies on real lanes")
    return out


# ---------------------------------------------------------------- route spline from OSM + terrain
def build_route(lonlath):
    geo = unreal.CesiumGeoreference.get_default_georeference(world())
    pts = [geo.transform_longitude_latitude_height_position_to_unreal(p) for p in lonlath]
    route = find(rig.CONFIG["route_name"])
    if route:
        EAS.destroy_actor(route)
    route = EAS.spawn_actor_from_class(unreal.CameraRig_Rail, unreal.Vector(0, 0, 0))
    route.set_actor_label(rig.CONFIG["route_name"])
    sp = route.get_rail_spline_component()
    sp.clear_spline_points()
    for p in pts:
        sp.add_spline_point(p, unreal.SplineCoordinateSpace.WORLD)
    for i in range(len(pts)):
        sp.set_spline_point_type(i, unreal.SplinePointType.CURVE_CLAMPED)
    sp.update_spline()
    rig.CONFIG["placeholder_route_length_cm"] = sp.get_spline_length()
    log(f"route spline: {len(pts)} points, {sp.get_spline_length()/100:.0f} m, z {min(p.z for p in pts)/100:.1f}..{max(p.z for p in pts)/100:.1f} m")


def finish(lonlath):
    build_route(lonlath)
    rig.ensure_traffic = ensure_traffic_real
    rig.main()                      # rig keeps the existing PlateRoute, skips the box world
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("rig done")


def main():
    lanes = json.load(open(LANES_JSON))["lanes"]["ours"]
    terrain = find("Cesium_WorldTerrain")
    google = find("Google3D_ReferenceOnly_DONOTRENDER")
    if google:
        google.set_editor_property("create_physics_meshes", False)   # never let the reference mesh drive anything
    # The async most-detailed height sampler isn't exposed to Python in 2.29, so trace down onto the
    # terrain tileset only (ignore buildings + the Google reference). Terrain LOD depends on what the
    # editor camera has streamed — park the viewport above the route before running.
    geo = unreal.CesiumGeoreference.get_default_georeference(world())
    h0 = geo.get_origin_longitude_latitude_height().z
    ignore = [a for a in (find("Cesium_OSMBuildings"), google) if a]
    out, miss = [], 0
    for lat, lon in lanes:
        top = geo.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(lon, lat, h0 + 300.0))
        bot = geo.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(lon, lat, h0 - 300.0))
        hit = unreal.SystemLibrary.line_trace_single(world(), top, bot, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     True, ignore, unreal.DrawDebugTrace.NONE, True)
        if isinstance(hit, tuple):
            hit = hit[-1] if hit and hit[0] else None
        if hit and hit.to_tuple()[0]:
            llh = geo.transform_unreal_position_to_longitude_latitude_height(hit.to_tuple()[4])
            out.append(unreal.Vector(lon, lat, llh.z))
        else:
            out.append(None); miss += 1
    # fill misses from neighbours (or the origin height if everything missed)
    known = [(i, v.z) for i, v in enumerate(out) if v]
    for i, v in enumerate(out):
        if v is None:
            z = min(known, key=lambda k: abs(k[0] - i))[1] if known else h0
            out[i] = unreal.Vector(lanes[i][1], lanes[i][0], z)
    log(f"terrain traces: {len(lanes) - miss}/{len(lanes)} hit, height {min(p.z for p in out):.1f}..{max(p.z for p in out):.1f} m")
    finish(out)


main()
