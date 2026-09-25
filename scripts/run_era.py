"""30 s windowed Wan 2.2 Fun-VACE run for one era on the Cesium depth PNGs.
Each window = N frames; the first OV frames are the previous window's last OV output frames,
kept via control_masks (0 = keep), so windows continue instead of popping. Then crossfade + mp4.
usage: python run_era.py <1955|1980s> [seconds=30] [N=49] [OV=8] [cam=C1] [start_frame=0] [geo=v4]"""
import sys, os, json, glob, time, shutil, subprocess, urllib.request
import numpy as np
from PIL import Image
sys.argv += []  # noqa
ERA = sys.argv[1]; SECS = float(sys.argv[2]) if len(sys.argv) > 2 else 30
N = int(sys.argv[3]) if len(sys.argv) > 3 else 49; OV = int(sys.argv[4]) if len(sys.argv) > 4 else 8
CAM = sys.argv[5] if len(sys.argv) > 5 else "C1"; START = int(sys.argv[6]) if len(sys.argv) > 6 else 0
GEO = sys.argv[7] if len(sys.argv) > 7 else "v4"
ROOT = os.environ.get("ORBITAL_ROOT", os.path.expanduser("~/Documents/OrbitalPlates")).replace("\\", "/")
SH = os.environ.get("COMFY_DIR", "C:/ComfyUI")   # Comfy input/output root (old desktop: Comfy-Desktop\ComfyUI-Shared)
_dd = f"{ROOT}/renders/Cesium_{CAM}_{GEO}_png"   # e.g. Cesium_C5_v7_png; falls back to the unversioned folder
DEPTH = sorted(glob.glob(f"{_dd if os.path.isdir(_dd) else f'{ROOT}/renders/Cesium_{CAM}_png'}/depth_*.png"))[START:]
TOTAL = min(int(SECS * 24) + 1, len(DEPTH)); STEP = N - OV
sys.argv = ["x", ERA, str(N), "0.8", "1955" if ERA == "1955" else "1980", "--noref", f"--cam={CAM}"]
_E, _N, _C = ERA, N, CAM
exec(open(f"{ROOT}/scripts/make_still_graph.py").read().split("out = f\"")[0])   # builds g (still graph)
ERA, N, CAM = _E, _N, _C
RUN = f"run/{ERA}_{CAM}_{time.strftime('%m%d_%H%M')}"; LOG = f"{ROOT}/renders/{RUN.replace('/', '_')}.log"
def log(s):
    open(LOG, "a").write(s + "\n"); print(s, flush=True)
def api(path, data=None):
    req = urllib.request.Request("http://127.0.0.1:8188" + path, json.dumps(data).encode() if data else None,
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))
os.makedirs(os.path.dirname(LOG), exist_ok=True)

# ---- v2 stabilisers (docs/ISSUES.md P1/P2/P3/P8/P9), off unless asked for ----------------------------------
# PLATES_SKYLOCK=1   sky pixels (depth ~ black = infinitely far) keep the value they had the first time they were
#                    seen; on a straight road the sky is fixed on screen, so this removes sky flicker and stitch seams.
# PLATES_COLORMATCH=1 every window's non-sky colour statistics are matched to window 0 before it seeds the next
#                    window, so saturation/contrast can't compound from window to window.
SKYLOCK = os.environ.get("PLATES_SKYLOCK") == "1"
COLORMATCH = os.environ.get("PLATES_COLORMATCH") == "1"
VARIANT = os.environ.get("PLATES_VARIANT", "")
SKY_T = 6                                  # depth PNG value at or below which a pixel is sky
sky_plate = np.zeros((480, 832, 3), np.float32); sky_seen = np.zeros((480, 832), bool)
ref_stats = None


def _sky_mask(di):
    d = np.asarray(Image.open(DEPTH[di]).convert("L"), np.float32)
    m = (d <= SKY_T).astype(np.float32)
    # erode 1 px then feather 2 px so building/palm edges never pick up frozen sky
    from PIL import ImageFilter
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(2))
    return np.asarray(mi, np.float32) / 255.0


def lock(img, di):
    global ref_stats
    a = np.asarray(img, np.float32)
    m = _sky_mask(di)
    ground = m < 0.5
    if COLORMATCH and ground.sum() > 1000:
        mu, sd = a[ground].mean(0), a[ground].std(0) + 1e-3
        if ref_stats is None:
            ref_stats = (mu, sd)
        else:
            a = np.where(ground[..., None], (a - mu) / sd * ref_stats[1] + ref_stats[0], a)
    if SKYLOCK:
        new = (m > 0.99) & ~sky_seen
        sky_plate[new] = a[new]; sky_seen[new] = True
        k = (m * sky_seen)[..., None]
        a = a * (1 - k) + sky_plate * k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
out_frames, s, w = [], 0, 0
while s < TOTAL - OV or w == 0:
    idx = [min(s + i, len(DEPTH) - 1) for i in range(N)]
    cdir, mdir = f"{SH}/input/{RUN}/w{w:02d}/ctrl", f"{SH}/input/{RUN}/w{w:02d}/mask"
    os.makedirs(cdir, exist_ok=True); os.makedirs(mdir, exist_ok=True)
    for i, di in enumerate(idx):
        keep = w > 0 and i < OV
        img = out_frames[-OV + i] if keep else Image.open(DEPTH[di]).convert("RGB")
        img.save(f"{cdir}/{i:04d}.png")
        Image.new("RGB", (832, 480), (0, 0, 0) if keep else (255, 255, 255)).save(f"{mdir}/{i:04d}.png")
    G = json.loads(json.dumps(g))
    G["1"] = {"class_type": "VHS_LoadImagesPath", "inputs": {"directory": cdir, "image_load_cap": N, "skip_first_images": 0, "select_every_nth": 1}}
    G["20"] = {"class_type": "VHS_LoadImagesPath", "inputs": {"directory": mdir, "image_load_cap": N, "skip_first_images": 0, "select_every_nth": 1}}
    G["21"] = {"class_type": "ImageToMask", "inputs": {"image": ["20", 0], "channel": "red"}}
    G["11"]["inputs"]["control_masks"] = ["21", 0]
    G["17"] = {"class_type": "SaveImage", "inputs": {"images": ["15", 0], "filename_prefix": f"{RUN}/w{w:02d}/f"}}
    del G["16"]; del G["18"]
    pid = api("/prompt", {"prompt": G})["prompt_id"]; t0 = time.time()
    while True:
        time.sleep(15); h = api(f"/history/{pid}")
        if pid in h: break
    st = h[pid]["status"]["status_str"]
    if st != "success":
        log(f"window {w} FAILED: {str(h[pid]['status'])[-800:]}"); sys.exit(1)
    frames = [Image.open(f).convert("RGB") for f in sorted(glob.glob(f"{SH}/output/{RUN}/w{w:02d}/f_*.png"))]
    frames = [lock(fr, idx[i]) for i, fr in enumerate(frames)] if (SKYLOCK or COLORMATCH) else frames
    if w == 0:
        out_frames += frames
    else:   # crossfade the overlap with the previous window's tail
        for i in range(OV):
            a = (i + 1) / (OV + 1)
            out_frames[-OV + i] = Image.blend(out_frames[-OV + i], frames[i], a)
        out_frames += frames[OV:]
    log(f"window {w} done in {time.time()-t0:.0f}s, frames {s}-{s+N-1}, total out {len(out_frames)}")
    s += STEP; w += 1
out_frames = out_frames[:TOTAL]
fdir = f"{ROOT}/renders/{RUN.replace('/', '_')}_frames"; os.makedirs(fdir, exist_ok=True)
for i, f in enumerate(out_frames): f.save(f"{fdir}/{i:06d}.png")
ff = shutil.which("ffmpeg") or glob.glob(os.path.expanduser("~/AppData/Local/Microsoft/WinGet/Packages/*/*/bin/ffmpeg.exe"))[0]
mp4 = f"{ROOT}/deliverables/{ERA}_{CAM}_cesium_{GEO}_{int(SECS)}s{VARIANT}.mp4"; os.makedirs(os.path.dirname(mp4), exist_ok=True)
subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", "24000/1001", "-i", f"{fdir}/%06d.png",
                "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "14", mp4], check=True)
log(f"DONE {mp4} ({len(out_frames)} frames)")
