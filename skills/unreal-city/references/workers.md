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

## Calibrate before you borrow: RAM, GPU memory and CPU, measured

A render that fits a graphics card can still take a machine down by its **system RAM**. In the worked case a test level whose frames used 5.7 GB of GPU memory needed **20.9 GiB of RAM** to load, because it lives in a 96 GB sample project; on a shared box with an 8 GiB rule for guests and swap already in use, the machine stopped answering for several minutes and the job died with no frames. GPU memory had been requested carefully. RAM had not been measured at all.

Resident memory understated it, too: when the kernel killed the job it held 18.75 GiB resident **plus 22.95 GiB swapped out**, about 41.7 GiB in all. A machine in swap hides a job's real size, so `measure_job.py` counts swapped memory on Linux, and a measurement taken on a box that was swapping is a floor, not a figure. The box's administrator set the rule that followed: 8 GiB per guest job including children and file cache, no swap allowance, at least 12 GiB available before launch, one guarded job at a time, and a GPU grant does not buy system RAM. This project's renders stay on a machine with the memory for them.

So before any job goes to a machine that is not yours alone:

1. **Measure the smallest real job** (one frame of the test level) on a machine you own, with `scripts/measure_job.py` (Linux, macOS) or `scripts/measure_job.ps1` (Windows) wrapped round the render command. It adds up the memory of the job and everything it starts (shader workers too), reads the GPU, and writes `budget.json`: peak RAM and in which phase, peak GPU memory, how many processes ran at once, and what to ask for (the peak plus 15%).
   ```sh
   python3 measure_job.py --label lm-test --log Saved/Logs/Project.log --mark "Movie Pipeline" --out budget.json -- <render command>
   ```
2. **Measure twice.** The first run on a machine compiles shaders (CPU and RAM heavy, one worker per core unless told otherwise); the second is the steady figure. Keep both.
3. **Check the fit** against the box's own rules before requesting anything:
   ```sh
   python3 fit_check.py budget.json --ram-limit 8 --gpu-free 10016 --gpu-margin 512 --threads-limit 4
   ```
   It exits non-zero and says what to ask the owner for when the job does not fit. **If it does not fit, do not run it there**: take the numbers to the owner.
4. **Read a broker's arithmetic.** One box granted only if free GPU memory was at least the request plus a fixed margin; a request with comfortable headroom was refused by 8 MiB and paused a service for nothing. Ask for the measured figure.
5. **Run under a hard cap anyway.** On a shared box wrap the job in `measure_job.py --ram-cap <GiB>`: if it passes the cap its whole process tree is stopped and the box stays up. Better still, ask the box's owner for a memory-limited cgroup for guest jobs.
6. **Every resource has its own rule.** GPU memory, system RAM, CPU threads and priority, time, disk. A broker usually enforces only the first. Check a new kind of job against each: the same run also started eight shader workers on a box whose rule was four threads.

Measured on the worked project (Unreal 5.8, City Sample, 1080p, Lumen with hardware ray tracing): a full-city render peaked at **7.7 GB of GPU memory**; a landmark-only level at 5.7 GB of GPU memory and **about 21 GiB of RAM**. Your own numbers will differ: that is the point of measuring.

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
