# Workers: one GPU PC, then two

Start with one. unreal-render's `references/setup.md` covers a Windows PC from nothing (Tailscale, OpenSSH Server, a key, the engine, the plugins, the work folder); gpu-job covers recruiting any PC and sharing a box politely. This file is what a city project adds.

## What one 8 GB card managed

- A district of about 11,000 footprints, 110 towers, 120,000 far-field boxes: a 1080p frame in about a minute, ten shots and the build in about 25 minutes.
- Ray tracing out to 1.5 km with instanced meshes included did not run out of memory. Streaming photogrammetry tiles at high detail did.
- A 3.9-million-triangle tree as a Nanite mesh was fine.
- The first run of a sample project compiles shaders for an hour or more; later runs reuse the cache.

## The network is part of the worker

- Measure the link before planning round it. A PC on Wi-Fi at 100 Mbit/s moved 3-6 MB/s whatever the route; a USB stick on the same PC wrote slower still.
- **Send only what changed.** A wrapper that re-sent 90 MB of meshes before every build cost minutes each time. `scripts/sync_changed.sh` keeps a list of sizes and times of what it last sent.
- Keep renders, caches and the project on the worker. Fetch frames; leave the rest.

## A second worker

It is worth having for parallel test levels, path-traced reference frames and long sequences. It roughly halves the wait only when the two can run different jobs; the builds themselves are single-machine.

1. **Same engine, to the patch.** A project saved in 5.x.4 does not open in 5.x.2. Read the version from the project's own `.uproject` and the first worker's `Build.version`; install exactly that.
2. **Verify the install** against its own manifest before blaming the project (a Linux install was 79,000 files short of 300,000 the first time; the build errors pointed everywhere else).
3. **Copy the project without its machine-made folders**: leave out `DerivedDataCache`, `Binaries`, `Intermediate`, `Saved`, renders. In the worked case that left 91 GB of 96. Copy folder by folder, mark each done when its file count matches, so a broken link resumes.
4. **Compile the project's C++ for the new OS** if the sample has any (City Sample does):
   - Linux: `Engine/Build/BatchFiles/Linux/Build.sh <Project>Editor Linux Development -project=<path>.uproject -MaxParallelActions=4 -NoHotReload -NoUBA` (`-NoUBA`: the build accelerator otherwise opens a network port while it runs). About nine minutes.
   - If errors persist after fixing their cause, **move the project's `Intermediate` folder aside**: the build tool caches header lists from the failed attempt.
   - Clang on Linux treats unreachable-code warnings as errors in code that compiled on Windows. Silence them at the top of the affected files in the copy (`#pragma clang diagnostic ignored "-Wunreachable-code"` and its `-break`, `-return`, `-loop-increment`, `-aggressive` forms), keeping the originals beside them.
5. **Paths from the environment.** Builders that hard-code `D:/...` will not run on the second machine. Take the scripts folder and the renders folder from environment variables with the first worker's paths as defaults.
6. **The first run rebuilds derived data from nothing** (the cache was not copied): a first headless level build spent a long while compressing a sample's animations before reaching the script's own work. Let it.
7. **Builds can run on the CPU** (`-nullrhi`); only renders need the GPU. On a shared box that means builds need no GPU lane at all.

## A shared box

If the second worker is someone's always-on machine with other services on its GPU, follow gpu-job to the letter: check free memory first, the box's own lanes and STOP file, low priority, a thread cap, a status file others can read. A lane that pauses another service needs the owner's yes each time. Tell whoever else uses the box before and after.

## Running

- **One Unreal job per machine at a time.**
- Builds headless: `UnrealEditor-Cmd <project> -run=pythonscript -script=<file> -unattended -nosplash -nullrhi`. Renders: `-game -LevelSequence=<seq> -MoviePipelineConfig=<cfg> -RenderOffscreen`.
- The builder writes its own short report file (what it placed, counts, a final `RENDER <map> <sequence> <config>` line); the wrapper reads that line to start the render. The render's real log is the project's `Saved/Logs/<Project>.log`: fetch it and search it locally.
- Windows kills an SSH session's children when the session closes: long runs go through a scheduled task (unreal-render's `--detach`).

## The owner's hands

Installing engines and content, signing in, accepting licences, buying anything, changing a machine's system settings: these are the owner's. Give exact steps, wait, then verify. If another person or agent administers a worker, give them the exact version string or the exact missing-file list, not a description.
