"""Cosmos 3 Nano transfer (render-to-real) on our Unreal passes. Separate venv: C:\\models\\cosmos-venv.
Controls: depth (our log-depth PNGs, white = near) and optionally edges (Canny on Unreal's beauty EXR: real car /
building outlines). Cosmos chains long clips itself in 121-frame chunks.
usage: python cosmos_transfer.py --cam C5 --geo v15 --frames 241 [--edge 0.5] [--start 0] [--steps 35] [--tag test]"""
import argparse, glob, json, os, sys, time
import numpy as np, cv2, torch

ap = argparse.ArgumentParser()
ap.add_argument("--cam", default="C5"); ap.add_argument("--geo", default="v15"); ap.add_argument("--era", default="1980s")
ap.add_argument("--frames", type=int, default=241); ap.add_argument("--start", type=int, default=0)
ap.add_argument("--edge", type=float, default=0.0, help=">0 adds an edge control (the pipeline has no per-hint weight)")
ap.add_argument("--depth", type=float, default=1.0); ap.add_argument("--steps", type=int, default=35)
ap.add_argument("--control_guidance", type=float, default=1.5); ap.add_argument("--guidance", type=float, default=3.0)
ap.add_argument("--seed", type=int, default=2026); ap.add_argument("--tag", default="test")
ap.add_argument("--offload", action="store_true")
ap.add_argument("--res", type=int, default=720, help="480 or 720 (16:9)")
ap.add_argument("--blur_from", default="", help="mp4 of a finished plate to use as a blur hint")
ap.add_argument("--blur_sigma", type=float, default=6.0, help="blur sigma in px at 832 wide")
a = ap.parse_args()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
W, H = (848, 480) if a.res == 480 else (1280, 720)   # multiples of 16
out_dir = os.path.join(ROOT, "deliverables", "cosmos"); os.makedirs(out_dir, exist_ok=True)
name = f"{a.era}_{a.cam}_{a.geo}_cosmos_{a.res}p_{a.frames}f_{a.tag}"


def log(s):
    print(time.strftime("%H:%M:%S"), s, flush=True)


# ---- controls -------------------------------------------------------------------------------------------------
dpng = sorted(glob.glob(os.path.join(ROOT, "renders", f"Cesium_{a.cam}_{a.geo}_png", "depth_*.png")))[a.start:a.start + a.frames]
if len(dpng) < a.frames:
    sys.exit(f"only {len(dpng)} depth frames")
depth = [cv2.cvtColor(cv2.resize(cv2.imread(p), (W, H), interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2RGB) for p in dpng]
controls = {"depth": depth}

if a.edge > 0:
    import OpenEXR, Imath
    exr = sorted(glob.glob(os.path.join(ROOT, "unreal", "Saved", "PlateRenders", "Cesium", f"SEQ_PlateRing_{a.cam}", "*.exr")))
    exr = exr[a.start:a.start + a.frames]
    FL = Imath.PixelType(Imath.PixelType.FLOAT); edges = []
    for p in exr:
        f = OpenEXR.InputFile(p); dw = f.header()["dataWindow"]; w, h = dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1
        rgb = np.stack([np.frombuffer(f.channel(c, FL), np.float32).reshape(h, w) for c in "RGB"], -1)
        t = np.clip((rgb / (1 + rgb)) ** (1 / 2.2) * 255, 0, 255).astype(np.uint8)
        g = cv2.cvtColor(cv2.resize(t, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
        e = cv2.Canny(cv2.GaussianBlur(g, (3, 3), 0), 60, 140)
        edges.append(np.repeat(e[..., None], 3, -1))
    controls["edge"] = edges
    log(f"edges from {len(edges)} beauty EXRs")

if a.blur_from:
    # "blur" hint from a finished Wan plate: Cosmos takes colour and layout from it and rebuilds the fine detail
    # itself, so Wan's invented palms/storefronts carry over while its seams and flicker (fine detail) do not.
    cap = cv2.VideoCapture(a.blur_from); frames = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, a.start)
    while len(frames) < a.frames:
        ok, fr = cap.read()
        if not ok:
            break
        fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
        fr = cv2.GaussianBlur(fr, (0, 0), a.blur_sigma * W / 832)
        frames.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    if len(frames) < a.frames:
        sys.exit(f"blur source has only {len(frames)} frames")
    controls["blur"] = frames
    log(f"blur hint from {os.path.basename(a.blur_from)}, sigma {a.blur_sigma}")

from PIL import Image
controls = {k: [Image.fromarray(x) for x in v] for k, v in controls.items()}
# preview of the controls actually fed in
prev = [np.asarray(controls[k][0]) for k in controls]
cv2.imwrite(os.path.join(out_dir, name + "_controls.png"), cv2.cvtColor(np.concatenate(prev, 1), cv2.COLOR_RGB2BGR))

# ---- model ----------------------------------------------------------------------------------------------------
from diffusers import Cosmos3OmniModularPipeline
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
from diffusers.utils import export_to_video

t0 = time.time()
pipe = Cosmos3OmniModularPipeline.from_pretrained(r"C:\models\Cosmos3-Nano", dtype=torch.bfloat16)
pipe.load_components(dtype=torch.bfloat16)
if a.offload:
    pipe.enable_model_cpu_offload()
else:
    pipe.to("cuda")
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=10.0, use_karras_sigmas=False)
log(f"loaded in {time.time() - t0:.0f}s, VRAM {torch.cuda.memory_allocated() / 1e9:.1f} GB")

prompt = json.load(open(os.path.join(os.path.dirname(__file__), f"prompt_{a.era}_{a.cam}.json")))
neg = json.load(open(r"C:\models\cosmos-assets\negative_prompt.json"))
kw = dict(prompt=json.dumps(prompt), negative_prompt=json.dumps(neg), control_videos=controls, num_frames=a.frames,
          height=H, width=W, fps=30.0, num_inference_steps=a.steps, guidance_scale=a.guidance,
          control_guidance=a.control_guidance, output="videos", generator=torch.Generator("cuda").manual_seed(a.seed))
pipe.disable_safety_checker()          # content-filter guardrail (supported opt-out); our own street renders
t0 = time.time()
videos = pipe(**kw)
log(f"generated {a.frames} frames in {time.time() - t0:.0f}s, peak VRAM {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")
vid = videos[0] if isinstance(videos, (list, tuple)) and not hasattr(videos[0], "size") else videos
# our plates play at 23.976: the depth frames are 24 fps samples, so encode at 24000/1001 to keep real speed
mp4 = os.path.join(out_dir, name + ".mp4")
export_to_video(vid, mp4, fps=24000 / 1001, macro_block_size=1)
log(f"DONE {mp4}")
