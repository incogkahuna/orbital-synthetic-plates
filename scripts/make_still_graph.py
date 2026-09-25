"""Build + submit a Wan 2.2 Fun-VACE 14B two-stage depth->era still (API format).
usage: python make_still_graph.py <era 1955|1980s> [frames] [depth_strength] [seed] [--submit]"""
import json, os, sys, urllib.request
era = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 33
STR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 1234
NOREF = "--noref" in sys.argv
CAM = next((a.split("=",1)[1] for a in sys.argv if a.startswith("--cam=")), "C1")
SKIP = int(next((a.split("=",1)[1] for a in sys.argv if a.startswith("--skip=")), "0"))
VID = next((a.split("=",1)[1] for a in sys.argv if a.startswith("--video=")), "depth_C1.mp4")
SRC = __import__("re").sub(r"depth_C\d_","",VID).replace(".mp4","") if "cesium" in VID else "box"
PREC = "bf16" if ("--bf16" in sys.argv or os.environ.get("PLATES_BF16") == "1") else "fp8_scaled"   # bf16: Ampere has no fp8 math
TAG = CAM + "_" + SRC + f"_s{STR}" + ("_noref" if NOREF else "_ref") + ("_bf16" if PREC == "bf16" else "")
LANE = ("positioned in the RIGHT-HAND lane of a two-way city street, the painted centre line runs up the left third "
        "of the frame, a car ahead in the same lane, oncoming traffic on the far side of the centre line, cars parked "
        "at the kerb to the right, storefronts and sidewalks on both sides, the bottom edge of the frame is clean "
        "asphalt of our lane, viewpoint at the driver's eye level, 1.5 m above the road, looking straight ahead")
CAMTXT = {
 "C1": LANE,
 "C5": ("view looking straight BACKWARD out of the rear of a car driving in the right-hand lane of a two-way city street, "
        "the road recedes behind us to the vanishing point, a car following close behind us in our lane with its headlights "
        "facing the camera, more following cars further back, the painted centre line runs up the RIGHT third of the frame, "
        "traffic on the far side of the centre line driving away from us, a few cars parked at the kerb on the LEFT facing toward us so we "
        "see their front grilles and headlights, never their tail lights, moderate evening traffic, storefronts and "
        "sidewalks on both sides, the bottom edge of the frame is clean asphalt, viewpoint at the driver's eye level, 1.5 m above the road"),
 "C3": ("side view looking straight out to the RIGHT of a car driving along a city boulevard, parked cars at the kerb close in "
        "the foreground seen side-on, the sidewalk with pedestrians, storefronts, shop windows and signs facing the camera, "
        "motion from the side, moderate evening traffic, a handful of cars spread out at different distances along the street, "
        "viewpoint at the driver's eye level, 1.5 m above the road, level horizon"),
 "C7": ("side view looking straight out to the LEFT of a car driving in the right-hand lane of a city boulevard, the adjacent "
        "lane close in the foreground with a car passing us seen side-on, the centre line and oncoming lanes beyond with "
        "moderate evening traffic, a handful of cars spread out at different distances, the far "
        "sidewalk and storefronts across the street, viewpoint at the driver's eye level, 1.5 m above the road, level horizon"),
}
# Plates are captured "as life looks": the era comes only from content (cars, signs, clothes), never from a
# film look. Grading and filtering happen on set through the lens (Danny, 2026-09-23).
NEUTRAL = ("photoreal footage from a clean modern digital cinema camera, neutral natural colour, true-to-life exposure "
           "and white balance, sharp, no film grain, no colour grade, ")
ERA = {
 "1955": (NEUTRAL + "Los Angeles in 1955, a boulevard at dusk, magic hour, warm glowing sky, street lamps and neon signs switched on, the street lamps cast soft pools of light on the road, moving cars have their headlights on, parked cars are dark and unlit, 1940s and 1950s American cars "
          "with chrome bumpers and rounded fenders, neon and painted shop signs, leafy street trees and palm trees along the sidewalks, telephone poles, pedestrians in 1950s clothes, "
          "realistic detail, ", "ref_1955_lane.png"),
 "1980s": (NEUTRAL + "Los Angeles in 1982, a boulevard at dusk, magic hour, warm glowing sky, street lamps and neon signs switched on, the street lamps cast soft pools of light on the road, moving cars have their headlights on, parked cars are dark and unlit, late-1970s and early-1980s "
           "American cars, boxy sedans and station wagons, leafy street trees and palm trees along the sidewalks, billboards and storefront signs, "
           "realistic detail, ", "ref_1978_lane.png"),
}[era]
NEG = ("film grain, vintage photo, film stock look, sepia, faded colours, colour grading, colour cast, retro filter, "
       "vignette, soft focus, police lights, flashing lights, strobing coloured lights, oversaturated neon reflections, "
       "camera shake, handheld camera, wobbling horizon, parked cars with lights on, car hood, bonnet, dashboard, car door, window frame, side mirror, rear window, windshield, camera rig, roof mount, part of our car, modern cars, modern signage, "
       "LED screens, traffic jam, gridlock, bumper-to-bumper traffic, crowded road, dozens of cars, cars facing the wrong way, video game, 3D render, CGI, cartoon, plastic, flat grey buildings, blocky slabs, blurry, text, watermark, "
       "distorted, low quality")
g = {
 "1": {"class_type": "VHS_LoadVideo", "inputs": {"video": VID, "force_rate": 0, "custom_width": 832, "custom_height": 480,
       "frame_load_cap": N, "skip_first_frames": SKIP, "select_every_nth": 1}},
 "2": {"class_type": "UNETLoader", "inputs": {"unet_name": f"wan2.2_fun_vace_high_noise_14B_{PREC}.safetensors", "weight_dtype": "default"}},
 "3": {"class_type": "UNETLoader", "inputs": {"unet_name": f"wan2.2_fun_vace_low_noise_14B_{PREC}.safetensors", "weight_dtype": "default"}},
 "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan"}},
 "5": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
 "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["2", 0], "shift": 8.0}},
 "7": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 8.0}},
 "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": ERA[0] + CAMTXT[CAM]}},
 "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": NEG}},
 "10": {"class_type": "LoadImage", "inputs": {"image": ERA[1]}},
 "11": {"class_type": "WanVaceToVideo", "inputs": {"positive": ["8", 0], "negative": ["9", 0], "vae": ["5", 0], "width": 832, "height": 480,
        "length": N, "batch_size": 1, "strength": STR, "control_video": ["1", 0], "reference_image": ["10", 0]}},
 "12": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["6", 0], "add_noise": "enable", "noise_seed": SEED, "steps": 20, "cfg": 3.5,
        "sampler_name": "uni_pc", "scheduler": "simple", "positive": ["11", 0], "negative": ["11", 1], "latent_image": ["11", 2],
        "start_at_step": 0, "end_at_step": 10, "return_with_leftover_noise": "enable"}},
 "13": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["7", 0], "add_noise": "disable", "noise_seed": SEED, "steps": 20, "cfg": 3.5,
        "sampler_name": "uni_pc", "scheduler": "simple", "positive": ["11", 0], "negative": ["11", 1], "latent_image": ["12", 0],
        "start_at_step": 10, "end_at_step": 10000, "return_with_leftover_noise": "disable"}},
 "14": {"class_type": "TrimVideoLatent", "inputs": {"samples": ["13", 0], "trim_amount": ["11", 3]}},
 "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["5", 0]}},
 "16": {"class_type": "ImageFromBatch", "inputs": {"image": ["15", 0], "batch_index": N - 1, "length": 1}},
 "17": {"class_type": "SaveImage", "inputs": {"images": ["16", 0], "filename_prefix": f"plates/still_{era}_{TAG}"}},
 "18": {"class_type": "VHS_VideoCombine", "inputs": {"images": ["15", 0], "frame_rate": 24, "loop_count": 0, "filename_prefix": f"plates/still_{era}_{TAG}_clip",
        "format": "video/h264-mp4", "pix_fmt": "yuv420p", "crf": 16, "save_metadata": False, "pingpong": False, "save_output": True}},
}
if NOREF:
    del g["10"]; del g["11"]["inputs"]["reference_image"]
out = f"{os.path.expanduser('~')}/Documents/OrbitalPlates/comfy_workflows/wan22_funvace_still_{era}_api.json"
json.dump(g, open(out, "w"), indent=1)
if "--submit" in sys.argv:
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8188/prompt", json.dumps({"prompt": g}).encode(),
                                                      {"Content-Type": "application/json"}))
    print(r.read().decode())
else:
    print("wrote", out)
