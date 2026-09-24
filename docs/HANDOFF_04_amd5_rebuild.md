# Orbital Synthetic Plates — handoff 04 (rebuild on AMD5, 2026-09-23)

Read 01–03 first. This covers the rebuild on the studio workstation **AMD5** (RTX A6000 48 GB, Ampere;
Threadripper PRO 7945WX; 511 GB RAM). **AMD5 does not persist** — anything not pushed here is lost.

## Where things live on AMD5
| What | Path |
|---|---|
| Repo (this) | `C:\Users\wilde\Desktop\DH Work\Synthetic Plate` (junction `~\Documents\OrbitalPlates` → here, so scripts' default ROOT works) |
| Unreal project | `unreal\OrbitalPlates.uproject` run **in place** (Saved/Intermediate/DDC/uasset/umap are git-ignored) |
| Cesium for Unreal | 2.29.1 prebuilt, project-local in `unreal\Plugins\` (excluded via `.git/info/exclude`) |
| ComfyUI | `C:\ComfyUI` (git + uv venv, Python 3.12, torch 2.14 cu130, ComfyUI 0.37), `start_comfy.bat`, 127.0.0.1:8188 |
| Models | `C:\ComfyUI\models` — Wan 2.2 Fun-VACE 14B high/low in **fp8_scaled and bf16**, umt5 fp8, wan_2.1_vae, lightx2v 4-step LoRAs, Z-Image Turbo + qwen_3_4b + ae |
| Custom nodes | Manager, VideoHelperSuite, KJNodes, DepthAnythingV2, GGUF, Frame-Interpolation |
| Wilder's repos | `C:\GTHB\<repo>` (flat, mirrors his `D:\GTHB`); `C:\GTHB\clone-gitpollo.ps1` to update |

Scripts now take `ORBITAL_ROOT` / `COMFY_DIR` env overrides (defaults: `~/Documents/OrbitalPlates`, `C:/ComfyUI`).

## Fixed today
- **Denver georeference bug.** Spawning tilesets without an explicit georeference made Cesium auto-create a
  default one at its Denver origin; tiles attached to it, so the rig drove "Sunset Blvd" through Colorado
  foothills (ground traced at -293 m). `cesium_route_level.py` now tags our georeference
  `DEFAULT_GEOREFERENCE` and sets every tileset's `georeference`. If a level shows mountains, check for two
  `CesiumGeoreference` actors and delete `Saved/cesium_route_raw.json` (cached heights).
- **Cars drawn backward.** Box proxies gave Wan no facing cue. `ensure_proxy` now builds a long hood / short
  trunk (cabin at -0.13 L) plus a half-height windshield step on the front. Prompts also say parked cars in
  C5 face the camera. Depth tag **v7** = these shapes.
- **"A million cars" on side views.** Depth had no distant cars — Wan invented them. Prompts now ask for
  light evening traffic; negative adds traffic jam / gridlock / crowded road. Danny: "much better, amazing".
- Depth renders are now **120 s** (`cesium_c1_run.py` `duration_s`), enough for 2-min plates.

## How to run (AMD5)
- Cesium render: touch `unreal\Saved\run_cesium_c1.flag`, launch the editor on the project; it renders C5/C3/C7
  and quits (UE 5.8 + Cesium **crashes on exit** after `render finished success=True` — renders are fine).
  Do **not** use `-ExecutePythonScript` for this: it quits the editor as soon as the script returns.
- Depth → Comfy: `exr_to_png.py <exr dir> renders\Cesium_<cam>_v7_png 832 480`, ffmpeg → `C:\ComfyUI\input\depth_<cam>_cesium_v7.mp4`.
- Stills: `make_still_graph.py <1955|1980s> 33 0.8 1234 --noref --cam=C5 --video=depth_C5_cesium_v7.mp4 --submit [--bf16]`.
- Long plates: `scripts\overnight.ps1 -Seconds 20 [-Bf16]` — 1955 + 1980s × C5, C3, C7, same length for all (Danny).
- Speed: a 33-frame still ≈ 4.8 min on the A6000 (fp8).

## Driving Unreal without clicks
The editor's MCP server (127.0.0.1:8000) speaks plain JSON-RPC; `SlateInspectorToolset` can type into the
Output Log **Cmd** box (`py "<file>"`) — the reliable way to run Python in a live editor. Its synthetic clicks
don't reach buttons in modal dialogs; real `SetCursorPos`/`mouse_event` clicks do.

## Wilder's stack (Nebula / Nexus)
Nebula runs fixed pipelines on its own worker ComfyUIs (`D:\Comfy`, port 8188, "ComfyUI headless" task) with a
GPU arbiter; it cannot run arbitrary graphs and has no Wan/VACE lane. AMD5 ("amd5 / orb-io") is **not** a
registered worker. Plan: develop here, later wrap plates as a Nebula capability to use the farm. Open
questions for Wilder: is AMD5 the ORB-IO box Star-Trax moves to; whose Redis is on :6379.

## Next (proof of concept before any budget ask)
- Danny has **Qwen-Image 2.1** (local; research/non-commercial weights — see Nebula `qwen21.ts`) and
  **Magnific** (API coming). Plan: Qwen 2.1 hero keyframe per camera/era with period photo refs →
  locked first frame for Wan (keyframe-first) → Magnific / SeedVR2 upscale to 4K.
- Cesium ion is on the free **non-commercial** tier; Commercial ($149/mo) before any client plate.
- Budget draft (models/services only; farm covers GPU): https://claude.ai/artifact/AkcQUsHYytCXYxPnimr9Hn
