# The pipeline: from a bounding box to a city

Everything is a script, so every build can be repeated and compared. The scripts fall into three groups: ones that run on your own machine and write data (`layout.json`, `.glb` meshes, pictures), ones that run inside Unreal on the worker and make a level from that data, and wrappers that send, run, render and fetch (unreal-render's).

A full city build with ten test shots took about 25 minutes on one 8 GB card once the pipeline was mature; a landmark-only test level about 8. Keep a fast test level: it pays for itself the first day.

## 1. Choose the frame of reference

- Pick an **origin** near the middle of the district (a bridge, a square) and work in **local metres: x east, y north, z up**. Every data file uses this frame. Unreal is centimetres with **+Y south**: convert in one place (`U(x, y) = (x*100, -y*100)`), never by hand in a formula.
- Pick the **box**: the district you build properly (a few kilometres across) and the **far field** round it (10 km or more) that only has to make a horizon.

## 2. The map (OpenStreetMap)

- Fetch buildings, highways, waterways, railways and bridges for the box through the Overpass API (unreal-render's `examples/overpass-query.txt` and `osm_layout.py`). Attribution: © OpenStreetMap contributors.
- Each building becomes its **best-fitting rotated rectangle**: centre, width along the long axis, depth, yaw, and a **height**: the mapped height, else levels × about 3.4 m, else an estimate from footprint size and use. Keep where each height came from (`src`).
- Know your data before trusting it. In the worked district: 79% of footprints were plain rectangles, 8 had 3D parts, 72% of heights were estimates. **Published heights for the landmarks** come from Wikidata or the buildings' own pages; put them in a small table that overrides the map.
- **Towers with an outline and no height are silently small.** List every large footprint whose height is an estimate and check the famous ones by name.
- **Water**: build the river or shore as its **real outline polygon** from the mapped banks. A fixed distance from a centre line empties both banks of a wide river.
- **"In the water" must be a strict test.** A building is left out only if its centre, or three of its four corners, is inside the water polygon. A looser test (one corner inside a coarse grid cell that touches water) removed 28 bank-side buildings from the two waterfronts, 14 of them over 20 m: the row a river view looks straight at.
- **Bridges, viaducts and rail** come from ways tagged as bridges: build them as decks on girders with piers, parapets and lamps, with their own traffic in the mesh.
- **Where the map is empty** (in the worked case 28% of the ground, exactly where the shot looked) the ground would be black. Invent a low fabric there: irregular blocks, lanes, low buildings. Keep it in its own file, say in the notes that it is invented, and never let it replace mapped data.

## 3. The mass (a sample project's buildings on real footprints)

- **Extract the kit once**: for each of the sample's buildings, the list of wall and roof pieces with their transforms, materials and per-instance window codes ("recipes"). In City Sample that is about 600 buildings and half a million pieces.
- **Place by nearest shape**: score each candidate by `|log(W/w)| + |log(D/d)| + 0.7·|log(H/h)|`, either way round; choose among the best three at random; scale within limits (about 0.6-1.6 in plan, 0.5-2.2 in height). Outside the limits the kit's windows stop looking like windows.
- **A building used the other way round is the recipe turned a quarter turn, whole.** Scale the recipe in its own frame, then turn it once. Turning the pieces' positions and the pieces separately stood half a city's walls edge-on for a dozen builds.
- **Instances, not actors**: group pieces by (mesh, materials) and add each group to one instanced component on a plain actor. See unreal-render's traps for the instancing rules.
- **Small buildings are their own type.** A footprint under about 250 m² and 20 m is not a tower shrunk down: it is the local small building (a shophouse row, a terrace, a bungalow). Build those as one mesh of your own with bays, shop fronts, signs, ledges, roofs, and leave their boxes out of the kit pass.
- **Decoration follows the building as built**, not the footprint: read back the placed size before hanging signs, rings or roof clusters.
- **A model from outside** (a Fab tower, a scanned building) joins the kit by size: stand it on plots about its own dimensions. Keep its glass on a material laid out in the model's own space so floors stay floors however it is turned.

## 4. Landmarks (hand-built, by script)

The buildings anyone would recognise decide whether the place is believed. A scripted mesh builder is enough; no modelling program is needed.

- **A small mesh class**: `quad`, `tri`, `wall(a, b, z0, z1)`, `ring(polygon, z0, z1)`, `cap`, `prism`, `box`, `lathe(profile)`, `sweep(frames)`, grouped by **material name**, written as `.glb`. A few hundred lines of plain Python.
- **Wall texture coordinates in metres**: u along the wall, v the height. One window shader then lays floors and panes true to scale on every facade, whichever way it faces.
- **Tell buildings apart inside a shared mesh by an offset in u** (for example `floor(u / 512)` is the building's number). Keep those numbers small (under about 140) and count rooms from the building's own start: shader hashes go flat on numbers in the hundred thousands.
- **Flat faces carry no meaningful v.** A roof cap or ledge top has whatever coordinates the builder gave it, often the map's own x and y. Any shader term that reads "height" from v must clamp it (see materials.md): this was the cause of a fault that cost four builds.
- **Guards must count what they drop.** A guard meant for bad map outlines ("skip anything under half a square metre") also swallowed every thin box for the life of the project: lamp posts, sign posts, columns, air conditioners. Print how many were skipped; when adding geometry, check the triangle count rose by what you added.
- **Outlines from the map, heights from published figures, shapes and lighting from photographs.** Read photographs for proportion (how many terraces, how tall the podium against the tower) and for where the light is at night. Copy nothing.
- **A manifest beside the meshes** (`landmarks.json`): each mesh's place and bounds, its material names, the **footprints it covers** (so the city pass leaves those plots empty), and lists the level builder acts on: lamp positions for real lights, tree positions, berths for boats, roofs free for clusters.
- **A local preview**: draw the `.glb` files with stand-in colours in three.js in headless Chrome from any camera, in seconds. It catches wrong shapes before a half-hour build.
- **Import with your own Interchange pipeline** (see troubleshooting.md): full-precision texture coordinates, high-precision tangents, Nanite off for meshes with few triangles and additive materials. Read back each imported mesh's bounds to learn how the importer turned it, and log its triangle count against what the builder printed.
- **Materials by name**: one table maps every material name the mesh builder uses to (parent material, scalars, colours, textures). The mesh says *what* a surface is; the table says *how it looks*; changing a look never means rebuilding a mesh.

Places of worship, stations, piers and markets come from the map's tags: give each kind its own roof and its own night lighting, on its mapped outline.

## 5. Small things that carry scale

- **Street lamps as real lights** near the shot only (a few hundred, no shadows, a bounded fall-off rather than inverse-square, no fog scattering); further off the lamp heads are emissive points. The engine's global illumination ignores emissives as small as a lamp head, so a lamp head alone lights nothing.
- **Traffic**: cars as dark bodies with two white lamps ahead and two red behind on streets over about 10 m wide, keeping to the local side of the road.
- **Boats are kinds, not boxes**: build each real kind (ferry, cruiser, barge and tug, the local small craft) with a lofted hull, lights where that kind carries them, and a short churned wake. Sequence them on their own random stream so adding a kind does not reshuffle the fleet.
- **Trees**: check the sample's trees have leaves (City Sample's are bare trunks by design). A CC0 scanned tree of several million triangles imports as a Nanite mesh. Size and place them from photographs of the real park.
- **Signs**: local script in a proper font, rendered to textures by a browser (text shaping for complex scripts needs one). Use real words; have a reader of the language check them if you can.

## 6. The far field

- Mapped buildings beyond the district become **boxes on one instanced component** (over a hundred thousand is fine) with a cheap window shader that has no texture lookups.
- **The ground's own light is a picture** (a few metres a pixel over the whole extent): street lines by class, dark along water. Inside the district, where streets are mapped, put light in the street lines only; a "light in the gaps between buildings" guess belongs to the far field and draws puddles round every tower foot if used near.
- **Far lamps as points** along the main roads, by class: this, not a glowing ground, is what makes a horizon.
- Check the pattern against a real view of the city at night from height, and its colours against an astronaut photograph (which roads are orange, whether there are dark quarters).

## 7. Cameras

Give every build the shot **and** test cameras, each proving one thing: a wider view, a high view (far field and ground), positions where reference photographs were taken (side-by-side), a street-level view (small buildings, surfaces), a water-level view (reflections), a view toward anything far the shot cannot see. One sequence at one frame a second with a cut per camera renders them all in one pass. Keep frame numbers stable across builds so reviews can compare.
