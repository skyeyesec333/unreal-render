# unreal-render

A Claude Code skill for building and rendering **Unreal Engine 5** scenes on a Windows GPU PC, headless, over SSH: Python-scripted levels (a city from OpenStreetMap, sample and Fab content, optionally Cesium's real-world tiles) rendered with Movie Render Queue into frames and a camera track you can composite on a website.

```
first-time setup → push scripts → build a NEW level by script → render offscreen → export the camera → fetch (copy only)
```

It came out of building a lit night city on ~11,000 real building footprints from a free sample project's kit, rendered at about a minute per 1080p frame on an 8 GB card, with live 3D drawn over the frames in three.js.

## What the skill does

1. **Walks you through first-time setup:** recruiting the PC (Tailscale + SSH, via the companion [gpu-job](https://github.com/skyeyesec333/gpu-job) skill), checking it can carry Unreal, the owner installing the engine, plugins and Fab content, and a read-only `check` of the result.
2. **Runs build scripts headless** (`ue.ps1` on the PC, `ue-remote.sh` here): a log per run, a timeout, one job at a time, and a run that fails on a Python traceback even when Unreal exits 0.
3. **Gives build scripts helpers** that avoid the traps: new time-stamped assets every build (nothing overwritten), materials with the instanced/Nanite usage flags, instanced meshes on plain actors, saved script-made assets, fixed exposure and a night rig, a camera + sequence + render config, Cesium georeferencing done right.
4. **Renders with Movie Render Queue offscreen** and **exports the camera** in three.js's axes, so live 3D lines up with the frames.
5. **Fetches renders, copy only**: working files stay on the PC.

## Install

**As a Claude Code plugin** (from inside Claude Code):

```
/plugin marketplace add skyeyesec333/unreal-render
/plugin install unreal-render@unreal-render
```

**Or as a plain skill:** copy `skills/unreal-render` into `~/.claude/skills/` (all your projects) or into a project's `.claude/skills/`:

```sh
git clone https://github.com/skyeyesec333/unreal-render
cp -r unreal-render/skills/unreal-render ~/.claude/skills/
```

## Use

Ask Claude:

- "Set up my gaming PC for Unreal renders"
- "Build a night city from this OpenStreetMap area and render a test frame"
- "Render the latest sequence at 1920x1080 and bring the frames back"
- "Export the camera from that shot for the site"

Or by hand:

```sh
export UR_HOST=render-pc UR_WORK=C:/Users/you/ue-work
skills/unreal-render/scripts/ue-remote.sh setup
skills/unreal-render/scripts/ue-remote.sh check
skills/unreal-render/scripts/ue-remote.sh push layout.json city.args.json
skills/unreal-render/scripts/ue-remote.sh run city_from_layout.py city.args.json --timeout 90
skills/unreal-render/scripts/ue-remote.sh render <map> <sequence> <config> --res 1920x1080 --timeout 240
skills/unreal-render/scripts/ue-remote.sh fetch <render-folder> ./renders/city-01
```

## Requirements

- [Claude Code](https://claude.com/claude-code); locally bash, ssh/scp, Python 3
- A Windows PC with an NVIDIA RTX card (8 GB+), OpenSSH Server and key login, room on disk (the engine ~60 GB, a large sample ~100 GB)
- Unreal Engine 5.x from the Epic Games Launcher, with the Python Editor Script Plugin, Editor Scripting Utilities and Movie Render Pipeline enabled in the project
- Optional: Cesium for Unreal and a Cesium ion account; check the licences for commercial use (see `references/setup.md`)

No Epic or Fab content is included or redistributed: you get it in your own launcher under its own licence.

## Licence

MIT. See [LICENSE](LICENSE).
