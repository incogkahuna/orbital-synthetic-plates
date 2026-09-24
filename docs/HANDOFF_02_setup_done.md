# Orbital Synthetic Plates — handoff 02 (desktop setup done, 2026-09-21)

**For Claude, in the next session on Danny's desktop.** Read this first, then
`handoff\HANDOFF.md` (the original brief: project goals, Danny's rules, learned settings,
Unreal Python gotchas). This file only covers what changed since: the machine is now set up.

## Working style (Danny's instructions)
- Full control of the machine, bypass permissions on. **Don't stop to ask for access** — just do
  the leg work. Stop only for things only he can do (UAC prompts, sign-ins) or genuine decisions.
- **He's short on tokens — be economical.** One watcher that fires once (never polling loops that
  wake you repeatedly), batch tool calls, short status replies, prefer PowerShell/MCP over
  screenshots, use 0.5-scale screenshots when you must look.

## Machine
- RTX 4500 Ada 24 GB (driver 596.71), 127 GB RAM, Windows 11.
- C: 1 TB NVMe (~125 GB free after setup) — models and projects live here.
- E: 11 TB **USB HDD** — too slow for model loading; OK for archiving finished renders.
- Two monitors: DELL U4025QW (primary, wide) and DELL U3225QE (portrait). The Epic Launcher and
  Unreal windows have tended to open on the U3225QE.
- `Documents` in Windows is redirected to **OneDrive**. The project lives in the *local*
  `C:\Users\danie\Documents` on purpose, so big renders don't sync.

## Where everything is
| What | Path |
|---|---|
| Project home | `C:\Users\danie\Documents\OrbitalPlates\` (`handoff`, `scripts`, `refs`, `comfy_workflows`, `renders`, `deliverables`, `Unreal`) |
| Unreal project | `...\OrbitalPlates\Unreal\OrbitalPlates\OrbitalPlates.uproject` (UE 5.8.2) |
| Rig script (v9) | `...\Unreal\OrbitalPlates\Content\Python\orbital_plates_rig.py` (also in `scripts\`) |
| EXR → PNG / mp4 | `...\OrbitalPlates\scripts\exr_to_png.py`, `exr_to_comfy.py` |
| Reference stills | `...\OrbitalPlates\refs\ref_1978_lane.png` (the look Danny wants), `ref_1955_lane.png` |
| Old VACE 1.3B graph | `...\OrbitalPlates\comfy_workflows\restyle_vace13b_depth_480p_49f_api.json` (wiring reference only) |
| Comfy install | `C:\Users\danie\AppData\Local\Comfy-Desktop\ComfyUI-Installs\OrbitalPlates\ComfyUI` |
| Comfy models / input / output | `C:\Users\danie\AppData\Local\Comfy-Desktop\ComfyUI-Shared\{models,input,output}` |
| Unreal engine | `C:\Program Files\Epic Games\UE_5.8` (5.5.4 / 5.6.1 / 5.7.1 also installed) |

## ComfyUI — ready
- Comfy Desktop, instance **"OrbitalPlates"**, ComfyUI 0.37.0, PyTorch 2.12.1+cu130, Python
  3.13.12. Runs on **127.0.0.1:8188**. Telemetry off.
- **orbital-comfyui MCP** is connected; its workspace default points at the instance above.
  `get_system_stats action:"health"` is the quick check.
- Custom nodes installed and confirmed loaded: VideoHelperSuite, KJNodes, DepthAnythingV2, GGUF
  (the GGUF pack had to be installed from its git URL, `city96/ComfyUI-GGUF`).
  Core `WanVaceToVideo`, `TrimVideoLatent`, `KSamplerAdvanced`, `LoraLoaderModelOnly` are present.
- Models (all complete, sizes match Hugging Face):
  - diffusion_models: `wan2.2_fun_vace_high_noise_14B_fp8_scaled`, `wan2.2_fun_vace_low_noise_14B_fp8_scaled` (16.2 GB each), `z_image_turbo_bf16` (11.5 GB)
  - loras: `wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise` / `_low_noise`
  - text_encoders: `umt5_xxl_fp8_e4m3fn_scaled`, `qwen_3_4b` (for Z-Image)
  - vae: `wan_2.1_vae` (Wan 2.2 Fun-VACE 14B uses the 2.1 VAE), `ae` (Z-Image)
  - Depth Anything V2 weights download on first use of that node.

## Unreal — ready
- Project file written by hand (no wizard). Plugins on: ModelContextProtocol (Unreal MCP),
  ToolsetRegistry, AllToolsets, PythonScriptPlugin, EditorScriptingUtilities, MovieRenderPipeline,
  MoviePipelineMaskRenderPass (additional render passes), CineCameraRigs.
- MCP server auto-starts with the editor (set in `Config\DefaultEditorPerProjectUserSettings.ini`,
  `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings] bAutoStartServer=True`, port 8000).
- Registered in Claude Code (user scope) as **`unreal` → `http://127.0.0.1:8000/mcp`**; it showed
  as connected. **Its tools only exist while the editor is open.** If they're missing, launch:
  `& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "C:\Users\danie\Documents\OrbitalPlates\Unreal\OrbitalPlates\OrbitalPlates.uproject"`
  then wait for port 8000 (one background wait, not a polling loop that wakes you).
- The level is empty and unsaved: the rig script builds everything. There is no startup map yet —
  save the level as `/Game/OrbitalPlates/PlatesMain` after the first run.

## Not done / open items
- **Nothing has been rendered on this machine yet.** The rig script has not been run.
- The UE 5.7.1 update in the Epic Launcher is pending and was left alone (not needed here).
- Danny hasn't said which commercial V2V finishing service he has (Runway Aleph / Luma Modify) —
  ask when it becomes relevant, not before.
- The `/areas/ai-driving-plates.md` history the first handoff mentions is **not** in the Headland
  brain (searched). HANDOFF.md is the only record.
- Old engines 5.5 / 5.6 could be removed to free ~60 GB on C: — only if Danny says so.

## Next steps (in order)
1. With the editor open, run the rig via the Unreal MCP: set `CONFIG["duration_s"] = 30` first
   (quick test), then `py "<project>/Content/Python/orbital_plates_rig.py"` (add
   `Content/Python` to `sys.path` if importing). Save the level as `PlatesMain`.
2. Render **SEQ_PlateRing_C1** only via MRQ
   (`MoviePipelineQueueSubsystem.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)`,
   disable the other 8 jobs with `job.set_is_enabled(False)`). EXRs land in
   `<project>\Saved\PlateRenders\SEQ_PlateRing_C1`.
3. **Close Unreal** (never run it alongside a Comfy render).
4. `python scripts\exr_to_png.py <exr_dir> renders\C1_png 832 480`, then
   `ffmpeg -framerate 24 -i depth_%06d.png -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 14 depth.mp4`
   → copy into the Comfy `input` folder. (ffmpeg is installed via winget; open a new shell if it
   isn't on PATH yet. OpenEXR / numpy / Pillow are installed for system Python 3.13.)
5. Build the Wan 2.2 Fun-VACE graph: start from Comfy's own Wan 2.2 Fun-VACE template if one exists
   (use `list_packs` / the templates), otherwise adapt the old 1.3B graph to two-stage high→low
   noise with `KSamplerAdvanced`. Use the handoff's learned settings: **real CFG ~3.5** (not the
   cfg 1 Lightning mode — it ignores the negative prompt and the hood comes back), **depth
   strength ~0.6**, photo-style prompts, the right-hand-lane prompt pattern, 832×480, ≥25 frames
   and keep the last.
6. One still each for **1955** and **1980s** (rename or regenerate the 1978 ref for the 1980s) →
   show Danny before any long render.
7. On approval: 30 s per era, 8-frame overlapping windows, crossfade, side by side.
