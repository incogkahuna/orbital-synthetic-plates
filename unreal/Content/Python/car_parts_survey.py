"""Survey Fab car packs under /Game/Vehicles: bounds of every static mesh, grouped by car (SM_Car_02a..k -> Car_02).
Writes Saved/car_parts_survey.json. Dekogon ships split cars (body, wheels, extras such as taxi signs and police
light bars) with a shared pivot, so bounds are enough to tell the parts apart: see classify() in build_car_kits.py.
Run: UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=".../car_parts_survey.py" -unattended"""
import json, os, re
import unreal

out = {}
for p in unreal.EditorAssetLibrary.list_assets("/Game/Vehicles", recursive=True, include_folder=False):
    ad = unreal.EditorAssetLibrary.find_asset_data(p)
    if str(ad.asset_class_path.asset_name) != "StaticMesh":
        continue
    m = unreal.load_asset(p.split(".")[0])
    bb = m.get_bounding_box()
    name = m.get_name()
    g = re.match(r"(SM_.*?_\d+)([a-z]*)$", name)
    key = g.group(1) if g else name
    out.setdefault(key, []).append({
        "path": p.split(".")[0], "name": name, "part": g.group(2) if g else "",
        "min": [round(bb.min.x, 1), round(bb.min.y, 1), round(bb.min.z, 1)],
        "max": [round(bb.max.x, 1), round(bb.max.y, 1), round(bb.max.z, 1)],
        "tris": m.get_num_triangles(0) if hasattr(m, "get_num_triangles") else -1,
    })
dst = os.path.join(unreal.Paths.project_saved_dir(), "car_parts_survey.json")
json.dump(out, open(dst, "w"), indent=1)
unreal.log(f"[OrbitalPlates] car survey: {len(out)} groups, {sum(len(v) for v in out.values())} meshes -> {dst}")
