"""Point the level's DEFAULT Cesium georeference (the one the tilesets use) at the route start,
and remove any extra georeference actors. Sunset & La Brea, eastbound lane."""
import unreal

LON, LAT, H = -118.3441, 34.0982, 80.0   # H = rough WGS84 ellipsoid height of the road (MSL ~115 m, geoid ~-35 m)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
default = unreal.CesiumGeoreference.get_default_georeference(world)
default.set_origin_longitude_latitude_height(unreal.Vector(LON, LAT, H))
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.CesiumGeoreference) and a != default:
        EAS.destroy_actor(a)
default.set_actor_label("CesiumGeoreference")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.log(f"[OrbitalPlates/Cesium] origin set on {default.get_name()}: {LAT}, {LON}, {H} m")
