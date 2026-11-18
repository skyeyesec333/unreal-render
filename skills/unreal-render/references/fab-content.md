# Fab and sample content in a scripted pipeline

## Getting it (the owner, in the launcher)

- **Free Epic samples** (a full city sample, vehicles, environment showcases) come from Fab and the launcher: Fab → the item → *Add to My Library*, then Launcher → Unreal Engine → Library → *Fab Library* → *Create Project* (a full sample project) or *Add to Project* (a content pack into an existing project). Large samples are ~100 GB: choose a project folder on the second drive; the launcher may stage the download on C: first, so C: needs room too.
- **Free and paid packs** from other creators: the same *Add to Project*. Anything paid, or any download, needs the user's explicit yes (name, source, size) before the owner gets it.
- **Engine plugins** from Fab (Cesium for Unreal, for example) install into the engine: Library → *Install to Engine*.

## Working with a sample project

- Build **inside the sample's project** when you need its content: World Partition maps, data layers, materials and Blueprints only load properly there. Put everything of yours under your own folder (`/Game/MyRenders`, the helpers' `ROOT`) and **never rename, move or edit the sample's assets in place**: the launcher can then update the sample, and your work stays separable.
- Read the sample's meshes and materials by path (`unreal.EditorAssetLibrary.load_asset("/Game/...")`) and place them with your own holders.
- Large World Partition maps: load actors in batches through `unreal.WorldPartitionBlueprintLibrary` (`get_actor_descs`, `load_actors`, `unload_actors`) so memory stays bounded when extracting from them.
- A sample's own sky may be a painted dome that ignores your lighting (it stays white at night): hide it (`rig.hide_labels`) and use Sky Atmosphere.
- Samples carry their own post-process and exposure: an unbound PostProcessVolume of yours (from `rig`) wins; check with a one-frame test.

## Licences and credits

- Epic's free samples and Fab's "Standard License" content may be used in renders; redistributing the **assets themselves** (the meshes, textures, the project) is not allowed. Ship frames and video, never the content files, and never commit them to a repository.
- **"UE-Only" content** (Epic marks some samples so, City Sample among them; the label is on the item's Fab page) may only be used in combination with Unreal Engine: rendered frames and video made in Unreal are fine, but exporting its meshes or textures to Blender, three.js or another engine is not. Other Fab items may be used with any tool. Check each item's listing and the Epic Content License Agreement (https://www.unrealengine.com/eula/content) before moving an asset out of Unreal.
- **CC-BY** items need credit. When one goes into a scene, record it in the project's credits list at once: the item's name, the creator, the licence and the link. Put the credits wherever the renders are shown.
- Data: OpenStreetMap is ODbL ("© OpenStreetMap contributors" wherever it shows). Fonts: check each one's licence (OFL fonts are fine to render with).
- Real places and brands in a scene: a recognisable logo on a building is someone's trademark; leave it out of commercial work unless cleared.
