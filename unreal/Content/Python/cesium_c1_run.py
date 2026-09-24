"""
cesium_c1_run.py — one-shot: real-street C1 depth test on Cesium geometry.
Triggered by init_unreal.py when Saved/run_cesium_c1.flag exists.

Sunset Blvd EASTBOUND, La Brea Ave -> Gower St (2.08 km, 0.13 deg N of E, straight).
PlateRoute = centre of the RIGHT-HAND through lane, 6.6 m south of the OSM centreline
(4 through lanes + centre turn lane, parking lane at the kerb). Ground heights come from
Cesium World Terrain (async sampler; falls back to streamed line traces).
Renders SEQ_PlateRing_C1 (30 s) to Saved/PlateRenders/Cesium, writes Saved/cesium_c1_status.txt,
quits the editor. PlatesMain / box-street assets are not touched.
"""
import sys, os, json, math, traceback, unreal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import orbital_plates_rig as rig
import cesium_route_level as crl
import world_dress

LANE_START = (-118.3440998, 34.0979128)   # lon, lat (right-hand lane centre at La Brea)
LANE_END = (-118.3215900, 34.0979552)     # at Gower
STEP_M = 25.0
LEVEL = "/Game/OrbitalPlates/Cesium/PlatesCesium"
SAVED = unreal.Paths.project_saved_dir()
MARK = os.path.join(SAVED, "cesium_c1_status.txt")
RAW = os.path.join(SAVED, "cesium_route_raw.json")
RENDER_JOBS = ["SEQ_PlateRing_C5", "SEQ_PlateRing_C3", "SEQ_PlateRing_C7"]   # rear + side profiles first
# Optional per-run overrides: Saved/run_options.json, e.g. {"era": "1955", "dress": true, "duration_s": 30,
# "jobs": ["SEQ_PlateRing_C5"]}. Absent = the defaults below (no street dressing, 120 s, C5/C3/C7).
OPTS_PATH = os.path.join(unreal.Paths.project_saved_dir(), "run_options.json")
OPTS = json.load(open(OPTS_PATH)) if os.path.exists(OPTS_PATH) else {}
RENDER_JOBS = OPTS.get("jobs", RENDER_JOBS)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
S = {"t": 0, "h": None, "phase": "wait", "act": None, "llh": [], "hits": [], "i": 0, "wait": 0}

rig.CONFIG.update({
    "duration_s": 120.0,                         # 2 min MVP plate: 1.61 km at 30 mph, fits the 2.08 km route
    "build_placeholder_world": False,
    "content_root": "/Game/OrbitalPlates/Cesium",
    "oncoming_offsets_cm": [-1000.0, -1350.0],   # oncoming lanes beyond the centre turn lane
    "parked_offset_cm": 290.0,                   # centre of the 2.4 m parking lane, kerb at +410
    "inner_lane_cars": 5,                        # same-direction cars in the lane to our left
    "proxy_ground_cm": 0.0,                      # spline sits on the real asphalt
    "camera_start_cm": 6000.0,                   # 60 m of road behind us for following traffic
    "following_traffic": True,
})
rig.CONFIG["render"]["output_dir"] = "{project_dir}/Saved/PlateRenders/Cesium/{sequence_name}"
if "duration_s" in OPTS:
    rig.CONFIG["duration_s"] = float(OPTS["duration_s"])


def mark(s):
    open(MARK, "a").write(s + "\n"); unreal.log("[CESIUM_C1] " + s)


def actors(cls):
    return [a for a in EAS.get_all_level_actors() if isinstance(a, cls)]


def lane_lonlat():
    (x0, y0), (x1, y1) = LANE_START, LANE_END
    L = math.hypot((x1 - x0) * 111320 * math.cos(math.radians(y0)), (y1 - y0) * 110950)
    n = int(L // STEP_M)
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def setup():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        les.load_level(LEVEL)
    else:
        crl.main()
    world = UES.get_editor_world()
    ws = world.get_world_settings()
    try:
        ws.set_editor_property("enable_world_bounds_checks", False)
    except Exception as e:
        mark(f"bounds-check toggle failed: {e}")
    geos = actors(unreal.CesiumGeoreference)
    S["geo"] = geos[0]
    S["geo"].set_editor_property("origin_latitude", LANE_START[1])
    S["geo"].set_editor_property("origin_longitude", LANE_START[0])
    tiles = actors(unreal.Cesium3DTileset)
    S["terrain"] = S["buildings"] = None
    for t in tiles:
        aid = t.get_editor_property("ion_asset_id")
        if aid == 1:
            S["terrain"] = t
        elif aid == 96188:
            S["buildings"] = t
        elif aid == 2275207:        # Google: layout reference only, never rendered
            t.set_actor_hidden_in_game(True)
            t.set_editor_property("suspend_update", True)
    mark(f"level loaded; georef {geos[0].get_actor_label()}, tilesets {[t.get_actor_label() for t in tiles]}")
    S["ll"] = lane_lonlat()


def start_sampling():
    if os.path.exists(RAW):     # traced last run — reuse (delete the file to re-trace)
        S["hits"] = [unreal.Vector(*v) for v in json.load(open(RAW))]
        S["phase"] = "build"; mark(f"reusing {len(S['hits'])} traced points"); return
    try:
        A = unreal.CesiumSampleHeightMostDetailedAsyncAction
        act = A.sample_height_most_detailed(S["terrain"], [unreal.Vector(lo, la, 0.0) for lo, la in S["ll"]])
        act.on_heights_sampled.add_callable(on_heights)
        S["act"] = act
        act.activate()
        S["phase"] = "sampling"
        mark(f"async height sampling {len(S['ll'])} points")
    except Exception as e:
        mark(f"async sampler unavailable ({e}) — falling back to streamed line traces")
        S["phase"] = "trace"


def on_heights(results, warnings):
    try:
        llh = []
        for r in results:
            v = r.get_editor_property("longitude_latitude_height")
            llh.append((v.x, v.y, v.z, r.get_editor_property("sample_success")))
        bad = sum(1 for p in llh if not p[3])
        mark(f"heights sampled, {bad} failed, warnings {list(warnings)[:3]}")
        if bad > len(llh) // 4:
            S["phase"] = "trace"; return
        S["llh"] = llh
        S["phase"] = "build"
    except Exception:
        mark("ERROR in on_heights " + traceback.format_exc()); S["phase"] = "trace"


def trace_step():
    """Fallback: park the editor camera over each lane point until terrain has loaded, trace down."""
    geo = S["geo"]
    lo, la = S["ll"][S["i"]]
    top = geo.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(lo, la, 400.0))
    bot = geo.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(lo, la, -200.0))
    if S["wait"] == 0:
        UES.set_level_viewport_camera_info(unreal.Vector(top.x - 3000, top.y, top.z), unreal.Rotator(0, -60, 0))
    S["wait"] += 1
    if S["wait"] < 20 or (S["terrain"].get_editor_property("load_progress") < 99.9 and S["wait"] < 600):
        return
    ignore = [a for a in [S["buildings"]] if a]
    hit = unreal.SystemLibrary.line_trace_single(UES.get_editor_world(), top, bot,
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                                                 unreal.DrawDebugTrace.NONE, True)
    S["hits"].append(hit.to_tuple()[4] if hit else None)
    S["i"] += 1; S["wait"] = 0
    if S["i"] >= len(S["ll"]):
        S["phase"] = "build"


# Sunset cross-section (70 ft roadway, 15 ft sidewalks): centre turn lane 3.3 m, 2 through lanes
# of 3.3 m each way, 2.45 m parking lanes. Our lane centre is 6.6 m right of the centreline.
KERB_R_CM = 410.0            # right kerb, from our lane centre
KERB_L_CM = -1720.0          # far (left) kerb
SIDEWALK_W_CM = 460.0
KERB_H_CM = 22.0            # 15 cm vanished in log depth


# signalised intersections along the route (m from La Brea, OSM traffic_signals)
INTERSECTIONS_M = [0.0, 230.0, 499.2, 690.0, 809.7, 1002.3, 1204.1, 1345.1, 1410.2, 1606.0, 1744.9, 1875.4, 2007.7]
CROSS_HALF_CM = 800.0        # cross street half-width: kerb/sidewalk break
LAMP_SPACING_CM = 4000.0


def _box(label, loc, rot, size_cm, mesh):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
    a.set_actor_label(label)
    a.static_mesh_component.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0))
    a.set_folder_path("Street")
    return a


def build_street_furniture(spl):
    """Streetlight poles (8.5 m, 2 m arm over the road) every 40 m on both sidewalks, skipping
    cross streets; signal masts (6 m pole, 7 m arm) on the near-right and far-left corners."""
    cyl = unreal.load_asset("/Engine/BasicShapes/Cylinder")
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    total = spl.get_spline_length()
    near_x = lambda d: any(abs(d - m * 100) < CROSS_HALF_CM + 300 for m in INTERSECTIONS_M)

    def at(d, lat):
        p = spl.get_location_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD)
        r = spl.get_right_vector_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD)
        yaw = spl.get_rotation_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD).yaw
        return unreal.Vector(p.x + r.x * lat, p.y + r.y * lat, p.z + KERB_H_CM), r, yaw

    def pole(label, d, lat, h, arm, toward):   # toward = -1 arm points left (over road from right side)
        base, r, yaw = at(d, lat)
        _box(label, unreal.Vector(base.x, base.y, base.z + h / 2), unreal.Rotator(0, 0, 0), (22, 22, h), cyl)
        c = unreal.Vector(base.x + r.x * toward * arm / 2, base.y + r.y * toward * arm / 2, base.z + h - 15)
        _box(label + "_Arm", c, unreal.Rotator(0, 0, yaw + 90), (arm, 14, 14), cube)

    n = 0
    for side, lat, toward, phase in (("R", KERB_R_CM + 70, -1, 0.0), ("L", KERB_L_CM - 70, 1, LAMP_SPACING_CM / 2)):
        d = 1500.0 + phase
        while d < total - 500:
            if not near_x(d):
                pole(f"Street_Lamp{side}_{n:03d}", d, lat, 850.0, 200.0, toward); n += 1
            d += LAMP_SPACING_CM
    k = 0
    for m in INTERSECTIONS_M:
        dm = m * 100
        if dm - CROSS_HALF_CM - 150 > 0:
            pole(f"Street_Signal_{k:02d}", dm - CROSS_HALF_CM - 150, KERB_R_CM + 60, 600.0, 700.0, -1); k += 1
        if dm + CROSS_HALF_CM + 150 < total:
            pole(f"Street_Signal_{k:02d}", dm + CROSS_HALF_CM + 150, KERB_L_CM - 60, 600.0, 700.0, 1); k += 1
    mark(f"street furniture: {n} lamps, {k} signal masts")


def build_street_edges(spl):
    """Raised sidewalk slabs along both real kerb lines, following the lane spline.
    The slab's inner face is the kerb; slabs run 60 cm down so terrain doesn't poke through."""
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith("Street_"):
            EAS.destroy_actor(a)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    total = spl.get_spline_length()
    depth = 60.0
    # runs of sidewalk between cross streets, cut into <=25 m slabs
    cuts, prev = [], 0.0
    for m in INTERSECTIONS_M:
        c0, c1 = m * 100 - CROSS_HALF_CM, m * 100 + CROSS_HALF_CM
        if c0 > prev:
            cuts.append((prev, min(c0, total)))
        prev = max(prev, c1)
    if prev < total:
        cuts.append((prev, total))
    spans = []
    for r0, r1 in cuts:
        k = max(1, int(math.ceil((r1 - r0) / 2500.0)))
        spans += [(r0 + (r1 - r0) * j / k, r0 + (r1 - r0) * (j + 1) / k) for j in range(k)]
    n = len(spans)
    for side, kerb, sgn in (("R", KERB_R_CM, 1.0), ("L", KERB_L_CM, -1.0)):
        for i, (d0, d1) in enumerate(spans):
            if d1 - d0 < 10:
                continue
            p0 = spl.get_location_at_distance_along_spline(d0, unreal.SplineCoordinateSpace.WORLD)
            p1 = spl.get_location_at_distance_along_spline(d1, unreal.SplineCoordinateSpace.WORLD)
            dm = (d0 + d1) / 2
            pm = spl.get_location_at_distance_along_spline(dm, unreal.SplineCoordinateSpace.WORLD)
            right = spl.get_right_vector_at_distance_along_spline(dm, unreal.SplineCoordinateSpace.WORLD)
            off = kerb + sgn * SIDEWALK_W_CM / 2
            c = unreal.Vector(pm.x + right.x * off, pm.y + right.y * off, pm.z + KERB_H_CM - depth / 2)
            dx, dy, dz = p1.x - p0.x, p1.y - p0.y, p1.z - p0.z
            seg = math.sqrt(dx * dx + dy * dy + dz * dz)
            rot = unreal.Rotator(0.0, math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx)))
            a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, c, rot)
            a.set_actor_label(f"Street_Sidewalk{side}_{i:03d}")
            a.static_mesh_component.set_static_mesh(cube)
            a.set_actor_scale3d(unreal.Vector(seg / 100.0, SIDEWALK_W_CM / 100.0, depth / 100.0))
            a.set_folder_path("Street")
    mark(f"street edges: {2 * n} sidewalk slabs, kerbs at {KERB_R_CM/100:+.1f} m / {KERB_L_CM/100:+.1f} m")


def build_and_render():
    geo = S["geo"]
    if S["llh"]:
        h0 = S["llh"][0][2]
        geo.set_editor_property("origin_height", h0)
        pts = [geo.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(x, y, z))
               for x, y, z, _ in S["llh"]]
    else:
        pts = [p for p in S["hits"] if p]
        json.dump([[p.x, p.y, p.z] for p in pts], open(RAW, "w"))
    # median-of-5 kills trace outliers (tile not yet at full detail), then mean-of-5 smooths
    zs = [p.z for p in pts]
    zs = [sorted(zs[max(0, i - 2):i + 3])[len(zs[max(0, i - 2):i + 3]) // 2] for i in range(len(zs))]
    pts = [unreal.Vector(p.x, p.y, z) for p, z in zip(pts, zs)]
    mark(f"{len(pts)} lane points; start {pts[0]}, end {pts[-1]}")
    zs = [p.z for p in pts]
    sm = [sum(zs[max(0, i - 2):i + 3]) / len(zs[max(0, i - 2):i + 3]) for i in range(len(zs))]
    pts = [unreal.Vector(p.x, p.y, z) for p, z in zip(pts, sm)]
    json.dump([[p.x, p.y, p.z] for p in pts], open(os.path.join(SAVED, "cesium_route_points.json"), "w"))

    route = rig.find_actor(rig.CONFIG["route_name"])
    if not route:
        route = EAS.spawn_actor_from_class(unreal.CameraRig_Rail, unreal.Vector(0, 0, 0))
        route.set_actor_label(rig.CONFIG["route_name"])
    route.set_actor_location(unreal.Vector(0, 0, 0), False, False)
    spl = route.get_rail_spline_component()
    spl.clear_spline_points()
    for p in pts:
        spl.add_spline_point(p, unreal.SplineCoordinateSpace.WORLD)
    spl.update_spline()
    rig.CONFIG["placeholder_route_length_cm"] = spl.get_spline_length()
    mark(f"PlateRoute {spl.get_spline_length()/100:.0f} m")

    build_street_edges(spl)
    build_street_furniture(spl)
    if OPTS.get("dress"):
        # parked proxies are re-planned around driveways / bus stops, so drop the old set (and their cabin parts)
        for a in EAS.get_all_level_actors():
            if a.get_actor_label().startswith("Traffic_Parked"):
                EAS.destroy_actor(a)
        rig.CONFIG["no_park_m"] = world_dress.dress(spl, OPTS.get("era", "timeless"), OPTS.get("seed", 1978),
                                                    INTERSECTIONS_M, mark)
    else:
        world_dress.clear()
    rig.main()
    mark("rig built + level saved")
    # diagnostics: where traffic sits relative to our lane at frame 0 (lateral + = right/kerb)
    for lbl in ["PlateRig", "Traffic_Lead", "Traffic_Inner01", "Traffic_Oncoming01", "Traffic_Parked01"]:
        a = rig.find_actor(lbl)
        if a:
            loc = a.get_actor_location()
            mark(f"pos {lbl}: x {loc.x/100:.1f} m, y {loc.y/100:.1f} m (south +), z {loc.z/100:.2f} m")
    preset = unreal.EditorAssetLibrary.load_asset(rig.CONFIG["content_root"] + "/MRQ_Plates")
    aa = preset.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.engine_warm_up_count = 240      # let tiles stream in PIE before frame 0
    aa.render_warm_up_count = 32
    unreal.EditorAssetLibrary.save_loaded_asset(preset)
    qs = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    for j in qs.get_queue().get_jobs():
        j.set_is_enabled(j.job_name in RENDER_JOBS)
        j.set_configuration(preset)
    ex = qs.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
    S["ex"] = ex
    ex.on_executor_finished_delegate.add_callable(finished)
    mark("render started")
    S["phase"] = "render"


def finished(executor, success):
    mark(f"render finished success={success}")
    unreal.SystemLibrary.quit_editor()


def tick(dt):
    S["t"] += 1
    try:
        if S["phase"] == "wait" and S["t"] == 300:
            setup(); S["phase"] = "loadwait"; S["t0"] = S["t"]
        elif S["phase"] == "loadwait" and S["t"] - S["t0"] > 120:
            start_sampling()
        elif S["phase"] == "sampling" and S["t"] - S["t0"] > 6000:
            mark("async sampling timed out — trace fallback"); S["phase"] = "trace"
        elif S["phase"] == "trace":
            trace_step()
        elif S["phase"] == "build":
            S["phase"] = "building"; build_and_render()
    except Exception:
        mark("ERROR " + traceback.format_exc())
        S["phase"] = "dead"
        unreal.SystemLibrary.quit_editor()


mark(f"---- run start {OPTS if OPTS else '(default options)'}")
S["h"] = unreal.register_slate_post_tick_callback(tick)
