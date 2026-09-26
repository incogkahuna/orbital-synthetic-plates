# Paid / commercial options for render-to-photoreal driving plates

Researched 2026-09-25 (web only; nothing signed up for, bought or submitted). **[V]** means the price was read on an official or first-party model page on that date. **[E]** means an estimate, a third-party or reseller figure, or my own derivation. Re-check every price before spending.

## Recommendation (5 lines)

1. **Trial first: LTX-2.3 "3DREAL" render-to-real IC-LoRA (Lightricks LTX-2.3 + fal).** It is built specifically to turn CG/game-engine video into photoreal video while keeping layout and camera. Hosted on fal at about $3.1 per plate-minute at 720p (about $12.5 with detail refine). The open weights also run free on our A6000 / PRO 6000.
2. **Trial second: Cosmos3 *Super* on rented Blackwell or H200 (RunPod B200 at $6.79/h [V]).** This tests whether the 64B model invents detail that Nano leaves out (stick palms, grey boxes) while keeping Nano's stability. Our hardware still runs Nano for free.
3. **Benchmark only: Runway Aleph 2 ($0.28/s [V]) and Luma Ray3.2 Modify ($0.216–0.432/s [V]).** They cost 5–8x more, cap at 30 s and 20 s, and give no depth/edge control. Use one short clip of each as a quality reference, not as the pipeline.
4. **Cheapest meaningful trial is about $65:** one 60 s Sunset shot through fal 3DREAL Light and Strong with refine (about $25), about 3 h of RunPod B200 for Cosmos3 Super transfer on the same shot (about $20), plus one 30 s Aleph clip ($8.40) and one 20 s Luma 1080p clip ($8.64) as references.
5. **Skip for now:** Veo (no structure-controlled V2V), Kling Motion Control (animates characters), Beeble SwitchX (live-action compositing), and upscalers (Topaz, Magnific, Runway), which only polish and add no structure.

## Comparison table

Plate maths: **1 min** = 60 s ≈ 1,439 frames at 23.976 fps. **Set** = 9 cameras × 2 min = 18 min = 1,080 s. All figures are output cost only, with no retries or overlap. Chunked takes need about 10–15% overlap on top.

| Option | Structure control | Max clip / chaining | Res | Unit price | 1 min | 9-cam × 2 min set | API | Fit |
|---|---|---|---|---|---|---|---|---|
| **LTX-2.3 3DREAL (fal render-to-real)** | Render video in, first-frame ref, intensity; Light/Strong LoRAs | Frame count configurable; local = your own chaining | 720p (1280×704) native, refine ×2 | $0.0024075 / MP [V] | **$3.12** (720p); $12.49 with refine [E, derived] | **$56**; $225 with refine | fal; weights on HF | ★★★ |
| **Cosmos3 Super / Nano on cloud GPU** | Depth / edge / seg controls (transfer) | 189-frame (~7.9 s) chunks; chain yourself | 720p | RunPod H100 SXM $3.49/h, B200 $6.79/h [V]; Lambda H100 $4.29, B200 $6.99 [V] | ~$2.7–2.8 [E] | ~$50–100 incl. setup [E] | DIY; DeepInfra Super $0.05/s [V] | ★★★ |
| Runway Aleph 2 | Text + reference frame; no depth/edge input | 2–30 s; no cross-clip consistency | 1080p | 28 cr/s × $0.01 = $0.28/s [V] | $16.80 | $302.40 | Yes | ★★ (benchmark) |
| Luma Ray3.2 Modify (V2V) | Strength presets (Adhere/Flex/Reimagine)* | 10/15/20 s | 540p–1080p, HDR/EXR | 720p $2.16 / 10 s; 1080p $4.32 / 10 s [V] | $12.96 (720p) / $25.92 (1080p) | $233 / $467 | Yes | ★★ (benchmark) |
| WAN 2.7 Video Edit | Instruction edit, keeps motion; up to 4 ref images | 2–10 s input | 720p/1080p | fal $0.10 / $0.15 per output s [V]; Magnific ~$0.086/s billed on input+output [E] | $9.00 (fal 1080p); ~$10.3 (Magnific) | $162 / ~$186 | fal, Magnific, others | ★ |
| Happy Horse 1.0 Video Edit | Instruction edit, up to 5 ref images | input 3–60 s, **output ≤15 s** | 720p/1080p, 24 fps | fal $0.14 / $0.28 per s [V] | $8.40 / $16.80 | $151 / $302 | fal, Magnific | ★ |
| Kling O1/O3 video edit | Instruction edit with video input | ≤10 s | 1080p | ~$0.126–0.168/s [E, reseller] | ~$7.6–10.1 | ~$136–181 | Official + resellers | ★ |
| Kling 3.0 Motion Control | Transfers a reference video's motion onto an image | ≤10–30 s | 1080p | fal $0.084–0.112/s [E] | $5–6.7 | $91–121 | Yes | ✗ (wrong tool) |
| Google Veo 3.1 / Flow | T2V/I2V, extend, ingredients; no depth-driven V2V in the API | 8 s + extend | 1080p/4K | $0.40–0.75/s generation [E] | n/a | n/a | Gemini / Vertex | ✗ |
| Topaz Starlight (cloud) | Upscale / restore only | 9,000 frames per job | up to 4K | ~31 credits/min at 30 fps; credits $0.11–0.25 [E] | ~$3–6 | ~$50–110 | Desktop + cloud | Polish only |
| Magnific Video Upscaler (Precision) | Upscale, strength 0–100 | not stated | 720p–4K | per-frame, rate not publicly visible (403) | ? | ? | Yes | Polish only |
| Runway video upscale | Upscale only | — | to 4K | $0.007–0.012 / frame [V] | $10–17 | $181–311 | Yes | Polish only |
| Beeble SwitchX | Relight / replace, pixel-grounded to source | 30 s (Creator) / 60 s (Pro) upload | 1080p cloud | 20 cr/s at 1080p; Pro $60/mo for 2,400 cr → ~$0.50/s [E, derived] | ~$30 | ~$540 | Web app | ✗ (live action) |

\*Luma's strength presets are from the 2025 Modify Video launch; not re-confirmed for Ray3.2.

## Per-option notes

### LTX-2.3 3DREAL IC-LoRA (fal "render-to-real") — new in 2026, best fit
- **What it is:** An in-context LoRA for Lightricks LTX-2.3, released 26 June 2026 by fal and Lovis Odin. It turns "rough 3D renders and CG viewport blockouts" into photoreal video while preserving composition, camera move and layout. Variants: **Light** (faithful), **Strong** (more aggressive), and **Strong v2** (multi-scene coherence).
- **Inputs:** The render video plus an optional photoreal first-frame reference. That lets us pre-grade frame 1 (for example, a Flux/Magnific still of the Unreal frame) and lock the look across all 9 cameras. It has an intensity setting, but no explicit depth/normal input: structure comes from the beauty pass. We could feed a cleaner beauty pass with better placeholder props.
- **Price:** $0.0024075 per megapixel of generated video (w × h × frames) [V]. At 1280×704 × 1,439 frames ≈ 1,297 MP → **$3.12/min**. Detail refine doubles both dimensions, so 4× the cost → **$12.49/min**. The set costs $56, or $225 with refine.
- **Licence:** The fal page marks the endpoint "Commercial use". The weights are on HF under a custom licence built on the LTX-2.x Community Licence: **free commercial self-hosting for entities under $10M annual revenue** (measured across affiliates). Above that a paid licence is needed. For a studio/production, check whose revenue counts.
- **Long takes:** Hosted clip limits are not stated. Running locally in ComfyUI on the A6000 / PRO 6000 gives full control of chunk overlap and first-frame hand-off, so it plugs into the existing chaining work.
- **Risks:** New and lightly reviewed. Because it is an LTX base, fine texture may be softer than Wan. Unknown behaviour on 5-minute takes.
- Sources: https://comfyui-wiki.com/en/news/2026-06-29-ltx-2-3-3dreal-lora-render-to-real · https://fal.ai/models/fal-ai/ltx-2.3-quality/render-to-real · https://huggingface.co/fal/LTX-2.3-3DREAL-LoRA · https://github.com/Lightricks/LTX-2/blob/main/LICENSE.md · https://ltx.io/model/license

### Cosmos3 Super / Nano on cloud GPUs
- **Why:** Nano already gives the stability we need. The open question is whether **Super (64B)** hallucinates plausible detail over crude geometry instead of copying it. Super at BF16 is about 128 GB of weights, so it needs an H200 141 GB or B200 180 GB. It will not fit our 96 GB card in BF16; FP8 might fit, but that is unverified.
- **Speed [V, NVIDIA benchmarks, image-to-video 720p, 189 frames]:** Nano takes H100 80 GB 206 s, B200 110 s, RTX PRO 6000 375 s (vLLM-Omni). Super takes B200 115 s (vLLM) or 96 s (NIM FP8), and H200 221 s. Transfer adds control branches, so I assume **×1.5** [E].
- **Cost per plate-minute [E]:** About 9 chunks of 189 frames with overlap.
  - H100 at RunPod Secure $3.49/h: 9 × 206 × 1.5 = 2,781 s ≈ 0.77 h → **$2.70**.
  - B200 at $6.79/h: 9 × 115 × 1.5 ≈ 1,550 s ≈ 0.43 h → **$2.92**.
  - The set (18 min) is about $50–55 of compute, plus about 1–3 h for model download and setup, so **~$60–100** in total.
- **Hourly prices [V]:**
  - RunPod: H100 SXM $3.49 Secure / $2.69 Community; H100 PCIe $2.89 / $1.99; H200 $4.59 / $3.59; B200 $6.79 / $5.98; RTX PRO 6000 $2.09 / $1.69; A6000 $0.53 / $0.33. Billed per second.
  - Lambda: H100 $4.29, B200 $6.99, GH200 $2.29.
- **Hosted alternative:** DeepInfra lists Cosmos3-Super at **$0.05/s at 720p** [V], with 5–300 frames and 24 fps supported → $3/min, set $54. It advertises video-to-video, but I could not confirm that it exposes depth/edge transfer controls. Treat it as untested.
- **Licence:** NVIDIA Open Model Licence (commercial use permitted — verify the current Cosmos3 text).
- **Note:** Nano on our own RTX PRO 6000 costs roughly 1.4 h of farm time per plate-minute and $0. Cloud only buys speed, or access to Super.
- Sources: https://github.com/NVIDIA/cosmos/blob/main/inference_benchmarks.md · https://huggingface.co/nvidia/Cosmos3-Super · https://deepinfra.com/nvidia/Cosmos3-Super · https://www.runpod.io/pricing · https://lambda.ai/pricing · https://www.spheron.network/blog/deploy-nvidia-cosmos-gpu-cloud-synthetic-data/

### Runway Aleph 2 (and Act-Two)
- **What it is:** Aleph 2.0 (August 2026) is Runway's video-to-video edit model. It works on up to **30 s of 1080p** and changes "only what you want" while keeping the rest. A reference frame can define the target look, and edits can span multiple shots. There is no depth/edge/strength input, so the base clip's pixels are the only structure guide. Our grey boxes may stay grey boxes, or get re-imagined unpredictably.
- **Price [V]:** 28 credits/s, 56-credit minimum, $0.01 per credit → **$0.28/s**. 1 min = $16.80 (2 clips). Set = $302.40.
- **Other models on the same API [V]:** Gen-4.5 12 cr/s; WAN 3.0 5/10/20 cr/s at 480/720/1080p; video upscale $0.007–0.012/frame.
- **Act-Two** (5 cr/s) is performance capture for characters. It is **not relevant**.
- **Long takes:** 30 s cap, and nothing ties one clip's look to the next, so expect seams at every 30 s.
- **Licence:** Outputs are usable commercially on paid plans per Runway's ToS [not re-read]. Enterprise plans are available.
- Sources: https://docs.dev.runwayml.com/guides/pricing/ · https://runway.com/news/introducing-aleph-2-and-edit-studio · https://runware.ai/docs/models/runway-aleph-2-0/guides/editing-video

### Luma Ray3.2 Modify Video
- **What it is:** Video-to-video "Modify" on Ray3.2 (June 2026): up to 20 s, 540p–1080p, native **HDR and EXR export**. EXR is useful for LED-wall pipelines.
- **Price [V, lumalabs.ai/api/pricing]:** Billed in 5 s blocks, at 10/15/20 s lengths.
  - SDR 720p: $1.44 / 5 s, $2.16 / 10 s → $12.96/min, set $233.
  - SDR 1080p: $2.16 / 5 s, $4.32 / 10 s → $25.92/min, set $467.
  - HDR costs ×2; HDR+EXR costs ×3.
- **Long takes:** 20 s cap, with no cross-clip consistency. There is no latency SLA on pay-as-you-go.
- Sources: https://lumalabs.ai/api/pricing · https://lumalabs.ai/llm-info · https://lumalabs.ai/changelog/modify-video-api-release

### Magnific API (WAN 2.7 edit, Happy Horse edit, Kling motion, upscalers)
- **Access:** magnific.com/api/pricing and several docs pages returned 403 or 404 to the fetcher, so **Magnific-specific rates are unverified**.
- **WAN 2.7 Video Edit:** Instruction-based repaint of a 2–10 s clip that keeps motion and layout, with up to 4 reference images.
  - Magnific price: a third-party guide quotes ~$0.086/s billed on input + output → about $0.172 per output second [E].
  - fal price [V]: $0.10/s at 720p, $0.15/s at 1080p.
  - This is the closed sibling of what we already run as Wan 2.2 Fun-VACE, with **no depth input**. It is unlikely to beat our VACE setup on structure.
- **Happy Horse 1.0 Video Edit** (Alibaba; top of Artificial Analysis video arena, April 2026):
  - Global or local instruction edits with up to 5 reference images.
  - Input 3–60 s, but **output capped at 15 s**, at 24 fps.
  - fal price [V]: $0.14/s at 720p, $0.28/s at 1080p.
  - Good for look, but offers no structure lock.
- **Kling Motion Control:** Drives a still image with a reference video's motion (character animation). **Not applicable to plates.**
- **Video Upscaler / Precision:** Diffusion upscaling to 720p–4K with a strength parameter, billed per frame at a rate not publicly visible. We have already found that it sharpens but adds no structure.
- Sources: https://docs.magnific.com/api-reference/video/video-upscaler-precision/overview · https://docs.magnific.com/api-reference/video/video-upscaler/overview · https://docs.magnific.com/api-reference/text-to-video/happy-horse-1/overview · https://fal.ai/models/alibaba/happy-horse/video-edit · https://fal.ai/models/fal-ai/wan/v2.7/edit-video · https://evolink.ai/blog/wan-2-7-video-edit-guide

### Kling (latest: 3.0 / O1 / O3)
- **Video-edit routes:** O1/O3 with video input take instruction edits of clips up to about 10 s. Reseller-reported prices [E]:
  - O1 Pro with video input $0.168/s; O1 Standard $0.126/s; O3 edit from $0.1125/s.
- The official kling.ai/dev/pricing page did not render its prices.
- **Motion Control 3.0:** fal $0.084–0.112/s [E]. Same caveat as above: it is for characters.
- **Long takes:** Same ≤10 s chunking and seam problem.
- Sources: https://kling.ai/dev/pricing · https://evolink.ai/blog/kling-3-o3-api-official-discount-pricing-developers · https://fal.ai (Kling listings) · https://vercel.com/ai-gateway/models/kling-v3.0-motion-control

### Google Veo 3.1 / Flow
- **Capabilities:** Text/image-to-video, "Ingredients", first/last frame and scene extension on the Gemini API and Vertex. Flow adds object insert/remove and conversational editing (Gemini Omni), but I found **no depth- or video-structure-conditioned V2V in the API**.
- **Price [E]:** Veo 3.1 costs $0.40–0.75/s on Vertex / Gemini; Lite and Fast tiers are cheaper.
- **Verdict:** Not suitable for layout-locked plates.
- Sources: https://blog.google/innovation-and-ai/products/veo-updates-flow/ · https://costgoat.com/pricing/google-veo

### Topaz Video / Starlight
- **What it is:** Diffusion restoration and upscaling. It does not add structure.
- **Cloud:** Starlight is limited to **9,000 frames per job** (≈6.25 min at 23.976 fps). It costs about 31 credits per minute at 30 fps and original resolution [V, docs table], or about 25 credits at 23.976 fps [E].
- **Credit prices:**
  - Credit subscriptions: $9.99–499.99 for 80–9,000 credits per month [V].
  - One-time packs: $5–999 for 20–9,000 credits [V].
  - That works out to roughly **$3–6 per plate-minute** [E]. A third-party report quotes 90 credits/min at higher output resolutions, so 4K output could cost 3× more.
- **Local:** Starlight Mini runs locally on the A6000.
- **Use:** Final polish only, after a structural pass.
- Sources: https://docs.topazlabs.com/topaz-video/cloud-rendering · https://www.topazlabs.com/pricing

### Beeble (SwitchLight 3.0 / SwitchX)
- **Products:** SwitchLight Studio is closed; it has been replaced by Beeble Studio (desktop, local 4K relighting) and Beeble Cloud.
- **SwitchX:** Video-to-video "generative compositing" that keeps the subject pixel-grounded while changing lighting and background. It is cloud-only, 1080p, and designed for live action.
- **Pricing:**
  - Plans [V]: Creator $16/month for 540 credits; Pro $60/month for 2,400 credits, with 1-minute uploads.
  - Usage [V]: 6 / 20 / 80 credits per second at 720p / 1080p / 2160p.
  - That is about **$0.50/s at 1080p** [E].
- **Possible use:** SwitchLight PBR passes could relight our car plates later, but it is not a render-to-real tool.
- Sources: https://beeble.ai/pricing-cloud · https://invideo.io/blog/beeble-switchx-compositing/ · https://www.cgchannel.com/2025/11/beeble-launches-switchlight-3-0/

### Other 2026 "sim-to-real" / render-to-real services
- **fal render-to-real (LTX 3DREAL):** Covered above. It is the only hosted, off-the-shelf CG→photoreal video endpoint I found.
- **NVIDIA Cosmos via build.nvidia.com / NIM:** Free trial endpoints for Transfer 1 / 2.5. Cosmos3 NIM is covered by enterprise agreements, with no public per-call price.
- **Reallusion AI Studio (2026 roadmap):** 3D previs → photoreal for iClone and Character Creator users. It is tied to their tools.
- **Visualizee:** Automotive design stills. It does not produce video plates.
- Sources: https://build.nvidia.com/nvidia/cosmos-transfer2_5-2b/modelcard · https://www.cgchannel.com/2026/04/see-reallusions-2026-roadmap-redefining-3d-with-hybrid-ai/ · https://visualizee.ai/for-who/automotive-designers

## Cross-cutting caveats
- **Frame rate:** Most hosted models output 24 (or 30) fps. Conform 24 → 23.976 by re-flagging (0.1% slowdown). Avoid anything that resamples 30 → 23.976, because it will judder traffic.
- **Layout lock:** Every closed tool above (Aleph, Luma, WAN/Happy Horse/Kling edit) conditions only on RGB pixels plus text. None accepts our depth or normal passes. Across 9 cameras, exact traffic-position matching must be QC'd, for example with a difference matte against the Unreal beauty pass.
- **Long takes:** Only self-hosted Cosmos or LTX give us control of chunk overlap and first-frame hand-off. All hosted edit tools cap at 10–30 s, so 5-minute takes mean 10–30 seamed clips.
- **Licences:** Commercial use is allowed on paid tiers of Runway, Luma, Kling and fal endpoints marked commercial, per their public ToS. I did not re-read those terms today, so have production legal check them. The one hard restriction found is LTX-2.x: a paid licence is required at **≥ $10M annual revenue**, measured across affiliates.
