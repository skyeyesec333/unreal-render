# Sources: what the worked city used, and how to keep your own list

Keep a list like this from the first download: for each thing, where it came from, its licence, what you owe (a credit, a fee, nothing), and where it sits on disk. Publishing day is too late to reconstruct it. Nothing below is bundled with this skill; each is fetched by you under its own terms.

**Licences change and listings change. Read the current terms on the source's own page before you rely on any line here, and before commercial use.** This is a record of what was used, not legal advice.

## Map and facts

| Source | Used for | Terms as understood | Where |
|---|---|---|---|
| OpenStreetMap, through the Overpass API | Building footprints, levels and heights, streets by class, river banks, canals, piers, rail and bridge ways, places of worship | ODbL. Credit "© OpenStreetMap contributors" wherever the result is published | openstreetmap.org/copyright · overpass-api.de |
| Wikidata | Published heights of named towers | CC0 | wikidata.org |
| The buildings' own and their developers' public pages | Heights, floor counts, facts the map lacks | Facts only; nothing copied | — |

## Reference photographs (read for look; nothing copied into the scene)

| Source | Used for | Terms | Where |
|---|---|---|---|
| Wikimedia Commons | Night photographs from the shot's side, from a boat, from the bank and from a rooftop 240 m up; daylight ones for shapes. Category pages for the mall and the river; a rooftop night view of the district | Each file has its own licence and author: record both per file | commons.wikimedia.org |
| NASA Gateway to Astronaut Photography of Earth | One oblique astronaut photograph of the city at night: the pattern and colour of its light (which roads are orange, no dark quarters) | Generally public domain; credit NASA | eol.jsc.nasa.gov |
| NASA Worldview (VIIRS night layers) | Tried for city light levels: stretched for display, plain white over the whole core. Not usable at district scale | — | worldview.earthdata.nasa.gov |
| NASA Black Marble (VNP46A4) | Measured night radiance at 500 m. Needs a free Earthdata login. Not used | — | blackmarble.gsfc.nasa.gov |

A style layer (cyberpunk and the like) is studied from artwork pages by **link and description only**. The artwork is copyrighted: download and reproduce none of it, and copy no single work's designs.

## Buildings, props and surfaces

| Item | By | Used for | Terms as understood |
|---|---|---|---|
| City Sample (project, about 96 GB) | Epic Games, on Fab, free | The kit of about 600 modular buildings; captured room cube maps for windows; street props | Epic's content licence: Unreal Engine projects only |
| Soul: City | Epic Games, on Fab, free | A leafed tree; tin, wall, wood and rust textures; slum facade pieces | As above. Its listing was marked "Allows usage with AI: No": the project's owner decided |
| High-Rise Building #01 | mirzaev3d, on Fab | A curved glass residential tower on plots its size | CC-BY: credit the author |
| Rooftop 1, 2, 3 HD JFG | JamyzGenius, on Fab | Stylised neon tower tops | CC-BY: credit the author |
| Rooftop 5 HD JFG | JamyzGenius, on Fab | Larger neon towers and a roof cluster | Fab Standard licence; listing marked no AI use: the owner decided |
| LA Night City | 33333DDDDDDDDD, on Fab | A patch of one real office facade at night, cut from the scan's texture, as a window reference and a facade on some office towers | Fab Standard licence (Personal tier) |
| Lower Sector | tunami3d, on Fab | A modular street and platform kit, for a later stage | CC-BY: credit the author |
| Poly Haven textures (2K): asphalt_03, clay_roof_tiles_02, concrete_wall_006, grey_plaster_03, painted_metal_shutter, peeling_painted_wall, rusty_corrugated_iron, rusty_metal_shutter, weathered_planks, worn_mossy_plasterwall | Poly Haven | Scanned surfaces on paving, quays, roofs, walls, shutters | CC0. No credit required (polyhaven.com/license) |
| Poly Haven model: jacaranda_tree | Poly Haven | The park's trees (a Nanite mesh) | CC0 |
| Noto Sans Thai | Google | Lettering for street signs and LED walls | SIL Open Font Licence |

**Credits owed where the renders are published**, as the list stood: mirzaev3d (High-Rise Building #01), JamyzGenius (Rooftop 1, 2, 3 and 5 HD JFG), 33333DDDDDDDDD (LA Night City), tunami3d (Lower Sector), "© OpenStreetMap contributors". Poly Haven and Wikidata need none.

Considered and not used: paid sky and landmark packs (free and scripted first; paid only on the owner's word); a baked sheet of invented city (the far field here is the real mapped one); a drone scan of another city as geometry.

## Real-world tiles (tested, not used for the buildings)

| Source | Finding | Terms as understood |
|---|---|---|
| Cesium for Unreal with Cesium ion | Streams well; detail follows the game's default pawn, so stand a PlayerStart at the render camera; a low screen-space error fills an 8 GB card | Cesium ion's free Community plan is personal and non-commercial |
| Google Photorealistic 3D Tiles | **No 3D buildings for the worked city**: a 314 m tower was painted flat on the ground. Daylight is baked in: black at night, flat in low sun. Still a good real ground picture under a built city | Needs billing on a Google Maps key; on-screen attribution; restrictions on content made from the tiles. Check before any offline frames go public |

Test a scan on your own city with one daylight frame 500 m from its tallest tower before planning round it.

## Engine and techniques

| What | Where |
|---|---|
| Unreal Engine 5: Python editor scripting, Movie Render Queue, Interchange import pipelines, Lumen (scene distance, far field, hardware ray tracing), volumetric fog, Sky Atmosphere, Nanite | Epic's documentation: dev.epicgames.com/documentation/unreal-engine |
| Interior mapping (rooms behind windows from a box intersection, no geometry) | Joost van Dongen, "Interior Mapping: A new technique for rendering realistic buildings", 2008; Epic's own window material in City Sample uses the same idea with captured room cube maps |
| Real luminances for ranking emissives (a lit window a few cd/m², a lit road 0.3-2, lamps far above) | Lighting-design references; confirm against your own photographs |
| Photographs' measured statistics (sky level, clipped share, window spread) | Your own measurements of your reference photographs with `scripts/frame_stats.py` |

## Tools

| Tool | Used for |
|---|---|
| Tailscale, OpenSSH | Reaching the workers |
| Python 3 (standard library) | Layout, the mesh builder, the glow map |
| numpy, OpenCV or Pillow | Measuring frames, the ground-glow picture, contact sheets |
| three.js in headless Chrome (through Playwright) | The local preview of landmark meshes; rendering sign lettering in complex scripts |
| Blender (headless) | Splitting a multi-part FBX from a download into pieces |

## Keep your own

For each download: file, source page, author, licence, date, size, where it is stored, whether it is backed up, and what credit it needs. Write it the moment the file lands. A reference photograph saved without the user's yes, or an asset whose listing forbids a use you make of it, is a question to put to the user plainly, not to tidy away.
