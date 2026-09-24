"""One-shot pitch-deck capture: the 9-camera PlateRig sitting on a camera-car proxy.

Triggered by init_unreal.py when Saved/run_rig_capture.flag exists. Loads the Cesium level,
spawns a car proxy + roof mount under PlateRig (NOT saved), frames the editor viewport,
takes two HighResShots, then writes "done" to Saved/rig_capture_status.txt.
The external launcher kills the editor after "done" so the level is never saved.
"""
import os, time, traceback, unreal

LEVEL = "/Game/OrbitalPlates/Cesium/PlatesCesium"
SAVED = unreal.Paths.project_saved_dir()
MARK = os.path.join(SAVED, "rig_capture_status.txt")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
CUBE = "/Engine/BasicShapes/Cube"
CYL = "/Engine/BasicShapes/Cylinder"
RIG_H = 150.0                                   # nodal origin above road (orbital_plates_rig.CONFIG)
CAR_L, CAR_W, BODY_H, CAB_H, CLEAR = 450.0, 180.0, 75.0, 60.0, 25.0
S = {"phase": "wait", "t0": time.time(), "shots": 0}


def mark(s):
    open(MARK, "a").write(s + "\n"); unreal.log("[RIG_CAPTURE] " + s)


def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a


def block(label, mesh, loc, rot, scale):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
    a.set_actor_label(label)
    a.static_mesh_component.set_static_mesh(unreal.load_asset(mesh))
    a.set_actor_scale3d(scale)
    return a


def setup():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    for t in EAS.get_all_level_actors():
        if isinstance(t, unreal.Cesium3DTileset):
            S.setdefault("tiles", []).append(t)
            if t.get_editor_property("ion_asset_id") == 2275207:      # Google 3D Tiles: never shown
                t.set_is_temporarily_hidden_in_editor(True)
                t.set_actor_hidden_in_game(True)
                t.set_editor_property("suspend_update", True)
    rig = find("PlateRig")
    if not rig:
        raise RuntimeError("PlateRig not found")
    p, rot = rig.get_actor_location(), rig.get_actor_rotation()
    yaw = unreal.Rotator(0.0, 0.0, rot.yaw)
    f, r = yaw.get_forward_vector(), yaw.get_right_vector()
    up = unreal.Vector(0, 0, 1)
    ground = p.z - RIG_H
    # car body + cabin (cabin sits under the rig), same proportions as the traffic proxies
    c = p + f * 40.0
    block("Pitch_CamCar_Body", CUBE, unreal.Vector(c.x, c.y, ground + CLEAR + BODY_H / 2), yaw,
          unreal.Vector(CAR_L / 100, CAR_W / 100, BODY_H / 100))
    block("Pitch_CamCar_Cabin", CUBE, unreal.Vector(p.x, p.y, ground + CLEAR + BODY_H + CAB_H / 2), yaw,
          unreal.Vector(CAR_L * 0.45 / 100, CAR_W * 0.78 / 100, CAB_H / 100))
    roof = ground + CLEAR + BODY_H + CAB_H
    # roof mount: plate + post up to the nodal centre
    block("Pitch_CamCar_Plate", CUBE, unreal.Vector(p.x, p.y, roof + 2.5), yaw, unreal.Vector(0.9, 0.9, 0.05))
    post_h = max(RIG_H - (roof - ground) - 5.0, 5.0)
    block("Pitch_CamCar_Post", CYL, unreal.Vector(p.x, p.y, roof + 5.0 + post_h / 2), yaw,
          unreal.Vector(0.08, 0.08, post_h / 100))
    S["p"], S["f"], S["r"], S["up"] = p, f, r, up
    S["views"] = [
        p - f * 520.0 + r * 380.0 + up * 260.0,       # rear three-quarter, high
        p + f * 80.0 + r * 520.0 + up * 90.0,         # side profile
    ]
    view(0)
    mark(f"setup ok; rig at {p}, yaw {rot.yaw:.1f}")


def view(i):
    eye = S["views"][i]
    look = unreal.MathLibrary.find_look_at_rotation(eye, S["p"] - S["up"] * 40.0)
    UES.set_level_viewport_camera_info(eye, look)


def loaded():
    try:
        return all(t.get_editor_property("load_progress") >= 99.0 for t in S.get("tiles", [])
                   if t.get_editor_property("ion_asset_id") != 2275207)
    except Exception:
        return True


def tick(dt):
    try:
        el = time.time() - S["t0"]
        if S["phase"] == "wait" and el > 20:
            setup(); S["phase"] = "load"; S["t1"] = time.time()
        elif S["phase"] == "load" and (time.time() - S["t1"] > 25 and loaded() or time.time() - S["t1"] > 120):
            S["phase"] = "shoot"; S["t2"] = time.time()
        elif S["phase"] == "shoot" and time.time() - S["t2"] > 6:
            unreal.SystemLibrary.execute_console_command(UES.get_editor_world(), "HighResShot 2560x1440")
            S["shots"] += 1
            mark(f"shot {S['shots']}")
            if S["shots"] < len(S["views"]):
                view(S["shots"]); S["t2"] = time.time() + 8   # let tiles refine for the new view
            else:
                S["phase"] = "finish"; S["t3"] = time.time()
        elif S["phase"] == "finish" and time.time() - S["t3"] > 8:
            S["phase"] = "idle"; mark("done")
    except Exception:
        mark("ERROR " + traceback.format_exc()); S["phase"] = "idle"; mark("done")


mark("---- capture start")
S["h"] = unreal.register_slate_post_tick_callback(tick)
