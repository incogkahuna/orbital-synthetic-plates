"""LTX-2.3 + fal 3DREAL IC-LoRA (render-to-real) through ComfyUI. Mirrors Comfy's video_ltx2_3_ic_lora template,
with Kijai's split LTX-2.3 files (UNet fp8 + video VAE + audio VAE + text projection) and Gemma 3 12B fp8.
The source clip is the in-context guide; 3DREAL keeps its layout and camera and makes it photoreal.
usage: python ltx_3dreal.py <source.mp4> [--lora strong|light|strong-v2] [--frames 121] [--start 0]
                            [--w 1280 --h 704] [--strength 1.0] [--seed 42] [--tag x] [--prompt_file p.txt]"""
import argparse, glob, json, os, shutil, sys, time, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("source"); ap.add_argument("--lora", default="strong", choices=["strong", "light", "strong-v2"])
ap.add_argument("--frames", type=int, default=121); ap.add_argument("--start", type=int, default=0)
ap.add_argument("--w", type=int, default=1280); ap.add_argument("--h", type=int, default=704)
ap.add_argument("--strength", type=float, default=1.0); ap.add_argument("--guide_strength", type=float, default=1.0)
ap.add_argument("--seed", type=int, default=42); ap.add_argument("--steps", type=int, default=8)
ap.add_argument("--tag", default=""); ap.add_argument("--prompt_file", default="")
ap.add_argument("--context", type=int, default=0, help=">0: LTXVContextWindows length in frames for long clips")
a = ap.parse_args()
assert (a.frames - 1) % 8 == 0, "LTX needs 8n+1 frames"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROMPT = open(a.prompt_file).read().strip() if a.prompt_file else (
    "3DREAL. Make it photorealistic. Real footage filmed through the rear window of a car driving along Sunset "
    "Boulevard in Hollywood, Los Angeles, in 1982, at dusk just after sunset. The road recedes behind us toward an "
    "orange horizon under a violet sky. Real early-1980s American cars with chrome bumpers and headlights on follow "
    "us; parked cars line both kerbs, dark and unlit. Tall Mexican fan palms line the sidewalks. Low commercial "
    "buildings with lit shop windows, painted and neon signs, awnings and street lamps glowing. Natural true-to-life "
    "colour and exposure, clean modern digital cinema camera, sharp, steady camera, no film grain, no colour grade.")
NEG = ("blurry, out of focus, low detail, CGI, 3D render, video game, cartoon, plastic, film grain, vintage filter, "
       "colour grading, oversaturated, flicker, camera shake, warping, morphing cars, distorted, watermark, text, "
       "smoke, clouds of smoke, fog, haze blobs, cartoon storefronts")


def api(path, data=None):
    req = urllib.request.Request("http://127.0.0.1:8188" + path, json.dumps(data).encode() if data else None,
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


# copy the source into Comfy's input folder (VHS_LoadVideo reads from there)
src_name = f"3dreal_src_{os.path.splitext(os.path.basename(a.source))[0]}.mp4"
shutil.copy(a.source, os.path.join(r"C:\ComfyUI\input", src_name))
LORA = {"strong": "3DREAL-strong.safetensors", "light": "3DREAL-light.safetensors", "strong-v2": "3DREAL-strong-v2.safetensors"}[a.lora]
FPS = 24
prefix = f"ltx3dreal/{os.path.splitext(os.path.basename(a.source))[0]}_{a.lora}{('_' + a.tag) if a.tag else ''}"

g = {
    "1": {"class_type": "VHS_LoadVideo", "inputs": {"video": src_name, "force_rate": 0, "custom_width": a.w, "custom_height": a.h,
          "frame_load_cap": a.frames, "skip_first_frames": a.start, "select_every_nth": 1}},
    "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled.safetensors", "weight_dtype": "default"}},
    "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": LORA, "strength_model": a.strength}},
    "4": {"class_type": "GetICLoRAParameters", "inputs": {"iclora_model": ["3", 0]}},
    "5": {"class_type": "VAELoader", "inputs": {"vae_name": "LTX23_video_vae_bf16.safetensors"}},
    "6": {"class_type": "LTXVAudioVAELoader", "inputs": {"ckpt_name": "LTX23_audio_vae_bf16.safetensors"}},
    "7": {"class_type": "LTXAVTextEncoderLoader", "inputs": {"text_encoder": "gemma_3_12B_it_fp8_scaled.safetensors",
          "ckpt_name": "ltx-2.3_text_projection_bf16.safetensors", "device": "default"}},
    "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": PROMPT}},
    "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": NEG}},
    "10": {"class_type": "LTXVConditioning", "inputs": {"positive": ["8", 0], "negative": ["9", 0], "frame_rate": FPS}},
    "11": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": a.w, "height": a.h, "length": a.frames, "batch_size": 1}},
    "12": {"class_type": "LTXVAddGuide", "inputs": {"positive": ["10", 0], "negative": ["10", 1], "vae": ["5", 0], "latent": ["11", 0],
           "image": ["1", 0], "frame_idx": 0, "strength": a.guide_strength, "iclora_parameters": ["4", 0]}},
    "13": {"class_type": "LTXVEmptyLatentAudio", "inputs": {"frames_number": a.frames, "frame_rate": FPS, "batch_size": 1, "audio_vae": ["6", 0]}},
    "14": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["12", 2], "audio_latent": ["13", 0]}},
    "15": {"class_type": "KSampler", "inputs": {"model": ["3", 0], "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["14", 0],
           "seed": a.seed, "steps": a.steps, "cfg": 1.0, "sampler_name": "euler_ancestral", "scheduler": "linear_quadratic", "denoise": 1.0}},
    "16": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["15", 0]}},
    "17": {"class_type": "LTXVCropGuides", "inputs": {"positive": ["12", 0], "negative": ["12", 1], "latent": ["16", 0]}},
    "18": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["17", 2], "vae": ["5", 0], "tile_size": 768, "overlap": 64,
           "temporal_size": 4096, "temporal_overlap": 64}},
    "19": {"class_type": "VHS_VideoCombine", "inputs": {"images": ["18", 0], "frame_rate": 23.976, "loop_count": 0,
           "filename_prefix": prefix, "format": "video/h264-mp4", "pix_fmt": "yuv420p", "crf": 14, "save_metadata": False,
           "pingpong": False, "save_output": True}},
}
if a.context:
    g["20"] = {"class_type": "LTXVContextWindows", "inputs": {"model": ["3", 0], "context_length": a.context, "context_overlap": 24,
               "context_schedule": "standard_static", "context_stride": 1, "closed_loop": False, "fuse_method": "pyramid",
               "freenoise": True, "retain_first_frame": False, "split_conds_to_windows": True}}
    g["15"]["inputs"]["model"] = ["20", 0]

t0 = time.time()
r = api("/prompt", {"prompt": g})
if r.get("node_errors"):
    sys.exit("node errors: " + json.dumps(r["node_errors"])[:1500])
pid = r["prompt_id"]; print(time.strftime("%H:%M:%S"), "queued", pid, LORA, f"{a.frames}f {a.w}x{a.h}", flush=True)
while True:
    time.sleep(10); h = api(f"/history/{pid}")
    if pid in h:
        break
st = h[pid]["status"]
if st["status_str"] != "success":
    sys.exit("FAILED: " + json.dumps(st)[-1500:])
outs = [f for o in h[pid]["outputs"].values() for f in o.get("gifs", [])]
dst_dir = os.path.join(ROOT, "deliverables", "ltx3dreal"); os.makedirs(dst_dir, exist_ok=True)
for f in outs:
    p = os.path.join(r"C:\ComfyUI\output", f.get("subfolder", ""), f["filename"])
    if p.endswith(".mp4"):
        d = os.path.join(dst_dir, os.path.basename(p)); shutil.copy(p, d)
        print(time.strftime("%H:%M:%S"), f"DONE in {time.time() - t0:.0f}s -> {d}", flush=True)
