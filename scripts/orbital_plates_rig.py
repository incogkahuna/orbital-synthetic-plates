"""
orbital_plates_rig.py (v9)  —  Orbital Synthetic Plates · Unreal 5.8 rig builder

v9: 120 s / 1.75 km route, 30 oncoming + ~45 parked proxies, street extended,
    ring cameras offset 22 cm from the nodal centre.

Run inside the Unreal Editor (Python Editor Script Plugin), either from the
Output Log (`py "C:/.../orbital_plates_rig.py"`) or through the Unreal MCP
Python toolset.

What it builds, idempotently:
  1. /Game/OrbitalPlates/  content folder
  2. BP-free "PlateRig" actor: an empty root + 9 CineCameraActors attached at
     ONE nodal origin, 8 x 45° around the yaw axis, plus C9 pitched up for
     the reflection view.  All cameras share filmback + focal length.
  3. A drive spline (if none named "PlateRoute" exists) — a straight 400 m
     placeholder you replace with the real route.
  4. Nine Level Sequences SEQ_PlateRing_C1..C9: the rig root keyed along the
     spline at a constant speed, one camera cut each.
  5. A Movie Render Queue preset MRQ_Plates: 16-bit multilayer EXR, beauty +
     world-depth + world-normal + motion-vector post-process passes,
     anti-aliasing / motion blur settings for a clean depth pass.
  6. Nine MRQ jobs queued (not started).

Everything is parameterised in CONFIG.  Re-running updates in place.
"""

import math
import unreal

CONFIG = {
    "content_root": "/Game/OrbitalPlates",
    "rig_name": "PlateRig",
    "route_name": "PlateRoute",
    "camera_height_cm": 150.0,          # nodal origin above the road: driver eye level (was 180, read as roof height)
    "yaw_step_deg": 45.0,
    "ring_count": 8,
    "reflection_pitch_deg": 35.0,
    "sensor_width_mm": 23.76,            # Super35 16:9
    "sensor_height_mm": 13.365,
    "hfov_deg": 65.0,                    # -> ~20° overlap at 45° spacing
    "fps": 24,                           # use 24000/1001 in MRQ output for 23.976
    "speed_mps": 13.4,                   # 30 mph
    "duration_s": 120.0,                 # 2-minute plate (MVP); 30 s for quick tests
    "placeholder_route_length_cm": 175000.0,  # 1.75 km: 120 s at 13.4 m/s + margin
    "ring_offset_cm": 22.0,              # cameras sit 22 cm out from the nodal centre (physical-array look)
    "build_placeholder_world": True,     # box street; set False once a real level exists
    "render": {
        "width": 1280, "height": 720,    # S3 working res; S4 upscales
        "output_dir": "{project_dir}/Saved/PlateRenders/{sequence_name}",
        "file_name_format": "{sequence_name}_{render_pass}.{frame_number}",
        "spatial_samples": 1,
        "temporal_samples": 1,           # 1 = no motion blur, clean depth
    },
}

EAL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def log(msg):
    unreal.log(f"[OrbitalPlates] {msg}")


def focal_from_hfov(sensor_w_mm, hfov_deg):
    return sensor_w_mm / (2.0 * math.tan(math.radians(hfov_deg) / 2.0))


def find_actor(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def ensure_folder(path):
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)


# ----------------------------------------------------------------------------
# 1. route spline
# ----------------------------------------------------------------------------
def ensure_route():
    """The route is a CameraRig_Rail actor: it ships with an editable spline and
    a rail preview, so the artist can drag points in the viewport.  The spline
    is the CENTRE OF OUR LANE (US: ~1.8 m right of the road centre line), not
    the road centre — that is what puts the plate in traffic."""
    route = find_actor(CONFIG["route_name"])
    if route and isinstance(route, unreal.CameraRig_Rail):
        log(f"route '{CONFIG['route_name']}' exists — keeping it")
        return route
    if route:
        log("route actor is the wrong class — replacing it")
        EAS.destroy_actor(route)
    route = EAS.spawn_actor_from_class(unreal.CameraRig_Rail, unreal.Vector(0, 0, 0))
    route.set_actor_label(CONFIG["route_name"])
    spline = route.get_rail_spline_component()
    spline.clear_spline_points()
    length = CONFIG["placeholder_route_length_cm"]
    spline.add_spline_point(unreal.Vector(0, 0, 0), unreal.SplineCoordinateSpace.WORLD)
    spline.add_spline_point(unreal.Vector(length, 0, 0), unreal.SplineCoordinateSpace.WORLD)
    spline.set_spline_point_type(0, unreal.SplinePointType.LINEAR)
    spline.set_spline_point_type(1, unreal.SplinePointType.LINEAR)
    spline.update_spline()
    log("spawned placeholder straight route (replace with the real drive)")
    return route


def route_spline(route):
    return route.get_rail_spline_component()


# ----------------------------------------------------------------------------
# 1b. traffic proxies — grey boxes with car silhouettes so the depth pass has
#     real vehicles in real lanes; the restyle dresses them into period cars.
# ----------------------------------------------------------------------------
LANE_W = 360.0      # cm, US lane
CAR_L, CAR_W, CAR_H = 450.0, 180.0, 140.0
WOBBLE = {"Traffic_Follow1": (400.0, 17.0), "Traffic_Follow2": (300.0, 23.0)}   # (amp cm, period s)
CAR_BODY_H, CAR_CAB_H, CAR_CLEAR = 75.0, 60.0, 25.0   # 1.6 m tall overall, wheel gap reads in depth


def _cube_actor(label, movable=True):
    a = find_actor(label)
    if not a:
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
        a.set_actor_label(label)
        smc = a.static_mesh_component
        smc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        smc.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    return a


def _proxy_part(parent, label, L, W, body_h, size_cm, offset_cm):
    """Axis-aligned block attached to a car body. Relative values live in the body's scaled
    space (cube = 100 cm), so sizes divide by the body size and offsets by the body scale."""
    p = _cube_actor(label)
    if p.get_attach_parent_actor() != parent:
        p.attach_to_actor(parent, "", unreal.AttachmentRule.KEEP_RELATIVE,
                          unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
    p.root_component.set_relative_scale3d(unreal.Vector(size_cm[0] / L, size_cm[1] / W, size_cm[2] / body_h))
    p.root_component.set_relative_location(
        unreal.Vector(offset_cm[0] / (L / 100.0), offset_cm[1] / (W / 100.0), offset_cm[2] / (body_h / 100.0)),
        False, False)
    return p


def ensure_proxy(label, size=(CAR_L, CAR_W, CAR_H)):
    """Car-shaped proxy so direction reads in depth: a low body (the keyed actor, pivot at
    body centre, +X = front) plus a cabin set well toward the REAR (long hood, short trunk)
    and a half-height step in front of the cabin standing in for a raked windshield.
    Symmetric boxes let Wan guess the facing and it drew parked cars backward (2026-09-23)."""
    L, W, H = size
    body_h = CAR_BODY_H
    a = _cube_actor(label)
    stale = find_actor(label + "_Car")                    # a real mesh from an earlier run: back to a box
    if stale:
        EAS.destroy_actor(stale)
    a.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    a.set_actor_scale3d(unreal.Vector(L / 100.0, W / 100.0, body_h / 100.0))
    cab_l, cab_w, cab_h = L * 0.40, W * 0.78, CAR_CAB_H
    cab_x = -0.13 * L                                     # cabin spans -0.33L..+0.07L: hood 0.43L, trunk 0.17L
    _proxy_part(a, label + "_Cabin", L, W, body_h, (cab_l, cab_w, cab_h), (cab_x, 0.0, body_h / 2 + cab_h / 2))
    scr_l, scr_h = L * 0.10, cab_h * 0.5                  # windshield step, front side of the cabin only
    _proxy_part(a, label + "_Screen", L, W, body_h, (scr_l, cab_w, scr_h),
                (cab_x + cab_l / 2 + scr_l / 2, 0.0, body_h / 2 + scr_h / 2))
    return a


# ---- real car meshes (Fab) -----------------------------------------------------------------------------------
# Static meshes under /Game/Vehicles/<era>/ replace the box proxies (P10, backward parked cars). The keyed proxy
# actor stays as an invisible anchor (pivot = body centre, +X = front); the car is a child actor placed on the
# ground. Optional /Game/Vehicles/<era>/manifest.json (Content/Vehicles/<era>/manifest.json on disk):
#   {"SM_Sedan_A": {"yaw": 90, "length_m": 5.2, "kinds": ["moving", "parked"]}, "SM_Bus": {"kinds": ["moving"]}}
# yaw = degrees to turn the mesh so its front points +X (default: auto - long axis, front assumed +X/+Y);
# length_m forces a length; otherwise meshes already at real scale (3.5-13 m long) are kept, others go to 4.5 m.
_CAR_LIB = {}


def car_library(era):
    if era in _CAR_LIB:
        return _CAR_LIB[era]
    import json, os
    root = f"/Game/Vehicles/{era}"
    man_path = os.path.join(unreal.Paths.project_content_dir(), "Vehicles", era, "manifest.json")
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    lib = []
    # "_roots": extra folders to pull cars from in place (e.g. a Fab pack under /Game/Dekogon_...)
    for r in [root] + list(man.get("_roots", [])):
        if not unreal.EditorAssetLibrary.does_directory_exist(r):
            continue
        for p in sorted(unreal.EditorAssetLibrary.list_assets(r, recursive=True, include_folder=False)):
            cls = str(unreal.EditorAssetLibrary.find_asset_data(p).asset_class_path.asset_name)
            if cls not in ("StaticMesh", "Blueprint"):     # skip textures / materials without loading them
                continue
            a = unreal.load_asset(p.split(".")[0])
            name = a.get_name() if a else ""
            opt = man.get(name, {})
            if opt.get("skip"):
                continue
            # a single StaticMesh, or a Blueprint that assembles a split car (body + wheels, e.g. Dekogon BP_*)
            if isinstance(a, unreal.StaticMesh) and not man.get("_blueprints_only"):
                lib.append((a, opt))
            elif isinstance(a, unreal.Blueprint) and name.upper().startswith("BP_"):
                lib.append((a, opt))
    _CAR_LIB[era] = lib
    log(f"car library {era}: {len(lib)} meshes" + (f" ({', '.join(m.get_name() for m, _ in lib)})" if lib else
                                                   f" - none under {root}, box proxies stay"))
    return lib


def dress_car(anchor, label, kind, rnd):
    """Swap one proxy for a real mesh. kind = 'moving' | 'parked'. Returns True if a mesh was used."""
    lib = [(m, o) for m, o in car_library(CONFIG.get("era", "timeless")) if kind in o.get("kinds", ["moving", "parked"])]
    if not lib:
        return False
    mesh, opt = lib[rnd.randrange(len(lib))]
    for part in (label + "_Cabin", label + "_Screen"):
        p = find_actor(part)
        if p:
            EAS.destroy_actor(p)
    anchor.static_mesh_component.set_static_mesh(None)
    anchor.set_actor_scale3d(unreal.Vector(1, 1, 1))
    stale = find_actor(label + "_Car")
    if stale:
        EAS.destroy_actor(stale)
    if isinstance(mesh, unreal.Blueprint):
        # spawn once at the world origin, unrotated, to measure it, then hang it off the anchor
        body = EAS.spawn_actor_from_class(mesh.generated_class(), unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        body.set_actor_label(label + "_Car")
        for c in body.get_components_by_class(unreal.PrimitiveComponent):
            c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        o, e = body.get_actor_bounds(False)
        bb = unreal.Box(unreal.Vector(o.x - e.x, o.y - e.y, o.z - e.z), unreal.Vector(o.x + e.x, o.y + e.y, o.z + e.z))
        body.attach_to_actor(anchor, "", unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE,
                             unreal.AttachmentRule.KEEP_RELATIVE, False)
    else:
        bb = mesh.get_bounding_box()
        body = None
    ex, ey = bb.max.x - bb.min.x, bb.max.y - bb.min.y
    yaw = opt.get("yaw", 0.0 if ex >= ey else -90.0)
    length = max(ex, ey)
    s = (opt["length_m"] * 100.0 / length) if "length_m" in opt else (1.0 if 350.0 <= length <= 1300.0 else CAR_L / length)
    cx, cy = (bb.max.x + bb.min.x) / 2 * s, (bb.max.y + bb.min.y) / 2 * s
    r = math.radians(yaw)
    rx, ry = cx * math.cos(r) - cy * math.sin(r), cx * math.sin(r) + cy * math.cos(r)
    if body is None:
        body = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
        body.set_actor_label(label + "_Car")
        body.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        body.attach_to_actor(anchor, "", unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE,
                             unreal.AttachmentRule.KEEP_RELATIVE, False)
        body.static_mesh_component.set_static_mesh(mesh)
    body.root_component.set_relative_scale3d(unreal.Vector(s, s, s))
    body.root_component.set_relative_rotation(unreal.Rotator(0.0, 0.0, yaw), False, False)   # (roll, pitch, yaw)
    ground = -(CAR_CLEAR + CAR_BODY_H / 2.0)                  # anchor sits at body centre; wheels go on the road
    body.root_component.set_relative_location(unreal.Vector(-rx, -ry, ground - bb.min.z * s), False, False)
    return True


def passing_lane_plan(rnd):
    """Same-direction traffic in the lane to our left, built around pass events (Danny, R4 / P7 2026-09-24):
    a car overtakes us, or we overtake it, every 6-14 s. Relative speed is 2-5 m/s, so a car spends 2-5 s
    alongside and never hovers (cars at ~our speed rocked back and forth in v1 C7). Each car gets a gentle speed
    drift (WOBBLE, peak < 0.7 m/s, so it never reverses relative to us), cars keep a 12 m gap, and no car may pop
    in within 200 m of the camera. Replaces the fixed Passer / Inner cars."""
    T, v = CONFIG["duration_s"], CONFIG["speed_mps"]
    cam0 = CONFIG.get("camera_start_cm", 0.0) / 100.0
    # The lane flows in phases of 25-45 s, faster (65%) or slower than us; cars in one phase share its speed
    # (+/-0.3 m/s) so they can't run into each other. v10 drew per-car speeds and rejected any pair that ever met,
    # which in one lane is nearly every pair: 1 car in 30 s.
    phases, pt = [], 0.0
    while pt < T:
        dv = rnd.uniform(2.0, 5.0) if rnd.random() < 0.65 else -rnd.uniform(2.0, 4.0)
        phases.append((pt, dv)); pt += rnd.uniform(25.0, 45.0)
    cars, t = [], rnd.uniform(3.0, 7.0)
    while t < T - 2.0:
        dv = [p for p in phases if p[0] <= t][-1][1] + rnd.uniform(-0.3, 0.3)
        rel0 = -dv * t                                  # metres ahead of the camera at t = 0; passes us at t
        d0 = cam0 + rel0                                # absolute route distance at t = 0
        ok = True
        if d0 < 0:                                      # hidden until it enters at the route start...
            t_enter = -d0 / (v + dv)
            ok = cam0 + v * t_enter > 200.0             # ...which must happen out of depth range (> 200 m)
        # 12 m gap, checked only where it can be seen (within 150 m of the camera)
        for c in cars if ok else []:
            for k in range(int(T * 2) + 1):
                a, b = rel0 + dv * k / 2, c[0] + c[1] * k / 2
                if abs(a) < 150 and abs(b) < 150 and abs(a - b) < 12.0:
                    ok = False; break
            if not ok: break
        if ok:
            cars.append((rel0, dv))
        t += rnd.uniform(6.0, 14.0) if ok else rnd.uniform(1.5, 3.0)   # blocked: try again a little later
    plan = []
    for i, (rel0, dv) in enumerate(cars):
        label = f"Traffic_Pass{i + 1:02d}"
        WOBBLE[label] = (rnd.uniform(60.0, 120.0), rnd.uniform(12.0, 25.0))
        plan.append((label, -LANE_W, rel0 * 100.0, v + dv))
    log(f"passing lane: {len(plan)} cars, passes every ~6-14 s "
        f"({sum(1 for _, dv in cars if dv > 0)} overtake us, {sum(1 for _, dv in cars if dv < 0)} we overtake)")
    return plan


def ensure_traffic():
    """Returns [(actor, lane_offset_cm, start_dist_cm, speed_mps)].  Negative
    lane offset = left (oncoming lane), positive = right (kerb).  Speed 0 =
    parked.  Negative speed = oncoming."""
    import random
    rnd = random.Random(1985)
    route_len = CONFIG["placeholder_route_length_cm"]
    plan = [
        ("Traffic_Lead",  0.0, 3500.0, CONFIG["speed_mps"]),         # holds ~35 m ahead all run
        ("Traffic_Lead2", 0.0, 9000.0, CONFIG["speed_mps"] * 0.97),  # very slowly closes
    ]
    if CONFIG.get("following_traffic"):
        # behind us, for the rear (C5) and side (C3/C7) plates: needs camera_start_cm of road behind
        plan += [
            ("Traffic_Follow1", 0.0, -1600.0, CONFIG["speed_mps"]),         # 16 m behind, gap breathes +/-4 m
            ("Traffic_Follow2", 0.0, -4200.0, CONFIG["speed_mps"]),
            ("Traffic_Follow3", 0.0, -7000.0, CONFIG["speed_mps"] * 1.01),
        ]
        if not CONFIG.get("passing_traffic"):
            plan += [
                ("Traffic_Passer1", -LANE_W, -2600.0, CONFIG["speed_mps"] * 1.08),  # left lane, draws level ~20 s
                ("Traffic_Passer2", -LANE_W, -6500.0, CONFIG["speed_mps"] * 1.05),
            ]
    if CONFIG.get("passing_traffic"):
        plan += passing_lane_plan(rnd)
    # oncoming: spawn far enough ahead that they keep arriving for the whole drive
    for i in range(30):
        plan.append((f"Traffic_Oncoming{i+1:02d}",
                     CONFIG.get("oncoming_offsets_cm", [-LANE_W])[i % len(CONFIG.get("oncoming_offsets_cm", [-LANE_W]))],
                     8000.0 + i * rnd.uniform(9000, 16000),
                     -CONFIG["speed_mps"] * rnd.uniform(0.8, 1.15)))
    # same-direction cars in the lane to our left (multi-lane boulevards)
    for i in range(CONFIG.get("inner_lane_cars", 0)):
        plan.append((f"Traffic_Inner{i+1:02d}", -LANE_W, 2000.0 + i * rnd.uniform(5000, 9000),
                     CONFIG["speed_mps"] * rnd.uniform(0.9, 1.12)))
    # kerb parking with gaps (driveways, hydrants)
    x, i = 1200.0, 0
    while x < route_len and i < 60:
        no_park = any(a * 100 <= x <= b * 100 for a, b in CONFIG.get("no_park_m", []))   # driveways, bus stops, corners
        if rnd.random() > 0.25 and not no_park:
            plan.append((f"Traffic_Parked{i+1:02d}", CONFIG.get("parked_offset_cm", LANE_W * 0.95), x, 0.0)); i += 1
        x += rnd.uniform(600, 2400)
    out, real = [], 0
    crnd = random.Random(CONFIG.get("car_seed", 1955))
    for label, off, start, spd in plan:
        a = ensure_proxy(label)
        if CONFIG.get("car_meshes", True) and dress_car(a, label, "parked" if spd == 0.0 else "moving", crnd):
            real += 1
        out.append((a, off, start, spd))
    log(f"traffic: {len(out)} cars, {real} real meshes, {len(out) - real} box proxies")
    return out


# ----------------------------------------------------------------------------
# 1c. placeholder street — boxes only. Gives the depth/normal passes real
#     structure (road, kerbs, building masses, poles) so the restyle has
#     something to dress. Replace with Cesium/OSM or a proper kit later.
#     Everything is relative to the lane spline: -Y = left (oncoming, far
#     side), +Y = right (kerb).  Straight-route assumption for the placeholder.
# ----------------------------------------------------------------------------
def ensure_block(label, center, size, mobility=unreal.ComponentMobility.STATIC):
    a = find_actor(label)
    if not a:
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
        a.set_actor_label(label)
        a.static_mesh_component.set_editor_property("mobility", mobility)
        a.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    a.set_actor_location(unreal.Vector(*center), False, False)
    a.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    return a


def ensure_world():
    import random
    rnd = random.Random(1978)
    L0, L1 = -10000.0, CONFIG["placeholder_route_length_cm"] + 20000.0   # street extent along X (cm)
    road_l, road_r = -700.0, 500.0         # road edges relative to lane spline (Y)
    ensure_block("World_Ground", ((L0 + L1) / 2, 0, -60), (L1 - L0 + 40000, 100000, 100))
    ensure_block("World_Road", ((L0 + L1) / 2, (road_l + road_r) / 2, 5), (L1 - L0, road_r - road_l, 20))
    for side, y0, y1 in (("L", road_l - 300, road_l), ("R", road_r, road_r + 300)):
        ensure_block(f"World_Sidewalk_{side}", ((L0 + L1) / 2, (y0 + y1) / 2, 22), (L1 - L0, y1 - y0, 16))
        x = L0
        i = 0
        while x < L1:
            w = rnd.uniform(800, 1600)
            h = rnd.uniform(400, 1000)
            d = rnd.uniform(1000, 2500)
            gap = rnd.choice([0, 0, 0, 300, 600])
            yc = (y1 + d / 2) if side == "R" else (y0 - d / 2)
            ensure_block(f"World_Bldg_{side}{i:03d}", (x + w / 2, yc, 30 + h / 2), (w, d, h))
            x += w + gap
            i += 1
        for j, px in enumerate(range(int(L0), int(L1), 3000)):
            py = (y1 - 50) if side == "R" else (y0 + 50)
            ensure_block(f"World_Pole_{side}{j:02d}", (px, py, 480), (30, 30, 900))
    log("placeholder street built (boxes)")


# ----------------------------------------------------------------------------
# 2. camera ring
# ----------------------------------------------------------------------------
def camera_specs():
    specs = []
    for i in range(CONFIG["ring_count"]):
        specs.append((f"C{i+1}", i * CONFIG["yaw_step_deg"], 0.0))
    specs.append((f"C{CONFIG['ring_count']+1}", 0.0, CONFIG["reflection_pitch_deg"]))
    return specs


def ensure_rig():
    rig = find_actor(CONFIG["rig_name"])
    if rig and not isinstance(rig, unreal.TargetPoint):
        EAS.destroy_actor(rig)
        rig = None
    if not rig:
        # TargetPoint = an empty actor that already has a root scene component
        rig = EAS.spawn_actor_from_class(
            unreal.TargetPoint, unreal.Vector(0, 0, CONFIG["camera_height_cm"]))
        rig.set_actor_label(CONFIG["rig_name"])
        log("spawned PlateRig root (nodal origin)")

    focal = focal_from_hfov(CONFIG["sensor_width_mm"], CONFIG["hfov_deg"])
    cams = {}
    for name, yaw, pitch in camera_specs():
        label = f"{CONFIG['rig_name']}_{name}"
        cam = find_actor(label)
        if not cam:
            cam = EAS.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(0, 0, 0))
            cam.set_actor_label(label)
            cam.attach_to_actor(rig, "", unreal.AttachmentRule.SNAP_TO_TARGET,
                                unreal.AttachmentRule.SNAP_TO_TARGET,
                                unreal.AttachmentRule.KEEP_WORLD, False)
        off = CONFIG.get("ring_offset_cm", 0.0) if pitch == 0.0 else 0.0
        cam.set_actor_relative_location(unreal.Vector(off * math.cos(math.radians(yaw)),
                                                      off * math.sin(math.radians(yaw)), 0.0), False, False)
        cam.set_actor_relative_rotation(unreal.Rotator(0.0, pitch, yaw), False, False)
        cc = cam.get_cine_camera_component()
        fb = cc.filmback
        fb.sensor_width = CONFIG["sensor_width_mm"]
        fb.sensor_height = CONFIG["sensor_height_mm"]
        cc.filmback = fb
        cc.current_focal_length = focal
        cc.set_editor_property("current_aperture", 8.0)
        fs = cc.focus_settings
        fs.focus_method = unreal.CameraFocusMethod.DISABLE
        cc.focus_settings = fs
        cams[name] = cam
    log(f"ring: {len(cams)} cameras, focal {focal:.2f} mm for {CONFIG['hfov_deg']}° HFOV")
    return rig, cams


# ----------------------------------------------------------------------------
# 3. sequences
# ----------------------------------------------------------------------------
def pose_on_route(spline, d, lane_offset_cm=0.0, height_cm=0.0, face_backward=False):
    """World transform at distance d along the lane spline, offset sideways."""
    total = spline.get_spline_length()
    d = max(0.0, min(d, total))
    loc = spline.get_location_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD)
    rot = spline.get_rotation_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD)
    right = spline.get_right_vector_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD)
    loc = unreal.Vector(loc.x + right.x * lane_offset_cm,
                        loc.y + right.y * lane_offset_cm,
                        loc.z + right.z * lane_offset_cm + height_cm)
    if face_backward:
        rot = unreal.Rotator(rot.roll, rot.pitch, rot.yaw + 180.0)
    return loc, rot


def sample_route(spline, fps, duration_s, speed_mps):
    n = int(round(duration_s * fps))
    speed_cm = speed_mps * 100.0
    total = spline.get_spline_length()
    keys = []
    for f in range(n + 1):
        loc, rot = pose_on_route(spline, CONFIG.get("camera_start_cm", 0.0) + speed_cm * (f / fps), 0.0,
                                 15.0 + CONFIG["camera_height_cm"])
        keys.append((f, loc, rot))
    if speed_cm * duration_s > total:
        log(f"WARNING route is {total/100:.0f} m, drive needs {speed_mps*duration_s:.0f} m — clamped")
    return keys


def sample_traffic(spline, traffic, fps, duration_s):
    """Per-proxy key lists.  Parked cars get one key; movers get one per frame."""
    n = int(round(duration_s * fps))
    out = []
    for actor, off, start, spd in traffic:
        keys = []
        frames = [0] if spd == 0.0 else range(n + 1)
        for f in frames:
            d = start + spd * 100.0 * (f / fps)
            if spd != 0.0:      # movers are placed relative to the camera's start
                d += CONFIG.get("camera_start_cm", 0.0)
            wob = WOBBLE.get(actor.get_actor_label())
            if wob:
                d += wob[0] * math.sin(2 * math.pi * (f / fps) / wob[1])
            loc, rot = pose_on_route(spline, d, off, CONFIG.get("proxy_ground_cm", 15.0) + CAR_CLEAR + CAR_BODY_H / 2.0,
                                     face_backward=(spd < 0))
            if spd != 0.0 and not (0.0 <= d <= spline.get_spline_length()):
                loc = unreal.Vector(loc.x, loc.y, loc.z - 10000.0)   # off the route: hide underground, don't pile up at its ends
            keys.append((f, loc, rot))
        out.append((actor, keys))
    return out


def key_transform(seq, actor, keys, last):
    b = seq.add_possessable(actor)
    tr = b.add_track(unreal.MovieScene3DTransformTrack)
    sec = tr.add_section()
    sec.set_range(0, last + 1)
    # channel names carry a numeric suffix in 5.8 ("Location.X_342") — match on the prefix
    ch = {}
    for c in sec.get_all_channels():
        n = c.get_name()
        ch[n.rsplit("_", 1)[0] if "_" in n else n] = c
    order = ["Location.X", "Location.Y", "Location.Z", "Rotation.X", "Rotation.Y", "Rotation.Z"]
    # unkeyed Scale channels evaluate to 1.0 at render time and would override the actor's
    # scale (proxies rendered as 1 m cubes) — key the actor's own scale once
    sc = actor.get_actor_scale3d()
    for key, v in (("Scale.X", sc.x), ("Scale.Y", sc.y), ("Scale.Z", sc.z)):
        if key in ch:
            ch[key].add_key(unreal.FrameNumber(0), v, interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT)
    missing = [k for k in order if k not in ch]
    if missing:
        log(f"WARNING channels not found: {missing} (have {list(ch)})")
    for f, loc, rot in keys:
        fn = unreal.FrameNumber(f)
        vals = [loc.x, loc.y, loc.z, rot.roll, rot.pitch, rot.yaw]
        for key, v in zip(order, vals):
            if key in ch:
                ch[key].add_key(fn, v, interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    return b


def make_sequence(name, rig, cam, keys, traffic_keys, fps):
    path = f"{CONFIG['content_root']}/{name}"
    if EAL.does_asset_exist(path):
        # reuse in place: deleting fails while the MRQ queue / editor hold references
        seq = unreal.load_asset(path)
        for b in list(seq.get_bindings()):
            b.remove()
        for t in list(seq.get_tracks()):
            seq.remove_track(t)
    else:
        seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, CONFIG["content_root"], unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(fps, 1))
    last = keys[-1][0]
    seq.set_playback_start(0)
    seq.set_playback_end(last + 1)

    key_transform(seq, rig, keys, last)
    for actor, tkeys in traffic_keys:
        key_transform(seq, actor, tkeys, last)

    # camera cut
    cam_b = seq.add_possessable(cam)
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
    cut_sec = cut.add_section()
    cut_sec.set_range(0, last + 1)
    cut_sec.set_camera_binding_id(unreal.MovieSceneSequenceExtensions.get_binding_id(seq, cam_b))
    EAL.save_loaded_asset(seq)
    return seq


# ----------------------------------------------------------------------------
# 4. MRQ preset + jobs
# ----------------------------------------------------------------------------
def make_mrq_preset():
    name = "MRQ_Plates"
    path = f"{CONFIG['content_root']}/{name}"
    if EAL.does_asset_exist(path):
        preset = EAL.load_asset(path)
    else:
        preset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, CONFIG["content_root"], unreal.MoviePipelinePrimaryConfig, None)
    r = CONFIG["render"]

    out = preset.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    out.output_resolution = unreal.IntPoint(r["width"], r["height"])
    out.output_directory = unreal.DirectoryPath(r["output_dir"])
    out.file_name_format = r["file_name_format"]
    out.zero_pad_frame_numbers = 6
    out.output_frame_rate = unreal.FrameRate(24000, 1001)
    out.use_custom_frame_rate = True

    exr = preset.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR)
    exr.compression = unreal.EXRCompressionFormat.PIZ
    exr.multilayer = True

    deferred = preset.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    mats = []
    for mp in ["/MovieRenderPipeline/Materials/MovieRenderQueue_WorldDepth",
               "/MovieRenderPipeline/Materials/MovieRenderQueue_WorldNormal",
               "/MovieRenderPipeline/Materials/MovieRenderQueue_MotionVectors"]:
        m = unreal.load_asset(mp)
        if m:
            e = unreal.MoviePipelinePostProcessPass()
            e.enabled = True
            e.material = m
            mats.append(e)
        else:
            log(f"WARNING post-process material missing: {mp}")
    deferred.additional_post_process_materials = mats
    deferred.disable_multisample_effects = True

    aa = preset.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.spatial_sample_count = r["spatial_samples"]
    aa.temporal_sample_count = r["temporal_samples"]
    aa.override_anti_aliasing = True
    aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_TSR

    cs = preset.find_or_add_setting_by_class(unreal.MoviePipelineColorSetting)
    cs.disable_tone_curve = True   # scene-linear out; grade in conform

    EAL.save_loaded_asset(preset)
    return preset


def queue_jobs(sequences, preset):
    qs = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = qs.get_queue()
    q.delete_all_jobs()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    map_path = unreal.SoftObjectPath(world.get_path_name())
    for seq in sequences:
        job = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
        job.sequence = unreal.SoftObjectPath(seq.get_path_name())
        job.map = map_path
        job.job_name = seq.get_name()
        job.set_configuration(preset)
    log(f"queued {len(sequences)} MRQ jobs — open Window > Cinematics > Movie Render Queue and press Render (Local)")


# ----------------------------------------------------------------------------
def main():
    ensure_folder(CONFIG["content_root"])
    unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).get_queue().delete_all_jobs()
    route = ensure_route()
    spline = route_spline(route)
    if CONFIG.get("build_placeholder_world", True):
        ensure_world()
    rig, cams = ensure_rig()
    traffic = ensure_traffic()
    keys = sample_route(spline, CONFIG["fps"], CONFIG["duration_s"], CONFIG["speed_mps"])
    tkeys = sample_traffic(spline, traffic, CONFIG["fps"], CONFIG["duration_s"])
    seqs = []
    for name, _, _ in camera_specs():
        seqs.append(make_sequence(f"SEQ_PlateRing_{name}", rig, cams[name], keys, tkeys, CONFIG["fps"]))
    preset = make_mrq_preset()
    queue_jobs(seqs, preset)
    ELL.save_current_level()
    log("done")


if __name__ == "__main__":
    main()
