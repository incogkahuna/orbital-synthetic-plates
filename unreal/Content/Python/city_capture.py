"""One-shot pitch-deck capture: wide aerials of the Cesium city build (World Terrain + OSM Buildings).

Triggered by init_unreal.py when Saved/run_city_capture.flag exists. Hides the Google 3D Tiles
layer, frames two high obliques over the Sunset Blvd route, takes HighResShots, then writes
"done" to Saved/city_capture_status.txt. Nothing is spawned or saved; the launcher kills the editor.
Cesium georeference origin = La Brea lane start; +X east (route direction), +Y south, +Z up.
"""
import os, time, traceback, unreal

LEVEL = "/Game/OrbitalPlates/Cesium/PlatesCesium"
MARK = os.path.join(unreal.Paths.project_saved_dir(), "city_capture_status.txt")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
M = 100.0
VIEWS = [   # (eye, look-at), cm
    (unreal.Vector(-1500 * M, 1300 * M, 650 * M), unreal.Vector(1000 * M, -200 * M, 0)),     # low oblique, looking NE up the route to the hills
    (unreal.Vector(-900 * M, 800 * M, 380 * M), unreal.Vector(700 * M, -150 * M, 0)),        # closer oblique over the route
]
S = {"phase": "wait", "t0": time.time(), "shots": 0, "tiles": []}


def mark(s):
    open(MARK, "a").write(s + "\n"); unreal.log("[CITY_CAPTURE] " + s)


def view(i):
    eye, at = VIEWS[i]
    UES.set_level_viewport_camera_info(eye, unreal.MathLibrary.find_look_at_rotation(eye, at))


def setup():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
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
    try:
        unreal.EditorLevelLibrary.editor_set_game_view(True)          # hide icons/gizmos
    except Exception as e:
        mark(f"game view toggle failed: {e}")
    view(0)
    mark(f"setup ok; tilesets {[t.get_actor_label() for t in S['tiles']]}")


def loaded():
    try:
        return all(t.get_editor_property("load_progress") >= 99.0 for t in S["tiles"])
    except Exception:
        return True


def tick(dt):
    try:
        now = time.time()
        if S["phase"] == "wait" and now - S["t0"] > 60:
            setup(); S["phase"] = "load"; S["t1"] = now
        elif S["phase"] == "load" and ((now - S["t1"] > 120 and loaded()) or now - S["t1"] > 300):
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
