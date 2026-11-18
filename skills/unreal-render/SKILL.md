---
name: unreal-render
description: Build and render Unreal Engine 5 scenes headless on a Windows GPU PC from Claude Code over SSH - Python-scripted levels (cities from OpenStreetMap, Fab and sample-project content, Cesium real-world tiles) rendered offline with Movie Render Queue into frames and a camera track for a website. Use when the user wants Unreal renders, Movie Render Queue, a City Sample or Fab asset scene, a photoreal backdrop or city for a web page, Cesium or Google 3D tiles in Unreal, or to set up a PC for Unreal work for the first time.
---

# Unreal render: headless Unreal on a GPU PC, driven over SSH

A pipeline that builds levels by Python script on a Windows PC with an NVIDIA card and renders them with Movie Render Queue (MRQ) without opening the editor, then brings the frames and the camera back for the web. It was used to build a lit night city of ~11,000 real footprints from a free sample project's buildings and render it at about a minute per 1080p frame.

```
0. setup     once per PC: recruit it (gpu-job skill), Unreal, the plugins, content, ue.json   (the owner's hands)
1. push      ue-remote.sh setup / push build.py args.json                                     (copies to the PC)
2. build     ue-remote.sh run build.py args.json --timeout 90     -> a NEW level, sequence, config; a RENDER line
3. render    ue-remote.sh render <map> <sequence> <config> --res 1920x1080 --timeout 240
4. camera    ue-remote.sh run export_camera.py cam.json           -> <sequence>.camera.json for three.js
5. fetch     ue-remote.sh fetch <render-folder> ./renders/<name>   (copy only)
```

`scripts/` below is the `scripts/` folder **in this skill's own directory** (as a plugin: `${CLAUDE_PLUGIN_ROOT}/skills/unreal-render/scripts/`), and `examples/` likewise. Run them by full path. On the PC everything lives in one work folder (`UR_WORK`): `scripts/` (ue.ps1, helpers in `scripts/ue/`, your build scripts), `args/`, `logs/`, and `ue.json`.

## 0. First-time setup

Follow [references/setup.md](references/setup.md). In short:

1. **Recruit the PC** with the **gpu-job** skill's recruit guide (Tailscale, OpenSSH Server on Windows, a key; `recruit.sh probe` must say READY). If that skill is not installed, setup.md has the Windows essentials.
2. **Check it can carry Unreal:** an RTX-class card (8 GB of VRAM works for 1080p; 12+ for heavy scenes), a current driver, and disk: the engine is ~60 GB and a large sample project ~100 GB, so plan a second drive.
3. **The owner installs**, at the PC, signed in to their own Epic account: the Epic Games Launcher, Unreal Engine 5.x, the project or sample, and any Fab content ([references/fab-content.md](references/fab-content.md)). They enable the Python Editor Script Plugin, Editor Scripting Utilities and Movie Render Pipeline once in the editor.
4. **Write `ue.json`** in the work folder (engine, project, renders folder), add `r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True` to the project's `Config/DefaultEngine.ini` if you will set exposure in EV, then `ue-remote.sh setup` and `ue-remote.sh check`.

**Never automate the owner's steps:** no installing software, signing in, accepting licences, buying or downloading content, or creating accounts on their behalf. Give the steps; check the result with `check`. A download or purchase needs the user's explicit yes, with name, source and size.

## 1-3. Build and render

```sh
export UR_HOST=render-pc UR_WORK=C:/Users/<you>/ue-work
S=<this skill>/scripts
$S/ue-remote.sh push my_build.py my_args.json
$S/ue-remote.sh run my_build.py my_args.json --timeout 90
#   ... the report ends with: RENDER /Game/MyRenders/Maps/City_1118_093000 /Game/MyRenders/Seq/Vista_1118_093000 /Game/MyRenders/Seq/VistaCfg_1118_093000
#                             RENDERS-TO D:/Unreal/Renders/Vista_1118_093000
$S/ue-remote.sh render /Game/MyRenders/Maps/City_1118_093000 /Game/MyRenders/Seq/Vista_1118_093000 /Game/MyRenders/Seq/VistaCfg_1118_093000 --timeout 240
$S/ue-remote.sh fetch Vista_1118_093000 ./renders/vista-01
```

- **Write build scripts with the helpers** in `scripts/ue/` (`ur`, `materials`, `instances`, `shot`, `rig`, `cesium`); `examples/city_from_layout.py` is a complete one. Each build makes **new** assets stamped with the run time, under your own `/Game/MyRenders` folder, and a new render folder: nothing is overwritten, so any earlier frame can be reproduced.
- **One Unreal job at a time** per PC: `ue.ps1` refuses to start a second. Long renders: `--detach`, then `status`.
- A run fails when Unreal exits non-zero **or** the log has a Python error (`-run=pythonscript` often exits 0 after a traceback). Read the `ERR` lines and the report, fix, run again: a new run makes new assets.
- Do a **one-frame test** (frames=1) before a long sequence: exposure and emissives are the usual misses.
- Keep working files on the PC (renders, logs, the project). Fetch only what the site needs; never delete on the PC without asking.

## 4. The camera for the web

`export_camera.py` with `{"sequence": "/Game/MyRenders/Seq/..."}` writes `<sequence>.camera.json` in the PC's `logs/`: per frame the position (metres), forward and up vectors and the vertical FOV, already in three.js's axes. `fetch-log` it, then in the page: `camera.position.set(...p); camera.up.set(...u); camera.lookAt(p + f); camera.fov = vfov`. Live 3D drawn over the frames then lines up with them.

## Traps

Read [references/traps.md](references/traps.md) before writing a build script. The ones that cost the most: materials on instanced meshes need the usage flags or silently render as the default material; instanced components on a Blueprint lose their materials and instances on save; script-made assets need saving explicitly; per-instance custom data only after the instances exist; exposure in EV needs the ini setting; Google 3D tiles carry baked daylight.

## Files

- `scripts/ue-remote.sh`: this machine's command (setup, check, push, run, render, status, fetch, fetch-log). Needs `UR_HOST`, `UR_WORK`.
- `scripts/ue.ps1`: runs on the PC (check, script, render, status, renders): validated names, a log per run, a timeout, the report.
- `scripts/ue/*.py`: helpers imported by build scripts in Unreal. `scripts/export_camera.py`: the camera export.
- `examples/`: `osm_layout.py` (OpenStreetMap to a layout, runs locally), `overpass-query.txt`, `city_from_layout.py`, `city.args.example.json`.
- `references/setup.md`, `references/fab-content.md`, `references/traps.md`.
