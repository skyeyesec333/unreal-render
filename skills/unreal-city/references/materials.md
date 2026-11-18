# Light and materials for a night city

All of these are Unreal materials built by script from Custom (HLSL) nodes, so they are text and can be reviewed. The snippets are the working cores; parameter names are the ones a material instance sets. Numbers are for a manual exposure with a bias of about -2 and are starting points: calibrate with one-frame tests and keep them as parameters.

**Status of each section** is stated, because some of this was settled by measurement and some was still on trial when written.

## 1. Windows (settled: approved by the scene's owner, stable across reviews)

Three versions failed first: one lit square per room ("windows way too large"), random lit rooms of equal brightness (every tower a "galaxy"), and bright rectangles on black glass. What a real skyline does:

- Light runs **along floors** in stretches on offices (stacked bars with dark floors between); homes are lit singly and patchily.
- A building has **one light colour**, warm or cool. No pink and cyan rooms.
- About **one window in ten** is lit on homes and hotels. At two or three in ten a tower is a galaxy again.
- Lit windows differ in brightness by **about 20 to 1, skewed**: most dim, a few bright.
- Unlit glass is **not black**: it carries the sky above and the city's glow low down, each pane slightly different, so the frames between panes read as a grid.

**The cell** (wall coordinates in metres; `bid` separates buildings sharing a mesh):

```hlsl
float bid = floor(UV.x / 512.0);
float fl = floor(UV.y / FloorH), fy = frac(UV.y / FloorH);
float pu = (UV.x - bid * 512.0) / PaneW, px = frac(pu);      // counted from the building's own start
float ru = pu / RoomPanes, rid = floor(ru), rx = frac(ru);
float h = frac(sin(dot(float2(rid, fl), float2(127.1, 311.7)) + Seed + bid * 3.71) * 43758.5453);   // one number a room
float band = step(fy, Sill);                                  // the slab edge / balcony front at each floor's foot
float pane = step(Sill, fy) * step(fy, 1.0 - Head) * step(Mx, px) * step(px, 1.0 - Mx);
```

**Rooms behind the glass (interior mapping).** `V` is the camera vector transformed to tangent space; the result is a direction to sample a room cube map with. City Sample ships 38 captured rooms (bedrooms, offices, shops, lobbies) under its window material's folder; use four per wall type.

```hlsl
float ru = (UV.x - bid * 512.0) / (PaneW * RoomPanes);
float2 r = float2(frac(ru), frac(UV.y / FloorH));
float flip = step(0.5, frac(sin(floor(ru) * 12.9898 + floor(UV.y / FloorH) * 78.233 + bid) * 43758.5453)) * 2.0 - 1.0;  // half mirrored
float3 ro = float3(r * 2.0 - 1.0, 1.0);
float3 rd = float3(-V.x, -V.y, min(-V.z, -0.05) / Depth);
float3 inv = 1.0 / rd, t3 = abs(inv) - ro * inv;
float3 hit = ro + rd * min(min(t3.x, t3.y), t3.z);
return float3(-hit.z, hit.x * flip, hit.y);
```

**Which rooms are lit, and how brightly:**

```hlsl
float floorOn = step(hfl, FloorLit * busy);                              // hfl: one number a floor; busy: one a building
float office = floorOn * step(hrun, RunFill) * step(0.1, h);             // hrun: one number per run of RunRooms rooms
float home = step(1.0 - Occupancy * busy, h);
float lit = max(office, home);
float luma = exp2(lerp(-4.0, 1.5, pow(frac(h * 13.1), 1.8)));            // skewed: most dim, a few bright
float3 view = room * RoomGain * luma;                                    // room: the cube sample, half desaturated, its own lamp tint
view = lerp(view, float3(0.22, 0.38, 1.0) * 0.2, step(frac(h * 41.3), 0.07) * (1.0 - Even));   // a few lit only by a television
```

Values that held: `Occupancy` 0.12-0.17 for homes and hotels, `RoomGain` about 0.085 for homes (the captures are bright; at 0.3 the median window sat at 88% of white and the spread vanished), 0.3 for shops and lobbies; offices `FloorLit` about 0.2 with broken runs (`RunFill` 0.6) at modest strength: at 0.3 with full runs, wide slabs became white bar codes.

**Measure it**, do not eyeball it: per tower face, the lit share and the 10th/50th/90th percentile of lit windows' peak brightness. Re-measure after any change near this shader.

**Walls that are walls.** The same shader draws small buildings' walls between their windows. A `Grime` parameter (0 by default, which leaves towers untouched) lays a scanned plaster's light and dark on everything that is not a pane and makes it rough and non-metal.

## 2. The rule that prevents the worst fault (settled)

Any term that falls off with height reads height from the wall's v coordinate. On flat faces v is arbitrary and can be hundreds of metres negative. `exp(-v / 4)` of minus a hundred is ten thousand million: a few hundred such faces produced screen-wide starbursts for four builds.

```hlsl
exp(-max(UV.y, 0.0) / SpillH)      // every fall-off with height, always
```

## 3. Water (shape settled; reflection brightness not solved when written)

A mirror with a slow swell returns sharp broken copies of the far bank. Two layers of ripple show as round blobs on a visible lattice. What works is **one spectrum of many waves with unrelated periods**, small ones dropped where they fall under two pixels, and those running toward or away from the camera weighted up (that is what draws a light into a column):

```hlsl
// P: world position in metres (xy), dist: distance to camera in metres, vd: view direction on the ground plane, t: time
float2 n2 = 0;
for (int j = 0; j < 22; j++) {
  float hj = frac(sin(j * 12.9898 + 4.1) * 43758.5453), hk = frac(sin(j * 78.233 + 1.7) * 24634.63);
  float f = 0.7 * pow(1.23, float(j)) * (0.9 + 0.2 * hk);        // 9 m down to 12 cm, stepping by a ratio
  float a = hj * 6.2832; float2 dir = float2(cos(a), sin(a));    // each its own heading
  float keep = saturate(2.0 - f * dist * 0.0006);                // gone where smaller than about two pixels
  float al = abs(dot(dir, vd));
  float wgt = lerp(1.0, al * al * 1.5, Aniso) * min(1.0, f / 3.0);
  n2 += dir * cos(dot(P.xy, dir) * f + t * (0.5 + 0.9 * sqrt(f)) + hk * 6.2832) * keep * wgt;
}
return normalize(float3(n2 * Ripple * patch, 1.0));               // patch: slow lanes of glassy and ruffled water
```

Base colour near white-grey with metallic 1 (a mirror reflecting about 70% head-on), roughness low near the camera rising a little with distance. Make sure the far bank is **in the ray-traced scene** at all (troubleshooting.md): otherwise the water reflects only what is on screen.

## 4. Scanned surfaces without texture coordinates (settled: compiles and reads)

Scripted meshes have no useful UVs on most faces, so lay scans by **world position along the face's own plane**. A wall's u runs along the wall whatever way it faces; a roof's v runs down its slope.

```hlsl
float3 n = normalize(N);                                           // vertex normal, world space
float3 t = abs(n.z) > 0.999 ? float3(1, 0, 0) : normalize(cross(float3(0, 0, 1), n));
float3 b = cross(n, t);
float3 p = P / 100.0;                                              // metres
return float2(dot(p, t), -dot(p, b)) / Tile;                       // -> the three texture samples
// world normal out (material's tangent-space normal off):  normalize(t * tn.x - b * tn.y + n * tn.z)
```

- **Keep the tuned colours**: divide the scan's luminance by its own measured mean and multiply the material's colour by it; a `Hue` value lets some of the scan's own colour through; a `Contrast` value tames it (a white wall under a plaster scan at full contrast is speckled granite).
- **Broad variation** a few to tens of metres across, or a roof seen whole is one tile repeated.
- **Nothing that moves**: a world-placed scan slides over a boat's hull.
- Import normals as normal maps and the packed ao/roughness/metal picture as linear, and set each sampler's type to match, or the material fails to compile only when the renderer loads it.

Free scans: Poly Haven (CC0). Ten 2K sets covered concrete, asphalt, plaster, tin, tiles, shutters and planks.

## 5. Streets, lamps and the far city (settled in principle; levels still being tuned)

- **Streets carry light**: from above, the brightest thing after towers is the street under its lamps. Warm, in **pools** (brighter every thirty-odd metres), not an even strip.
- **Lamps are the light sources**; windows are only a few times a lit road. Rough real luminances to rank by: lit window about 6 cd/m², floodlit facade 2-6, lit road 0.3-2, lamps and signs far above. Only lamps and signs should clip.
- **The far city**: boxes with sparse windows of one colour a building; a ground-glow picture for the streets; lamp points along main roads. Do **not** fade lights by distance (that made a blackout): haze does the dimming. Past a few kilometres a building is a faint even glow, not separate sparks.
- **Light on every edge is "Tron".** A line of light needs a real fitting to point at; otherwise use a dim hidden cove light or none.
- **Floodlit things fall off from their lights** (strongest at the foot, fading up), or they read as self-lit paint.

## 6. Sky and air (settled by measurement against photographs)

- **Sun under the horizon, lighting no surface** (turn its lighting channels off): it is there for the sky and clouds. The sun's own colour is white; the atmosphere reddens it. Put it where it really sets for the place and season.
- A dim moon and a sky light whose lower half is a dim warm colour (the city's bounce), not black.
- **Two fog layers**: a thin ground layer, and a deep thin one (some hundreds of metres) as the veil that carries the city's glow. Without it, a fifth of a high shot is pure black. Cap the fog's opacity so far lights keep themselves. Tint it close to neutral: measure the sky's red-over-blue in your photographs (about 1.1 in ours) and match it.
- **Measure the photographs' own sky** before setting a target. Ours ran 7-10 of 255 overhead in handheld night shots and 55 in a long exposure; a target taken from memory was wrong twice.
- `unreal.Color` takes **b, g, r, a** by position. Give colours by name.

## 7. Exposure, bloom and where the highlights live (settled by a reviewer's measurement)

- Manual exposure, fixed. One-frame tests before sequences.
- Convolution (FFT) bloom's stock kernel is a star: long spikes on near lamps, nothing on far ones. Photographs of lamps show round halos a few times the lamp's own width. The standard bloom, applied only above white and wide, gives those without veiling the frame. It also softens distant points together: recount the horizon after changing it.
- **When the share of near-white pixels will not rise however bright the sources, find out where the photograph's white pixels are before touching anything.** In the worked case three builds raised lamps, signs and glass and the share stayed at 0.3% against 1-5% in the photographs. The builder then blamed the film curve's shoulder. A reviewer measured instead: the curve did reach 255 on glass and lamp cores, and **59% of the photograph's clipped pixels were in the water**, as reflections. The scene's water returned a dim smear where the real river returns each lamp as a column of clipped glints. The gap was reflection radiance, not sources and not the curve.
- So: a mirror-like facet returns the source's own radiance times Fresnel, and the reflection of a clipping lamp must clip. Reflections that come from a low-resolution cache of surface lighting return an average instead. Make sure bright emissives reach reflections at full value (screen-space reflections help for what is on screen), keep near-camera roughness very low, and fight sparkle with specular anti-aliasing rather than roughness.
- Saturated signs stop at a luma of about 240 with one channel at 255: that is channel clipping on a pure colour, not a tone-curve limit.

## 8. Reflections and the ray-traced scene

A sample project's own settings can keep ray tracing to the street: a culling radius of 150 m, instanced meshes excluded. From a height across a river the far bank is then not in the traced scene. Set per render: the culling radius (1.5 km held on 8 GB), instanced meshes in, Lumen's scene distance and reflection quality up. Check a variable exists in your engine version before trusting it: the log says "no cvar by that name". Shading reflections with hit lighting doubled render time and lost the main reflection here; test before adopting.
