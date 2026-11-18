# The loop: measure, review, fix, journal

The scene in the worked case went from 4 of 10 to 6 of 10 "as a photograph" over seven independent reviews; the eighth marked it down to 5.5 when a round of changes overshot, and said exactly where. The reviews did not make the picture; they stopped the builder believing its own.

## Reference photographs

- Start with photographs **taken near the shot's position**, at the shot's time of day. Then one from a height over the district (it calibrates ground, streets, horizon), then the landmarks close up.
- Prefer openly licensed sources (Wikimedia Commons); read them for look only. Keep each with its source, author and licence.
- **Write down what each photograph is for.** "r1: the mall from a boat: reflections, lamp halos, tents" beats a folder of pictures.
- A handful calibrates one view. As cameras multiply, send an agent to build a library by stretch, time of day and viewpoint (agents.md).
- Satellite "night lights" pictures are stretched for display and useless at district scale; measured radiance products are 500 m a pixel. An astronaut photograph settles pattern and colour (which roads are orange, whether there are dark quarters), not levels.

## What to measure

`scripts/frame_stats.py` on the new frames **and on the photographs**:

- **Sky**: mean of the top rows, and its red over blue. Measure the photographs' own before setting a target.
- **Highlights**: share of pixels above 230 and above 200; the 99th percentile. A real night frame clips on lamps, signs and its brightest glass: in ours the photographs ran 1-5% above 230.
- **Blacks**: share under 8 (a frame with a fifth pure black has no air in it).
- **Windows**: per tower face, lit share and the 10/50/90th percentile of lit windows' peaks.
- **Water**: the 90th percentile and share above 200 in the reflection region, against the same region in a photograph.
- **Horizon**: a count of small bright blobs in the horizon band (it should not fall between builds).

Targets come from photographs, with the photograph named. Scale them to the framing: a mall that fills 5% of the frame cannot supply the highlights of one that fills 40%.

## The review

After every build, an independent frame reviewer (agents.md has the brief): frames, the previous build's frames, the photographs, what changed, what is already known. It returns a score, a ranked list with measurements and crops, verdicts on each change, and regressions.

- **Work its list.** Bring the user only what is theirs to decide.
- **A reviewer can be wrong.** One gave sky targets from memory; a later one, measuring, overturned them. Ask where numbers come from.
- **Protect what the user approved.** Name it in the brief as "measure, do not change".
- **Reviews of the same build by eye will miss what is absent.** No review in eight noticed that no lamp post existed. Counts and projections find absences; eyes find excesses.

## Finding a fault

1. **If it has a place in the frame, project the geometry into the frame.** `scripts/project_points.py` gives the pixel where any world point falls; list what lies under the fault. It also answers "what should be in this frame that is not": project the mapped buildings and compare.
2. **If a fix does not move it, switch the suspect off** (a test level without the lamps; a camera without the haze) before trying a second fix. Four plausible fixes were tried on one fault before a single run with the suspect removed cleared it.
3. **If a number will not respond to its control**, stop turning the control. First find where the reference gets that number from (which pixels of the photograph are white?), then what sits between your control and the measurement. The worked case blamed lamps for three builds and then the tone curve; a reviewer who mapped the photograph's clipped pixels found most of them in the water. A diagnosis is not a measurement either.
4. **Read back, do not trust the log.** After importing, print what the mesh stored (`scripts/ue/probe_uv.py`). After setting a light, log the light's real values. After syncing files, check a new file's date on the worker.
5. **Count what a guard discards** and print it.

## Test levels and variants

- A **landmark-only level** (minutes, not half an hour) for anything about materials, lamps or one building.
- **Several variants in one render**: give cameras their own post-process overrides, or put three material brackets on three buildings. One eight-minute render then answers "which value".
- **Never queue a build with a loop that greps the process list for the first build's command**: the loop's own command line contains those words and it waits on itself for ever. Use `scripts/queue_after.sh`.

## Two layers, two reviews

If the scene has a stylised layer over a real base (neon, holograms, flying traffic), review them apart: the base against photographs with the layer off, the layer against a brief written from a study of that style. Judged together against photographs, every review asks for less of the layer, and it is gone in six rounds without anyone deciding so.

## The journal

One file, written **as each thing happens**: every build (what changed, what the frame and the numbers showed), every review and what it found, every decision of the user's in their words, every mistake and its cause. It is the only thing that survives a lost context, and it is the source for any later write-up. No names, addresses or keys in it. Keep a separate short file of standing facts (paths, traps, current best build) for the next session to read first.

## Showing the user

Send real frames at each build, with one line on what is new and one on what is wrong. Give every status as a short table: job, where, state, how far, when. Say plainly when something is unverified or when a mistake cost time.
