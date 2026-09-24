"""
cesium_route_level.py  —  Orbital Plates · real-route geometry test (Cesium for Unreal 2.29)

Builds /Game/OrbitalPlates/Cesium/PlatesCesium: a georeferenced level on the real route with
Cesium World Terrain + Cesium OSM Buildings (clean footprints/heights, ODbL — commercial OK
with OpenStreetMap credit). Google Photorealistic 3D Tiles are added HIDDEN, for layout
reference in the editor only — never render them (Google ToS: no offline use / extraction,
on-screen attribution required).

Needs a Cesium ion token: Cesium panel > Connect to Cesium ion (Danny signs in).

Cesium's local frame at the georeference origin is +X east, +Y south, +Z up — so with the
origin on our lane at the start of the route and the route running east, the v9 rig's straight
+X spline already lies along the street. ROUTE["heading_deg"] rotates the rig if the street
isn't due east. Then run orbital_plates_rig.py with build_placeholder_world = False.
"""
import unreal

ROUTE = {
    # Sunset Blvd, Hollywood, EASTBOUND from La Brea Ave toward Gower St (~2.0 km, near-straight).
    # Default pick — confirm with Danny. Coordinates are approximate: verify against the hidden
    # Google tiles and nudge so the origin sits on the centre of the outer through-lane.
    "name": "Sunset_LaBrea_to_Gower_EB",
    "origin_lat": 34.09820,
    "origin_lon": -118.34410,
    "origin_height_m": 115.0,      # rough ground height; the rig spline is re-seated on terrain later
    "heading_deg": 0.0,            # 0 = due east along +X
}
ION = {"terrain": 1, "osm_buildings": 96188, "google_3d": 2275207}
LEVEL = "/Game/OrbitalPlates/Cesium/PlatesCesium"

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary


def log(m):
    unreal.log(f"[OrbitalPlates/Cesium] {m}")


def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def spawn(cls, label):
    a = find(label)
    if not a:
        a = EAS.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0))
        a.set_actor_label(label)
    return a


def ensure_level():
    if not EAL.does_directory_exist("/Game/OrbitalPlates/Cesium"):
        EAL.make_directory("/Game/OrbitalPlates/Cesium")
    if EAL.does_asset_exist(LEVEL):
        LES.load_level(LEVEL)
    else:
        LES.new_level(LEVEL)
    log(f"level {LEVEL}")


def tileset(label, asset_id, hidden=False):
    t = spawn(unreal.Cesium3DTileset, label)
    t.set_editor_property("tileset_source", unreal.TilesetSource.FROM_CESIUM_ION)
    t.set_editor_property("ion_asset_id", asset_id)
    t.set_editor_property("create_physics_meshes", True)   # needed to trace the road surface
    t.set_actor_hidden_in_game(hidden)                      # hidden in renders (MRQ = game view)
    t.set_is_temporarily_hidden_in_editor(False)
    return t


def main():
    ensure_level()
    geo = spawn(unreal.CesiumGeoreference, "CesiumGeoreference")
    geo.set_editor_property("origin_latitude", ROUTE["origin_lat"])
    geo.set_editor_property("origin_longitude", ROUTE["origin_lon"])
    geo.set_editor_property("origin_height", ROUTE["origin_height_m"])
    spawn(unreal.CesiumSunSky, "CesiumSunSky")
    tileset("Cesium_WorldTerrain", ION["terrain"])
    tileset("Cesium_OSMBuildings", ION["osm_buildings"])
    tileset("Google3D_ReferenceOnly_DONOTRENDER", ION["google_3d"], hidden=True)
    LES.save_current_level()
    log("done — georeferenced route level with terrain + OSM buildings (+ hidden Google reference)")


if __name__ == "__main__":
    main()
