# Research: making AI driving plates photoreal and stable (Sept 2026)

Scope: Orbital Synthetic Plates (UE 5.8 + Cesium geometry, then ComfyUI Wan 2.2 Fun-VACE depth-to-video, 9-camera ring, 1-5 min takes at 23.976 fps).
Labels used below: **[V]** = verified from the cited source; **[I]** = my inference or recommendation, not tested by us.
Licence flags: **OK** = outputs usable commercially; **COND** = commercial use with conditions; **NC** = non-commercial or unclear, keep it out of client work.

---

## 0. Bottom line

1. **Per-frame hallucination cannot give you 1-5 minute LED-wall plates.** Every diffusion V2V model re-invents texture in every window, and that is where drift, smears and morphing come from. The approaches with the best chance of working for 9 cameras x 5 minutes **move the invention off the time axis**. Either (a) let the AI generate photoreal *textures and materials* that you bake into Unreal and then render normally, or (b) give the video model a *good lit beauty render* so it only has to add realism. Do (b) at low denoise with strong geometry controls, not depth alone. **[I]**
2. The **two best candidate video models** to test against Wan 2.2 depth-only are **NVIDIA Cosmos 3 Nano Transfer**, the purpose-built sim2real model (multi-control, 720p, OpenMDW licence), and **LTX-2.3/2.5 with IC-LoRA Union control** (depth plus canny, fast, community licence). **[V/I]**
3. For long takes, stop crossfading independent windows. Use either a model with **native autoregressive chunking** (Cosmos 3 transfer, the LTX looping sampler) or Wan with a **drift-trained LoRA (SVI 2.0 Pro)**. Colour-match every window to the **Unreal beauty render**, not to window 0. **[V/I]**

---

## 1. Structure-guided / sim2real video models

| Model | Controls | Res / length | Speed / VRAM | Licence (outputs) | ComfyUI |
|---|---|---|---|---|---|
| **Cosmos 3 Nano** (16B, Jun 2026) | Transfer: edge, blur (= downsampled beauty), depth, segmentation, world-scenario map. Multi-control with per-hint weights in the Cosmos Framework; Diffusers takes multiple controls without weights [V] ([cookbook](https://github.com/NVIDIA/cosmos/tree/main/cookbooks/cosmos3/generator/transfer)) | 720p (1280x720) control input; defaults of 121 frames @30 fps; long clips generated **autoregressively in chunks and stitched automatically** [V] ([diffusers docs](https://huggingface.co/docs/diffusers/main/en/api/pipelines/cosmos3)) | Nano fits on a single GPU; Super (64B, about 120 GB of weights) needs 4-8 GPUs [V]. I expect fp8 Nano on a 48 GB card and bf16 on the 96 GB card [I] | **OK**: OpenMDW-1.1, "outputs … entirely free of license restrictions" [V] ([OpenMDW](https://openmdw.ai/license/1-1/), [Nano card](https://huggingface.co/nvidia/Cosmos3-Nano)) | Community wrappers only, T2V/I2V ([ComfyUI-Cosmos3](https://github.com/RyukoMatoiFan/ComfyUI-Cosmos3)). Run transfer in Python/Diffusers [V] |
| **Cosmos-Transfer2.5-2B** (superseded) | Up to 4 controls: edge, blur/vis, seg, depth [V] | 720p, 16 fps, best in multiples of 93 frames; autoregressive sliding window [V] | **65.4 GB VRAM**, about 12-15 min per clip on an H100 [V] ([HF](https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B)) | **OK**: NVIDIA Open Model License, no claim on outputs [V] | No official node |
| **Wan 2.2 VACE-Fun A14B** (current) | Depth, canny, MLSD, pose, trajectory; VACE masks and reference frames [V] ([comfyui-wiki](https://comfyui-wiki.com/en/tutorial/advanced/video/wan2.2/wan2-2-fun-control)) | Trained on **81 frames @16 fps** [V]; 480p/720p | You measured 7.5 min per 49 frames at 832x480 | **OK**: Apache-2.0 [V] ([HF](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B)) | Native + Kijai wrapper |
| **Wan 2.5 / 2.6 / 3.0** | n/a | n/a | n/a | **API-only.** No open weights. "Wan 2.7 open source" pages are SEO fabrications [V] ([Atlas Cloud](https://www.atlascloud.ai/blog/tips/is-wan-3.0-open-source)) | No |
| **LTX-2.3 (22B) / LTX-2.5 (22B, Aug 2026)** | IC-LoRA depth, canny, pose, **Union (depth+canny)**; most 2.3 IC-LoRAs run on 2.5 [V] ([LTX-2.5 card](https://huggingface.co/Lightricks/LTX-2.5)) | Up to 1920x1088 native, 4K via upscaler, 24 fps. **The IC-LoRA path trades resolution for length: roughly 6 s at 720p, 15 s at 480p** [V, secondary source] | Very fast (distilled at 8 steps). fp8 checkpoints available [V] | **COND**: LTX-2.x Community Licence, free under $10M annual revenue, paid above that [V] ([LTX licence](https://ltx.io/model/license)) | **Official**, with templates plus Looping and Extend samplers [V] ([ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)) |
| **LTX-2.3 3DREAL IC-LoRA** (by fal) | Grey or blockout 3D render in, photoreal out. Light and Strong variants [V] | Up to about 1280x704 [V] | n/a | **NC/unclear**: licence "other", contact fal [V] ([HF](https://huggingface.co/fal/LTX-2.3-3DREAL-LoRA)) | Weights are local, no official node. The same idea is available as a hosted endpoint on fal |
| **HunyuanVideo 1.5** | No official depth control (FramePack is built on Hunyuan) | 720p | 8.3B | **COND/NC**: Tencent licence **excludes the EU, UK and South Korea** [V] ([LICENSE](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE)) | Yes |
| **Runway Aleph 2.0** (SaaS) | Prompt, up to 5 keyframe anchors, source video [V] | **30 s max, 1080p**, 24-30 fps [V] ([Runway](https://runway.com/news/introducing-aleph-2-and-edit-studio)) | Cloud | **OK** on paid plans. Inputs are used for training by default [V] ([Runway usage rights](https://help.runwayml.com/hc/en-us/articles/18927776141715-Usage-rights)) | API node |
| **Luma Ray3 Modify** (SaaS) | Source video with a choice of what to preserve (motion, structure, camera…); HDR, 4K HiFi upscale [V] ([Luma](https://lumalabs.ai/ray3)) | Short clips | Cloud | **OK** on paid plans [V] | API |
| **Helios** (Mar 2026) | T2V/I2V long video, no structure control [V] | ~1,440-frame benchmarks | Real-time | Apache-2.0 [V] ([GitHub](https://github.com/PKU-YuanGroup/Helios)) | n/a |
| **Krea Realtime 14B** | Autoregressive | long | real-time | **NC**: CC BY-NC-SA [V] | n/a |

**Assessment [I]:**
- Cosmos is the only family *trained for sim-to-real of driving scenes*. NVIDIA's own CARLA recipe turns simulator video into photoreal video using depth, seg and edge ([cookbook](https://nvidia-cosmos.github.io/cosmos-cookbook/recipes/inference/transfer2_5/inference-carla-sdg-augmentation/inference.html)).
- The catch is that it is tuned for AV and robotics ("physical AI"), not cinematography. It needs long JSON-upsampled prompts. Its default guardrail pixelates faces, so disable it at construction [V].
- Commercial SaaS (Aleph, Ray3) looks great but caps at 30 s or less per call, so it has the same chaining problem as Wan. Use it for look reference only.
- The 3DREAL LoRA confirms that "render-to-real" IC-LoRAs work on LTX. You can train your own on LTX with the official trainer, which keeps the licence clean.

---

## 2. Long-take consistency

| Technique | What it does | Status | ComfyUI today |
|---|---|---|---|
| **Native AR chunking in the model** (Cosmos 3 transfer `num_video_frames_per_chunk`; Cosmos-Transfer2.5 sliding window) | Conditions each chunk on the tail of the previous one; the model was trained this way | [V] | Python only |
| **LTXV Looping Sampler / Extend Sampler** | Temporal tiles with overlap, "carrying context across the seams", optional AdaIN normalisation against drift [V] ([looping_sampler.md](https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/looping_sampler.md)) | [V] | **Yes (official)** |
| **Stable Video Infinity 2.0 Pro** (Wan 2.2 LoRA, ICLR'26 oral) | Error-recycling fine-tune so the model learns to correct its own drift; 10-20 min demos; MIT licence [V] ([GitHub](https://github.com/vita-epfl/Stable-Video-Infinity)) | Built for I2V; the VACE/depth combination is **untested** [I] | Yes (official workflows; use a new seed per clip) |
| **WanVideo Context Options** (Kijai) | Overlapping uniform windows blended in *latent* space, one sampler pass | [V] ([DeepWiki](https://deepwiki.com/kijai/ComfyUI-WanVideoWrapper/6.5-context-windows-for-long-videos)) | Yes. Colour/contrast creep is a known open issue ([#1541](https://github.com/kijai/ComfyUI-WanVideoWrapper/issues/1541)) |
| **Causal AR / self-forcing** (Self-Forcing++, Rolling Forcing, LongLive, Helios) | Minute-scale T2V via rolling KV cache and attention sinks [V] ([Rolling Forcing](https://github.com/TencentARC/RollingForcing)) | Research. **No depth control**, mostly Wan-1.3B based | Not for your use case yet [I] |
| **FramePack F1** | Anti-drift I2V | Hunyuan-based (licence issue), no depth control [V] | Yes |

**What to change in your chain [I]:**
- **Anchor to ground truth, not to window 0.** Your window-0 colour match propagates whatever window 0 got wrong. Render an Unreal beauty pass and, for every window, colour-transfer the generated frames to the *corresponding Unreal frames* (LAB mean/std or a 3D LUT fitted on sky and road masks from your segmentation). This bounds drift to the render instead of letting it accumulate.
- **Feed kept frames as clean latents, not decoded-and-re-encoded pixels.** Each VAE round trip adds saturation and contrast bias. That is a likely cause of the saturation climb you see.
- **Match the model's training frame rate.** Wan was trained at 16 fps [V]. Generating 49 frames that represent 2 s at 24 fps means per-frame motion is off-distribution. Test generating at 16 fps and interpolating (RIFE/GIMM) to 23.976, or switch to a 24 fps-native model (LTX, Cosmos 3). [I]
- **Camera shake.** Your camera is known exactly. Add the negative prompt "handheld, shaky camera", keep the VACE reference frames, and as a safety net measure residual shake as optical flow between the output and the Unreal beauty on static background (using the seg mask) and remove it with a per-frame 2D warp. [I]

---

## 3. Multi-control: does adding seg, normals, edges and beauty help?

- **Yes, per NVIDIA's own guidance [V].** "Multi-control tuning … is required for achieving high-fidelity, structurally consistent video results." Their walk-through goes edge (structure), then edge + vis (appearance consistency), then edge + vis + seg (realism). **Never use seg alone.** Start vis (blurred beauty) at 0.4-0.6. Weights that sum above 1 are renormalised ([Cosmos control modalities](https://nvidia-cosmos.github.io/cosmos-cookbook/core_concepts/control_modalities/overview.html)).
- **The literature agrees.** RealMaster (Mar 2026) lifts game-engine renders to photoreal video by enhancing anchor frames and propagating them with geometric cues. It reports that adding engine depth and normals "significantly improves geometric grounding" ([arXiv 2603.23462](https://arxiv.org/abs/2603.23462)). RGBX-Next (Aug 2026) fine-tunes DiTs on G-buffers (albedo, normal, depth…) as a generative renderer ([arXiv 2608.13929](https://arxiv.org/abs/2608.13929)). [V]
- **Which models accept several controls:**
  - Cosmos 3 and Transfer2.5: up to 4-5, weighted. [V]
  - LTX IC-LoRA Union: depth plus canny. [V]
  - Wan VACE: one control video, but you can pack or composite controls, for example depth with canny overlaid, or use VACE masks per region. [V/I]
  - No open video model takes normals directly. Convert normals to edges or to a shaded "clay" pass instead. [I]
- **What to expect [I]:**
  - Canny from the *Unreal* render (not from the AI frames) locks window mullions, signs and car silhouettes. That directly targets your "cars change shape" and "hallucinated signs" problems.
  - Segmentation or object-ID lets you set *different* denoise and control strength per class: rigid control on cars and buildings, looser on sky and foliage.
  - A lit beauty pass gives the model correct dusk colour, light direction and exposure, which also removes most of the reason for colour drift.

---

## 4. Finishing: upscaling and temporal cleanup

| Tool | Notes | Licence |
|---|---|---|
| **SeedVR2 3B/7B** (ByteDance) | One-step diffusion restoration, native ComfyUI, fp8/GGUF. Batch must be 4n+1 and as long as possible for temporal consistency. LAB colour correction [V] ([numz node](https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler)). Can shimmer on moving high-contrast edges [V, secondary] | **OK** Apache-2.0 |
| **FlashVSR v1.1** | Streaming one-step VSR on Wan2.1, about 17 fps at 768x1408 on an A100. Needs Block-Sparse Attention, which is confirmed working on Ampere (A6000 = Ampere) [V] ([GitHub](https://github.com/OpenImagingLab/FlashVSR)) | **OK** Apache-2.0 weights; the ComfyUI node code is GPL-3 (fine for internal use) |
| **STAR** (NJU/ByteDance) | Older T2V-prior VSR, slower [V] | MIT (I2VGen-XL variant) |
| **LTX-2.3/2.5 Pixel Spatial Upscaler IC-LoRA** | Generative 2x; "synthesizing fine detail rather than simply interpolating" [V] ([HF](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Pixel-Spatial-Upscaler)) | COND (LTX community) |
| **Topaz Starlight Precise 2.5** | Diffusion enhancement with full temporal consistency, aimed at removing the "plastic" look of AI video. Local on RTX 30+ with 10 GB+. Astra 2 is "not for photoreal fidelity" [V] ([Topaz](https://www.topazlabs.com/starlight)) | **OK** (commercial software, subscription) |
| Deflicker | DaVinci Resolve Deflicker, or flow-guided temporal median using **Unreal motion vectors** for exact warps [I] | OK |

**Per-frame image passes (Qwen-Image / FLUX) [I]:** these are not temporally stable as video passes, even at low denoise. Use them for keyframes and texture generation (section 5), not for every frame.
- Qwen-Image (20B) with the InstantX ControlNet-Union (depth, canny…) is **Apache-2.0 (OK)** ([HF](https://huggingface.co/InstantX/Qwen-Image-ControlNet-Union)).
- FLUX.2-dev outputs may be used commercially, but *running the model* for commercial work falls under a non-commercial licence ([BFL](https://bfl.ai/legal/non-commercial-license-terms)). **Treat it as NC** unless you buy a licence.

**Order [I]:** generate, then colour-lock to the Unreal beauty, then SeedVR2 (long batches) or FlashVSR to 1080p/4K, then light temporal denoise. Add grain and lens effects last, in comp, as a *measured* camera profile (real sensor noise and lens) rather than a "film look".

---

## 5. Unreal side: make the AI invent less

**Literature and vendor guidance [V]:**
- Sim2real works best when the simulator already supplies correct geometry, semantics and approximate appearance. The recipe is Cosmos-style multi-control plus a blurred RGB "vis" hint, and G-buffer-conditioned rendering (RealMaster, RGBX-Next, FrameDiffuser [arXiv 2512.16670](https://arxiv.org/abs/2512.16670)).

**Recommendations [I]:**
1. **Render a real beauty pass.**
   - Lumen GI plus a physically plausible dusk sky: SkyAtmosphere, a real sun angle for Sunset Blvd at the date, and an exposure-locked camera.
   - Use real materials: Megascans/Fab asphalt, concrete, stucco, glass with reflections, and emissive neon and signage with period-accurate text you author. Hallucinated signs come from primitives *without* content, so give the model the content.
   - Unreal's frames are rock-solid over time. The more of the final pixel they supply, the less can drift.
2. **Switch from depth-only T2V to low-denoise V2V.** Encode the beauty render and denoise at roughly 0.35-0.6, keeping depth + canny as control. The model then "photographs" your scene instead of imagining it.
3. **Hero cars.** Low-poly Dekogon cars are the main source of close-car smear. Use higher-poly period cars from Fab, or keep cars at *very* low denoise with an object-ID mask. The option most likely to hold up is to composite the Unreal car render back over the AI plate for near-lane cars. [I]
4. **Texture baking instead of per-frame generation (most robust for 5-minute, 9-camera output).**
   - Generate photoreal facades from Unreal depth and canny using Qwen-Image + ControlNet (Apache-2.0).
   - Project them onto the Cesium/OSM building meshes as textures, or create material variants.
   - Then render all 9 cameras for any duration **with zero temporal drift**.
   - Use video AI only as a light "realism" pass at low denoise, or not at all.
   - This is the classic matte-painting / camera-projection approach with AI as the painter.
5. **Export per frame:** beauty, depth, normals, object ID / seg, canny computed from beauty, and motion vectors (used for deflicker and QC). The multi-control models can use all of them.

---

## 6. Experiment plan (1-2 weeks), ranked by expected gain per unit of effort

Use one fixed 20 s test shot (front camera, dusk, one near car) and score every test against the same baseline. For QC, measure flicker (frame-to-frame LPIPS on the static background, warped with Unreal motion vectors) and colour drift (Lab delta vs Unreal beauty per window).

| # | Test | Gain | Effort | Download | Time |
|---|---|---|---|---|---|
| 1 | **Unreal beauty + canny + seg export** (Lumen, dusk sky, a few Megascans materials, authored period signs) | Very high: helps every other test | 1-2 days of artist time | Fab/Megascans (free with UE) | 1-2 d |
| 2 | **Wan 2.2 VACE low-denoise V2V from beauty** (denoise 0.4/0.5/0.6, depth+canny composite, colour lock to Unreal per window, kept frames as latents) | High | Low: your existing graph | none | about 0.5 d setup + 3 variants x 95 min, parallel on 3 A6000s |
| 3 | **LTX-2.3 IC-LoRA Union (depth+canny) + Looping Sampler**, 24 fps native, 720p, then V2V from beauty | High (speed, frame rate, long-take tooling) | Low: official templates | `ltx-2.3-22b-dev-fp8` or distilled, Union IC-LoRA, spatial upscaler via ComfyUI Manager (about 30-50 GB) | 1 d. Expect minutes per 20 s, not hours [I] |
| 4 | **Cosmos 3 Nano Transfer, multi-control** (edge 0.3-0.5 + depth + vis/blur 0.4-0.5 + seg), 720p, AR chunks | High (sim2real specialist, clean licence) | Medium: Python/Diffusers, prompt upsampler, run on the RTX PRO 6000 | `nvidia/Cosmos3-Nano` (HF), cosmos cookbook transfer assets | 1.5-2 d |
| 5 | **Finishing A/B**: SeedVR2-7B fp8 (long batch) vs FlashVSR v1.1 vs Topaz Starlight trial on the best output from tests 2-4 | Medium-high (fine detail) | Low | SeedVR2 via ComfyUI Manager; FlashVSR v1.1 (HF); Topaz trial | 0.5-1 d |
| 6 | **Texture-bake prototype**: Qwen-Image + ControlNet-Union facades for about 10 buildings, projected in UE, rendered 2 min on 3 cameras | Potentially highest for 5 min x 9 cameras | Medium-high | Qwen-Image fp8, InstantX ControlNet-Union | 2-3 d |
| 7 | **SVI 2.0 Pro LoRA** on Wan 2.2 for the chaining (check whether it tolerates VACE depth) | Medium, uncertain | Low-medium | SVI 2.0 Pro high/low LoRAs + official workflow | 1 d |
| 8 | **Train your own render-to-real IC-LoRA** (LTX trainer; pairs of Unreal render and real LA dusk driving footage you have rights to) | High long-term | High | LTX-2 trainer | after the PoC |

**Decision gate at the end of week 2 [I]:**
- If any of tests 2-4 holds 60 s with no visible drift *after* the Unreal colour lock, scale that path to 9 cameras on the farm.
- If none does, pivot to test 6 (texture baking) as the production path and keep video AI as an optional low-denoise realism pass.

**Licence summary:**
- **Safe:** Wan 2.2 (Apache), Cosmos 3 / Transfer2.5 (OpenMDW / NVIDIA OML), SeedVR2, FlashVSR, Qwen-Image, SVI (MIT), Helios, Topaz, and Runway/Luma on paid plans.
- **Conditional:** LTX (under $10M annual revenue); HunyuanVideo (excluded in the EU, UK and South Korea).
- **Avoid for client work:** Krea Realtime, fal 3DREAL (until you get terms from fal), and FLUX.2-dev inference without a licence.
