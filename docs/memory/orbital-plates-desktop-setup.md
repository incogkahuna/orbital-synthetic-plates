---
name: orbital-plates-desktop-setup
description: "Where Orbital Synthetic Plates lives on Danny's desktop (RTX 4500 Ada) — project home, Comfy paths, Unreal version, disks"
metadata: 
  node_type: memory
  type: project
  originSessionId: cf0e0b24-f27d-411c-8786-6b0d168e6682
  modified: 2026-09-21T22:51:17.839Z
---

Set up 2026-09-21 on the desktop (RTX 4500 Ada 24 GB, 127 GB RAM, C: 1 TB NVMe, E: 11 TB USB HDD).

- Project home: `C:\Users\danie\Documents\OrbitalPlates` (local, NOT the OneDrive Documents — MyDocuments is redirected to OneDrive; keep big renders out of sync). Subfolders: handoff, scripts, refs, comfy_workflows, renders, deliverables.
- Latest handoff: `C:\Users\danie\Documents\OrbitalPlates\HANDOFF_02_setup_done.md` (read first).
- Handoff bundle origin: `...\Orbital projects\Any drive\starter handoff to super computer\HANDOFF.md`.
- Comfy Desktop instance "OrbitalPlates" at `C:\Users\danie\AppData\Local\Comfy-Desktop\ComfyUI-Installs\OrbitalPlates`; shared models/input/output under `...\Comfy-Desktop\ComfyUI-Shared\`. Telemetry off.
- Unreal 5.8.2 at `C:\Program Files\Epic Games\UE_5.8` (5.5/5.6/5.7 also installed; 5.7.1 has a pending update, not applied).
- Comfy runs on 127.0.0.1:8188 (Desktop picked it; no clash). orbital-comfyui MCP workspace default set to the instance's ComfyUI folder. Custom nodes: VHS, KJNodes, DepthAnythingV2, GGUF.
- Unreal project: `C:\Users\danie\Documents\OrbitalPlates\Unreal\OrbitalPlates\OrbitalPlates.uproject` (UE 5.8, hand-written uproject: MCP, ToolsetRegistry, AllToolsets, Python, EditorScripting, MRQ + extra passes, CineCameraRigs). MCP auto-start set in Config/DefaultEditorPerProjectUserSettings.ini. Registered in Claude Code user scope as `unreal` → http://127.0.0.1:8000/mcp (only live while the editor is open). Rig script copied to Content/Python.
- Keep models on C: — E: is a USB HDD, too slow for 17 GB model swaps.

**Why:** every previous machine's copy was lost/stale; this is now the canonical box.
**How to apply:** start from these paths; see [[orbital-plates-working-style]].
