# unreal-render

Builds and renders Unreal Engine 5 scenes on a Windows gaming PC from your own computer, for use as backdrops on a website.

It came out of building a lit night city on about 11,000 real building footprints, rendered at about a minute per 1080p frame on an 8 GB card.

## Two skills

- **unreal-render**: the runner. Sets the PC up, runs build scripts, renders, fetches frames and the camera.
- **unreal-city**: the method for a real city on top of it, from step 1: workers, helper agents (fetch sources, survey, build, review), OpenStreetMap layout, a sample project's buildings on real footprints, hand-built landmarks, night lighting with window, water and surface shaders, and a review loop that holds every frame against real photographs. It comes with troubleshooting tables and the list of sources the worked city used. See [skills/unreal-city](skills/unreal-city/SKILL.md).

## Good for

- Photoreal city or landscape backdrops for a website, rendered on a separate PC
- Setting up a Windows GPU PC for Unreal work for the first time
- Building levels by script, so every build is repeatable and nothing is overwritten
- Lining live 3D on the web up with the rendered frames

## Install

In Claude Code, run:

```
/plugin marketplace add skyeyesec333/unreal-render
/plugin install unreal-render@unreal-render
```

Or copy the skill into your own skills folder:

```sh
git clone https://github.com/skyeyesec333/unreal-render
cp -r unreal-render/skills/unreal-render unreal-render/skills/unreal-city ~/.claude/skills/
```

You can also copy it into one project's `.claude/skills/` folder instead.

## Try asking Claude

- "Set up my gaming PC for Unreal renders"
- "Build a night city from this OpenStreetMap area and render a test frame"
- "Render the latest sequence at 1920x1080 and bring the frames back"
- "Export the camera from that shot for the site"
- "Build my city's riverside at night from the map and review it against real photos"
- "My towers look like galaxies and the water is dead: what is wrong?"

## You'll need

- [Claude Code](https://claude.com/claude-code); on your computer bash, ssh/scp and Python 3
- A Windows PC with an NVIDIA RTX card (8 GB+), OpenSSH Server and key login
- Room on that PC's disk: the engine is about 60 GB, and a large sample project about 100 GB
- Unreal Engine 5.x from the Epic Games Launcher, with the Python Editor Script Plugin, Editor Scripting Utilities and Movie Render Pipeline enabled in the project
- Optional: Cesium for Unreal and a Cesium ion account. Check the licences before commercial use (see `references/setup.md`).

No Epic or Fab content is included or redistributed. You get it in your own launcher, under its own licence.

## How it works

```
first-time setup → push scripts → build a NEW level by script → render offscreen → export the camera → fetch (copy only)
```

Everything runs headless, meaning Unreal runs without its window, controlled over SSH.

1. **Walks you through first-time setup.** It recruits the PC through the companion [gpu-job](https://github.com/skyeyesec333/gpu-job) skill (Tailscale and SSH). It checks the PC can carry Unreal. The PC's owner installs the engine, plugins and Fab content, then a read-only `check` confirms the result.
2. **Runs build scripts** (`ue.ps1` on the PC, `ue-remote.sh` on your computer). Each run gets a log and a timeout, and only one job runs at a time. A run fails on a Python error even when Unreal reports success.
3. **Gives build scripts helpers that avoid known traps**:
   - new, time-stamped assets on every build, so nothing is overwritten;
   - materials with the settings instanced meshes and Nanite (Unreal's detailed-geometry system) need;
   - instanced meshes on plain actors, which keep their materials on save;
   - fixed exposure and a night lighting rig;
   - a camera, sequence and render config;
   - Cesium map placement done right.
4. **Renders with Movie Render Queue** (Unreal's offline renderer) without a window, and **exports the camera** in three.js's axes, so live 3D lines up with the frames.
5. **Fetches renders back, copy only.** Working files stay on the PC.

Or by hand, with paths relative to the cloned repo:

```sh
export UR_HOST=render-pc UR_WORK=C:/Users/you/ue-work
skills/unreal-render/scripts/ue-remote.sh setup
skills/unreal-render/scripts/ue-remote.sh check
skills/unreal-render/scripts/ue-remote.sh push layout.json city.args.json
skills/unreal-render/scripts/ue-remote.sh run city_from_layout.py city.args.json --timeout 90
skills/unreal-render/scripts/ue-remote.sh render <map> <sequence> <config> --res 1920x1080 --timeout 240
skills/unreal-render/scripts/ue-remote.sh fetch <render-folder> ./renders/city-01
```

## Licence

MIT. See [LICENSE](LICENSE).
