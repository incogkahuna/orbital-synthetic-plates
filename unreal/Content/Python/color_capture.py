"""One-shot pitch-deck capture, COLOUR version: dusk CesiumSunSky + tinted terrain/building materials (transient, never saved).

Triggered by init_unreal.py when Saved/run_city_capture.flag exists. Hides the Google 3D Tiles
layer, frames two high obliques over the Sunset Blvd route, takes HighResShots, then writes
"done" to Saved/color_capture_status.txt. Nothing is spawned or saved; the launcher kills the editor.
Cesium georeference origin = La Brea lane start; +X east (route direction), +Y south, +Z up.
"""
import os, time, traceback, unreal

LEVEL = "/Game/OrbitalPlates/Cesium/PlatesCesium"
MARK = os.path.join(unreal.Paths.project_saved_dir(), "color_capture_status.txt")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
M = 100.0
VIEWS = [   # (eye, look-at), cm
    (unreal.Vector(-1500 * M, 1300 * M, 650 * M), unreal.Vector(1000 * M, -200 * M, 0)),     # low oblique, looking NE up the route to the hills
    (unreal.Vector(-900 * M, 800 * M, 380 * M), unreal.Vector(700 * M, -150 * M, 0)),        # closer oblique over the route
]
S = {"phase": "wait", "t0": time.time(), "shots": 0, "tiles": []}


def mark(s):
    open(MARK, "a").write(s + "\n"); unreal.log("[COLOR_CAPTURE] " + s)


def view(i):
    eye, at = VIEWS[i]
    UES.set_level_viewport_camera_info(eye, unreal.MathLibrary.find_look_at_rotation(eye, at))


def open_level():
    world = UES.get_editor_world()
    if not world or LEVEL not in world.get_path_name():
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    mark("level open: " + UES.get_editor_world().get_path_name())


def setup():
    S["tiles"] = []
    for t in EAS.get_all_level_actors():
        if isinstance(t, unreal.Cesium3DTileset):
            if t.get_editor_property("ion_asset_id") == 2275207:      # Google 3D Tiles: never shown
                t.set_is_temporarily_hidden_in_editor(True)
                t.set_actor_hidden_in_game(True)
                t.set_editor_property("suspend_update", True)
            else:
                S["tiles"].append(t)
                for prop, val in (("maximum_screen_space_error", 4.0), ("forbid_holes", True),
                                  ("maximum_simultaneous_tile_loads", 64), ("maximum_cached_bytes", 4 * 1024 ** 3)):
                    try:
                        t.set_editor_property(prop, val)
                    except Exception as e:
                        mark(f"{prop} not set: {e}")
    tint()
    dusk()
    try:
        unreal.EditorLevelLibrary.editor_set_game_view(True)          # hide icons/gizmos
    except Exception as e:
        mark(f"game view toggle failed: {e}")
    view(0)
    mark(f"setup ok; tilesets {[t.get_actor_label() for t in S['tiles']]}")


def make_mat(name, rgb, rough):
    parent = unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial")      # has a "Color" vector param
    mid = unreal.MaterialLibrary.create_dynamic_material_instance(UES.get_editor_world(), parent)
    mid.set_vector_parameter_value("Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return mid


def tint():
    looks = {96188: ("M_PitchBuildings", (0.62, 0.50, 0.40), 0.8),    # warm plaster
             1: ("M_PitchTerrain", (0.34, 0.30, 0.22), 0.95)}        # dry olive-tan ground
    for t in S["tiles"]:
        aid = t.get_editor_property("ion_asset_id")
        if aid in looks:
            try:
                t.set_editor_property("material", make_mat(*looks[aid]))
                t.refresh_tileset()
                mark(f"tinted {t.get_actor_label()}")
            except Exception as e:
                mark(f"tint failed on {t.get_actor_label()}: {e}")


def dusk():
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.CesiumSunSky):
            for prop, val in (("year", 2026), ("month", 9), ("day", 21), ("time_zone", -8.0),
                              ("solar_time", 18.55)):
                try:
                    a.set_editor_property(prop, val)
                except Exception as e:
                    mark(f"sunsky {prop}: {e}")
            try:
                a.update_sun()
            except Exception as e:
                mark(f"update_sun: {e}")
            mark("dusk set on " + a.get_actor_label())
            return
    mark("no CesiumSunSky found")


def loaded():
    try:
        return all(t.get_editor_property("load_progress") >= 99.0 for t in S["tiles"])
    except Exception:
        return True


def tick(dt):
    try:
        now = time.time()
        if S["phase"] == "wait" and now - S["t0"] > 60:
            open_level(); S["phase"] = "settle"; S["t1"] = now
        elif S["phase"] == "settle" and now - S["t1"] > 15:
            setup(); S["phase"] = "load"; S["t1"] = now
        elif S["phase"] == "load" and ((now - S["t1"] > 120 and loaded()) or now - S["t1"] > 300):
            view(S["shots"]); S["phase"] = "aim"; S["ta"] = now          # re-aim right before the shot
        elif S["phase"] == "aim" and now - S["ta"] > 8:
            mark(f"camera before shot: {UES.get_level_viewport_camera_info()}")
            unreal.SystemLibrary.execute_console_command(UES.get_editor_world(), "HighResShot 3840x2160")
            S["shots"] += 1; mark(f"shot {S['shots']} (loaded={loaded()})")
            S["phase"] = "post"; S["t2"] = now          # HighResShot resolves on a later frame: don't move yet
        elif S["phase"] == "post" and now - S["t2"] > 6:
            if S["shots"] < len(VIEWS):
                view(S["shots"]); mark(f"view {S['shots']} set: {UES.get_level_viewport_camera_info()}")
                S["phase"] = "load"; S["t1"] = now
            else:
                S["phase"] = "finish"; S["t3"] = now
        elif S["phase"] == "finish" and now - S["t3"] > 10:
            S["phase"] = "idle"; mark("done")
    except Exception:
        mark("ERROR " + traceback.format_exc()); S["phase"] = "idle"; mark("done")


mark("---- capture start")
S["h"] = unreal.register_slate_post_tick_callback(tick)
