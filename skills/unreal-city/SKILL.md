---
name: unreal-city
description: Build a real city in Unreal Engine 5 by script, from nothing but an installed engine and one or two GPU PCs - OpenStreetMap layout, sample-project buildings on real footprints, hand-built landmarks, night lighting, window, water and surface shaders, offline renders, and a review loop that holds every frame against real photographs. Use when the user wants a real or real-based city (their own town, a skyline, a riverside, a district) as a 3D scene or rendered backdrop, a night city that has to look like a photograph, a cyberpunk or stylised layer over a real city, or is stuck on one (flat windows, dead water, a black or star-field horizon, flares, missing buildings, frames that will not brighten).
---

# Unreal city: a real place, built by script, judged against photographs

A method for rebuilding a real city district in Unreal Engine 5 without opening the editor: map data in, a new level out, frames back, and an independent review of each build against real photographs of the place. It was worked out on a 3 km stretch of riverside city (about 11,000 mapped footprints, 110 towers, a mall and half a dozen hand-built landmarks) on one 8 GB card, over some forty builds and eight independent reviews. It is a working method with its failures written down, not a finished recipe: the worked scene was still being improved when this was written.

It sits on two companion skills: **unreal-render** (runs build scripts and Movie Render Queue on the PC, fetches frames) and **gpu-job** (recruits a GPU PC over Tailscale and SSH, and keeps a shared box polite). If they are not installed, install them first or follow their READMEs; this skill does not repeat them.

```
1. workers     one or two GPU PCs with Unreal, reachable over SSH                    (unreal-render step 0, gpu-job)
2. agents      set up the helpers: fetch sources, survey, build, review              (references/agents.md)
3. the brief   the place, the shot, the time of day, the bar; reference photographs   (references/qa.md)
4. the map     OpenStreetMap -> layout.json: footprints, heights, streets, water      (references/pipeline.md)
5. the mass    a sample project's buildings scaled onto the real footprints           (references/pipeline.md)
6. landmarks   the buildings people know, hand-built as meshes by a script            (references/pipeline.md)
7. light       night rig, windows, streets, water, air, the far city                  (references/materials.md)
8. cameras     the shot, and test cameras that each prove one thing                   (references/qa.md)
9. the loop    build -> render -> measure -> independent review -> fix -> journal      (references/qa.md)
10. a layer    optional: a stylised overlay (cyberpunk etc.) judged apart from the base
```

`scripts/` below is the `scripts/` folder **in this skill's own directory** (`${CLAUDE_SKILL_DIR}/scripts/`). Run them by full path.

## 1. Workers

Follow **unreal-render**'s first-time setup for the PC (the owner installs the engine, plugins and content; you check). What this method adds:

- **A free sample project is the building kit.** Epic's City Sample (about 96 GB, free on Fab) holds some 600 buildings made of modular wall pieces with lit windows. Build in a copy of that project, with your own work in your own content folders; rename nothing of Epic's.
- **Disk first.** Engine about 60 GB, the sample about 100 GB, plus renders. Put the project on a second drive.
- **A second worker must match the first exactly**: same engine version to the patch (a project saved in 5.x.4 will not open in 5.x.2), verified install, the project's C++ compiled for that OS. See [references/workers.md](references/workers.md) before copying 90 GB anywhere.
- **Measure before you borrow.** A render that fits the GPU can still need 20 GiB of system RAM. Run one frame under `scripts/measure_job.py`, then `scripts/fit_check.py` against a shared box's rules, before requesting anything there ([references/workers.md](references/workers.md)).
- **Network is the hidden cost.** On Wi-Fi a build that re-sends 90 MB of meshes each time loses minutes per build. Send only what changed (`scripts/sync_changed.sh`).

## 2. Agents

Set these up before the first build, not after the tenth. Each is a sub-agent with its own narrow brief; templates are in [references/agents.md](references/agents.md).

| Agent | Does | Rule |
|---|---|---|
| **Source fetcher** | pulls map data, heights, openly licensed textures and models | downloads only with the user's yes; records source and licence for every file |
| **Reference collector** | builds a library of real photographs along the scene, indexed by where and when | openly licensed only are saved; the rest are links |
| **Surveyor** | reads the photographs: what landmarks, signs, boats, lights exist, where, how lit | says what it saw versus what it inferred |
| **Researcher** | finds how others solved a rendering problem; studies a style | sources with every claim |
| **Frame reviewer** | after every build, judges frames against photographs, with measurements | independent: gets frames and photographs, not your opinion of them |
| **Script reviewer** | reads the build scripts when they change a lot | read-only |

Run the reviewer on a strong model: it is the one whose judgement you cannot check cheaply. Act on findings without asking the user for each; check a reviewer's numbers come from a photograph before making them targets.

## 3. The brief

Before any geometry: **where** (a bounding box), **the shot** (where the camera stands, what it looks at, lens), **when** (night, dusk, day: night hides the most and asks the most of light), **the bar** (in the user's words), and **reference photographs** taken near the shot's position. Five photographs calibrate one view; a scene with ten cameras needs a library. Write down what each photograph is for.

## 4-6. The city

Read [references/pipeline.md](references/pipeline.md). The shape of it:

- **Layout from OpenStreetMap** (`unreal-render`'s `osm_layout.py`): footprints as best-fit rectangles with heights, streets by class, the water's real outline. Expect most heights to be estimates and four footprints in five to be rectangles. Check where the map has **no buildings at all**: that ground needs invented fabric, marked as invented.
- **No scan will save you.** Photogrammetry tiles (Google's, through Cesium) carry baked daylight and, in many cities, no 3D buildings at all: test one tall tower from 500 m in daylight before planning round them.
- **Mass from the sample project's kit**: each footprint gets the nearest kit building, scaled within limits; small buildings become rows of the local building type from a mesh of your own.
- **Landmarks by hand, as plain Python that writes `.glb`**: outlines from the map, heights from published figures, shapes and night lighting read from photographs. Wall texture coordinates in **metres**, so one window shader fits every facade. Preview shapes locally in seconds before a half-hour build.
- **Every build is a new level** with new assets; nothing is overwritten or deleted.

## 7. Light

Read [references/materials.md](references/materials.md): the shaders, with code. What matters most, in order:

1. **Windows are rooms, not rectangles**: interior mapping into captured room cube maps, about one window in ten lit on homes, a skewed spread of brightness of some 20 to 1, runs of light along office floors.
2. **A lit ground does not make a horizon; points do.** Far streets need lamps on posts, far buildings separate sparks. Haze dims distance, not distance itself.
3. **Water is a mirror roughened by many waves of unrelated sizes**, weighted toward those running at the camera, so lights draw out into columns.
4. **Most of a night photograph's white pixels are reflections.** If the frame will not brighten however much the sources are raised, map where the photograph clips before touching lamps or the tone curve: in the worked case 59% of it was the water.
5. **Real units, measured targets.** Rank emissives by real luminance (a lit window is a few times a lit road; only lamps and signs clip).

## 8-9. The loop

Read [references/qa.md](references/qa.md). Each build: render the shot **and** the test cameras; measure (`scripts/frame_stats.py`); send frames and photographs to the frame reviewer; fix its ranked list; journal what was done and what the frame showed. When a fault has a place in the frame, **project the geometry into the frame** (`scripts/project_points.py`) before guessing. When a fix does not move a fault, **switch the suspect off** before guessing again. When a number does not respond to its obvious control over three tries, ask what sits between the control and the measurement.

Then [references/troubleshooting.md](references/troubleshooting.md): symptoms, causes and fixes, including the engine's silent failures when run headless.

## 10. A stylised layer

A review loop optimises what it measures: judged only against photographs, a scene converges on a photograph and any genre layer thins out fix by fix. If the brief is "cyberpunk X" or any stylised city: keep the real city as the base, design the layer from a reference study of that style (links and descriptions, not copies), and **review the two apart**: the base against photographs with the layer off, the layer against its own brief.

## House rules (they are part of the method)

- **Show real frames fast.** A rough frame today beats a plan. Research is short and aimed at one problem.
- **Never delete or overwrite**: new level, new sequence, new render folder each build; old files move to a holding folder only with the user's yes.
- **Downloads, purchases and licence choices are the user's**: state name, source, size, licence; free and openly licensed first, paid packs only on their word. Record every source ([references/sources.md](references/sources.md)) and every credit owed.
- **Working files live on the worker**, not on the laptop.
- **Do not trade picture quality for speed without asking.**
- **Report honestly**: a job is "running" only while it is; a log line saying a setting was set proves nothing until the result is read back.
- **Keep a journal as things happen**, one entry per build, review, decision and mistake, so nothing is more than one build behind when context is lost.
- **Nothing private in a request to an outside service**: a neutral client name, no names or emails.

## Files

- `scripts/frame_stats.py`: sky level and colour, share of near-white pixels, percentiles, for a list of frames (and the photographs).
- `scripts/project_points.py`: where named world points fall in a camera's frame; which mapped buildings a camera should see.
- `scripts/queue_after.sh`: start a build when another finishes, without the self-matching wait loop.
- `scripts/sync_changed.sh`: send a worker only the files that changed.
- `scripts/measure_job.py` (and `.ps1` for Windows): peak RAM, GPU memory and process count of a job and everything it starts, with an optional RAM cap; `scripts/fit_check.py`: does that budget fit a shared machine's rules.
- `scripts/ue/probe_uv.py`: what a mesh really stored for its texture coordinates (run in Unreal).
- `references/agents.md`, `pipeline.md`, `materials.md`, `qa.md`, `troubleshooting.md`, `workers.md`, `sources.md`.
