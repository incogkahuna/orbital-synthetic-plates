"""SeedVR2 video restore + upscale for a finished plate (Comfy's native SeedVR2 nodes).
Graph: comfy_workflows/seedvr2_video_upscale_api.json, exported from Comfy's
`utility_seedvr2_3b_int8_upscale_video` template, run here with the 7B fp16 model.
usage: python upscale_plate.py <plate.mp4> [x=2] [model=7b|7b_sharp] [color=lab|wavelet|adain|none] [overlap=2]
Writes <plate>_seedvr2_<model>_x<x>.mp4 next to the input."""
import sys, os, json, time, glob, shutil, urllib.request

src = os.path.abspath(sys.argv[1])
X = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
MODEL = sys.argv[3] if len(sys.argv) > 3 else "7b"
COLOR = sys.argv[4] if len(sys.argv) > 4 else "lab"
OVERLAP = int(sys.argv[5]) if len(sys.argv) > 5 else 2
COMFY = os.environ.get("COMFY_DIR", "C:/ComfyUI")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def api(path, data=None):
    req = urllib.request.Request("http://127.0.0.1:8188" + path, json.dumps(data).encode() if data else None,
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


name = os.path.splitext(os.path.basename(src))[0]
tag = f"seedvr2_{MODEL}_x{X:g}"
os.makedirs(f"{COMFY}/input/plates_in", exist_ok=True)
shutil.copy(src, f"{COMFY}/input/plates_in/{name}.mp4")

g = json.load(open(f"{ROOT}/comfy_workflows/seedvr2_video_upscale_api.json"))
g["73"]["inputs"]["file"] = f"plates_in/{name}.mp4"
g["66:52"]["inputs"]["unet_name"] = f"seedvr2_{MODEL}_fp16.safetensors"
g["66:57"]["inputs"]["resize_type.multiplier"] = X
g["66:59"]["inputs"]["color_correction_method"] = COLOR
g["66:105"]["inputs"]["value"] = True                       # temporal chunking on: long plates don't fit in one pass
g["66:99"]["inputs"]["temporal_overlap"] = OVERLAP          # crossfade chunk joins instead of hard seams
g["76"]["inputs"]["filename_prefix"] = f"plates/upscaled/{name}_{tag}"   # format stays "auto" = MP4 / H.264

pid = api("/prompt", {"prompt": g})["prompt_id"]; t0 = time.time()
print(f"queued {pid} ({name}, {tag})", flush=True)
while True:
    time.sleep(15)
    h = api(f"/history/{pid}")
    if pid in h:
        break
st = h[pid]["status"]
if st["status_str"] != "success":
    print("FAILED", json.dumps(st)[-1500:]); sys.exit(1)
out = sorted(glob.glob(f"{COMFY}/output/plates/upscaled/{name}_{tag}*.mp4"), key=os.path.getmtime)[-1]
dst = os.path.join(os.path.dirname(src), f"{name}_{tag}.mp4")
shutil.copy(out, dst)
print(f"DONE {dst} in {time.time() - t0:.0f}s")
