# Troubleshooting: symptom, cause, fix

Every row cost at least one build. unreal-render's `references/traps.md` has the engine-level traps (usage flags, instancing, saving assets, exposure in EV, Cesium); this file is what building a city added. Read both before writing a builder.

## Silent failures when Unreal runs without its window

| Symptom | Cause | Fix |
|---|---|---|
| Walls crossed by bright bars, or panes with ragged edges; a "fix" to mesh build settings changes nothing | Texture coordinates are stored as 16-bit halves by default. With coordinates in metres, at a value of 60,000 a half steps by 32 m; even at a few hundred it steps by centimetres. `EditorStaticMeshLibrary.set_lod_build_settings` forwards to a subsystem that is `None` in a commandlet: it does nothing and raises nothing (the matching `get_` returns defaults). | Set it **at import** with your own `InterchangeGenericAssetsPipeline` (`common_meshes_properties.use_full_precision_u_vs`, `use_high_precision_tangent_basis`), passed as `ImportAssetParameters.override_pipelines`. Verify with `scripts/ue/probe_uv.py`. |
| A material keeps a value you removed from your table | A material instance reused from an earlier run keeps every parameter that run set | `MaterialEditingLibrary.clear_all_material_instance_parameters` before setting; or new instances per run |
| A mesh draws as nothing, or as a fraction of its triangles | The sample project builds every import for Nanite; low-triangle meshes and additive materials do not survive it | Turn Nanite off in the import pipeline (`mesh_pipeline.build_nanite = False`) or on the mesh's own `nanite_settings`; log the triangle count |
| Sun is blue, moon is warm | `unreal.Color(...)` takes b, g, r, a by position | Name the channels |
| A cvar you set has no effect | It does not exist in this engine version, or the project's own ini overrides it | Search the render log for "no cvar by that name"; read the project's ini for limits (ray-tracing culling radius, instanced meshes in ray tracing) |
| The render exits non-zero after writing every frame | A shutdown assertion (audio streaming, in our case) | Check the frames are complete; treat as harmless once identified in the log |
| The builder reports a material made; the render shows the grey default | A material can be created and still fail to compile when the renderer loads it | Search the render's own log for "Failed to compile" and "missing usage flag" after every run |
| The wrapper renders the previous build under the new name | The builder's log is only emptied once its Python starts; if Unreal dies earlier the old log is still there | Require the log to be newer than the run's start |

## Geometry

| Symptom | Cause | Fix |
|---|---|---|
| Screen-wide starbursts; a view flooded white | `exp(-v / h)` in a shader on flat faces whose v is the map's own coordinate, hundreds of metres negative | `max(UV.y, 0.0)` in every fall-off with height. Found by projecting mesh vertices into the frame and reading the v range of what lay under the flares |
| No lamp posts, columns, sign posts, small fittings | A guard dropping outlines under half a square metre, shared by `box()` | Boxes bypass the guard; guards print what they drop; check triangle counts after adding geometry |
| Half the kit buildings stand with walls edge-on; seams on two faces | A building used the other way round had its pieces turned twice and its scales not swapped | Scale the recipe in its own frame, swap the two plan scales for a quarter turn, turn once |
| Hand-built towers go dark after a lighting change | Shader hashes (`frac(sin(x) * big)`) go flat on inputs in the hundred thousands | Keep per-building offsets small; count rooms from the building's own start; use a sine-free hash where inputs are world positions |
| A waterfront with holes in it; a temple or pier standing alone | The "in water" test dropping bank-side buildings | Centre, or three corners, inside the real water polygon |
| A famous tower missing | Its outline is mapped with no height, so it was never treated as a tower | A table of known heights by map id; list large footprints with estimated heights |
| Signs and rings inside walls | Placed by footprint, not by the building as built | Read back the placed building's size |
| A landmark you added is not in the shot | Another building hides it from that camera | Project it and what stands in front before modelling it for that shot |

## Light

| Symptom | Cause | Fix |
|---|---|---|
| The horizon is a star field, "a galaxy cluster" | Far buildings with bright windows of several colours at full strength | Few windows, one colour a building, a faint even glow past a few kilometres |
| The horizon is a blackout | A fade by distance on the far city | Distance does not dim a light; haze does. Remove the fade, add fog and lamp points |
| A glowing ground still gives no horizon | Seen edge-on a lit street hides behind its buildings and is no brighter for being far | Lamp points along roads, which crowd together with distance |
| Cream puddles round every tower foot | The far field's "light in the gaps" guess applied inside the mapped district | Street lines only where streets are mapped |
| The sky is brown-red, or violet-black | A warm sun colour (the air already reddens it); or the sun in the wrong part of the sky | White sun, real azimuth, a few degrees under the horizon, lighting channels off |
| Towers are galaxies | Too many lit windows at equal brightness | One in ten, skewed 20 to 1; measure |
| Office slabs are bar codes | Whole floors lit full width near white | A fifth of floors, broken runs, modest strength |
| Small-building rows are white paper models | The street's light washing three storeys evenly, cool | Warm, weak, over the first few metres only; then surfaces |
| Lines of light on every edge | Decoration with no fitting behind it | Dim coves, or nothing |
| Whole faces gold with building-shaped shadows at "night" | The dusk sun lighting surfaces | Sun lights no surface |
| Black streets and blocky water across a river | The far bank is outside Lumen's scene and the ray-traced scene | Raise Lumen's scene distance; ray-tracing culling radius; instanced meshes in ray tracing |
| Lamps light nothing | Emissives as small as a lamp head are culled from global illumination | Real lights near the shot, or light pools in the ground material |
| Lamps flare into fog cones | Volumetric scattering on hundreds of small lights; inverse-square fall-off with a long reach | No fog scattering on them; a bounded fall-off |
| Star spikes on near lamps, nothing on far ones | Convolution bloom's stock kernel | Standard bloom above white, wide |
| Near-white pixels far below the photographs however bright the sources | Usually the reflections, not the sources or the curve | Map where the photograph's white pixels are first |
| Blue sparkle on near water | Steeper small waves with no specular anti-aliasing | Roughness from normal variance; drop waves under two pixels |
| Reflections as round blobs on a lattice | Two or three ripple layers sharing periods | One spectrum of many unrelated waves |
| A white wall reads as speckled granite | A scan at full contrast on a pale surface | Scale the scan's contrast down for pale materials |
| Trees are bare branches | The sample's trees have no leaves by design; or a fine-leaved tree shrunk and unlit | A broad-crowned tree of the place, lit from below |

## Process and shell

| Symptom | Cause | Fix |
|---|---|---|
| A queued build never starts | A wait loop grepping the process list for the first build's command matches its own command line | `scripts/queue_after.sh`; or chain with `;`; or wait on the worker's own process |
| A sync writes a strange folder locally and nothing on the worker | In zsh `$W:path` applies the `:r`, `:h`... modifiers to `$W` | `${W}:path`, always |
| A script runs half-edited | The shell reads a script as it runs | Never edit a wrapper during a run; write a new file |
| PowerShell one-liners over SSH lose `$_` | Quoting through two shells | Copy the log to your machine and search it there; or `-EncodedCommand` |
| A pattern with `\|` matches nothing | Basic versus extended regular expressions differ by tool | Test the pattern alone first |
| Two fixes "confirmed by the log" changed nothing | A log line saying a setting was set proves nothing | Read the result back from the asset |
| A shared machine stops answering during a render; the job dies with no frames | System RAM, not GPU memory: loading a level from a large sample project took 21 GiB on a 29 GiB box already in swap | Measure RAM first (`scripts/measure_job.py`), check the fit (`scripts/fit_check.py`), run under a RAM cap |
| A second machine refuses to compile the project | Stale `Intermediate` from a broken install; clang treats unreachable-code warnings as errors | See workers.md |

## When the picture is wrong and you do not know why

1. Does the fault have a place in the frame? Project the geometry there (`scripts/project_points.py`) and list what is under it.
2. Can the suspect be switched off for one run in a small test level?
3. What does the reference do? Measure the photograph, not your memory of it.
4. Was the last "fix" verified by reading something back?
5. After two failed fixes, stop and get a second opinion (a researcher or reviewer agent, a stronger model) before a third.
