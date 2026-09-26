"""Download LTX-2.3 (ComfyUI split files) + fal 3DREAL IC-LoRA into C:\\ComfyUI\\models. Approved by Danny 2026-09-25."""
import os, shutil
from huggingface_hub import hf_hub_download

M = r"C:\ComfyUI\models"
FILES = [
    ("Kijai/LTX2.3_comfy", "diffusion_models/ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled.safetensors", "diffusion_models"),
    ("Kijai/LTX2.3_comfy", "vae/LTX23_video_vae_bf16.safetensors", "vae"),
    ("Kijai/LTX2.3_comfy", "vae/LTX23_audio_vae_bf16.safetensors", "vae"),
    ("Kijai/LTX2.3_comfy", "text_encoders/ltx-2.3_text_projection_bf16.safetensors", "text_encoders"),
    ("Comfy-Org/ltx-2", "split_files/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors", "text_encoders"),
    ("Lightricks/LTX-2.3", "ltx-2.3-spatial-upscaler-x2-1.1.safetensors", "latent_upscale_models"),
    ("fal/LTX-2.3-3DREAL-LoRA", "3DREAL-light.safetensors", "loras"),
    ("fal/LTX-2.3-3DREAL-LoRA", "3DREAL-strong.safetensors", "loras"),
    ("fal/LTX-2.3-3DREAL-LoRA", "3DREAL-strong-v2.safetensors", "loras"),
]
for repo, fn, sub in FILES:
    dst_dir = os.path.join(M, sub); os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(fn))
    if os.path.exists(dst):
        print("have", dst); continue
    p = hf_hub_download(repo, fn, local_dir=os.path.join(M, "_dl", repo.replace("/", "__")))
    shutil.move(p, dst)
    print("got", dst, f"{os.path.getsize(dst) / 1e9:.1f} GB", flush=True)
print("ALL DONE")
