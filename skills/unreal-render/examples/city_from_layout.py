"""Example build: a night city from a real layout (osm_layout.py), in a new level of its own, ready to render.

Each footprint becomes a box in a glass facade material whose lit windows and neon bands come from world position (so
a box of any size gets 3.8 m floors), streets become dark ribbons, a night rig and a fixed exposure go in, and a camera,
sequence and render config are made. Swap the boxes for kit buildings from a sample project when you have one (keep
the sample's content where it is; read its meshes, never rename them).

Arguments file (in <work>/args), all but layout optional:
  {"layout": "C:/<work>/args/layout.json", "box": [-800, 800, -800, 800], "camera": [-900, -1100, 220],
   "aim": [0, 300, 20], "focal_mm": 24, "frames": 24, "exposure_bias": -2.0, "window_nits": 7500, "neon_nits": 18000}
camera / aim in local metres (x east, y north, z up). The report ends with RENDER and RENDERS-TO lines.
"""
import json, math, os, sys
sys.path.insert(0, os.environ.get("UE_RENDER_LIB", ""))
import unreal
import ur, materials, instances, rig, shot

a = ur.args({"box": [-800, 800, -800, 800], "camera": [-900, -1100, 220], "aim": [0, 300, 20], "focal_mm": 24,
             "frames": 24, "exposure_bias": -2.0, "window_nits": 7500.0, "neon_nits": 18000.0})
if "layout" not in a:
    raise SystemExit("arguments need 'layout' (the file osm_layout.py wrote, copied to the PC)")
with open(a["layout"], encoding="utf-8") as f:
    layout = json.load(f)
x0, x1, y0, y1 = (float(v) for v in a["box"])
U = lambda x, y: (x * 100.0, -y * 100.0)          # local metres (x east, y north) -> Unreal cm (X east, Y south)

level = ur.new_level("City")

# ---- the facade: windows lit by a hash of their cell, neon bands every few floors (real-world units) ----
FACADE = r"""
float3 p = WorldPos / 100.0;
float3 n = abs(Normal);
if (n.z > 0.7) return float3(0, 0, 0);
float2 uv = (n.x > n.y) ? p.yz : p.xz;
float2 g = uv / float2(1.7, 3.8), id = floor(g), f = frac(g);
float seed = dot(floor(ObjPos / 1000.0), float3(12.9898, 78.233, 37.719));
float h = frac(sin(dot(id, float2(127.1, 311.7)) + seed) * 43758.5453);
float lit = step(0.62, h);
float pane = step(0.10, f.x) * step(f.x, 0.90) * step(0.16, f.y) * step(f.y, 0.84);
float3 warm = float3(1.0, 0.58, 0.28), cool = float3(0.30, 0.72, 1.0);
float3 wc = frac(h * 7.31) < 0.7 ? warm : cool;
float band = step(0.95, frac(uv.y / (3.8 * 6.0)));
return wc * lit * pane * WindowNits * (0.6 + 0.4 * frac(h * 13.1)) + cool * band * NeonNits;
"""
mel = unreal.MaterialEditingLibrary
m = materials.fresh("M_Facade")
wp = materials.node(m, unreal.MaterialExpressionWorldPosition, -900, 0)
op = materials.node(m, unreal.MaterialExpressionObjectPositionWS, -900, 100)
nn = materials.node(m, unreal.MaterialExpressionVertexNormalWS, -900, 200)
c = materials.custom(m, FACADE, ["WorldPos", "ObjPos", "Normal", "WindowNits", "NeonNits"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 0)
mel.connect_material_expressions(wp, "", c, "WorldPos"); mel.connect_material_expressions(op, "", c, "ObjPos")
mel.connect_material_expressions(nn, "", c, "Normal")
mel.connect_material_expressions(materials.scalar(m, "WindowNits", a["window_nits"], -900, 320), "", c, "WindowNits")
mel.connect_material_expressions(materials.scalar(m, "NeonNits", a["neon_nits"], -900, 400), "", c, "NeonNits")
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.connect_material_property(materials.vector(m, "Glass", (0.012, 0.016, 0.022), -400, 300), "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(materials.scalar(m, "Metallic", 0.85, -400, 420), "", unreal.MaterialProperty.MP_METALLIC)
mel.connect_material_property(materials.scalar(m, "Roughness", 0.12, -400, 490), "", unreal.MaterialProperty.MP_ROUGHNESS)
materials.finish(m)
road = materials.emissive("M_Road", (0.02, 0.02, 0.025), 0.0)

# ---- buildings: one box per footprint, scaled (the engine cube is 100 cm, pivot at its centre) ----
CUBE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
PLANE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane")
ts = []
for b in layout["buildings"]:
    if not (x0 <= b["x"] <= x1 and y0 <= b["y"] <= y1):
        continue
    X, Y = U(b["x"], b["y"])
    ts.append(instances.xf(X, Y, b["h"] * 50.0, 0, 0, -b["yaw"], b["w"], b["d"], b["h"]))
_, cb = instances.holder(CUBE, [m], "Buildings")
ur.say("buildings", instances.add(cb, ts))

# ---- streets: a flat ribbon per segment ----
rs = []
for r in layout.get("roads", []):
    width = 14.0 if r["kind"] in ("primary", "secondary", "trunk", "motorway") else 8.0
    for (ax, ay), (bx, by) in zip(r["pts"], r["pts"][1:]):
        if not (x0 <= ax <= x1 and y0 <= ay <= y1):
            continue
        L = math.hypot(bx - ax, by - ay)
        if L < 0.5:
            continue
        X, Y = U((ax + bx) / 2, (ay + by) / 2)
        yaw = -math.degrees(math.atan2(by - ay, bx - ax))
        rs.append(instances.xf(X, Y, 5.0, 0, 0, yaw, L / 1.0, width / 1.0, 1.0))
_, cr = instances.holder(PLANE, [road], "Streets")
ur.say("street segments", instances.add(cr, rs))

# ---- ground, night, exposure ----
g = ur.spawn(unreal.StaticMeshActor, (0, 0, 0), label="Ground", path="MyRenders/City")
g.static_mesh_component.set_static_mesh(PLANE); g.set_actor_scale3d(unreal.Vector((x1 - x0) * 1.2, (y1 - y0) * 1.2, 1))
g.static_mesh_component.set_material(0, road)
rig.night()
rig.exposure_manual(bias=a["exposure_bias"], bloom=1.4)

# ---- camera, sequence, config ----
cx, cy, cz = a["camera"]; ax_, ay_, az_ = a["aim"]
cam = shot.camera(at=(*U(cx, cy), cz * 100.0), aim=(*U(ax_, ay_), az_ * 100.0), focal_mm=a["focal_mm"], label="Vista")
seq, cfg, out = shot.sequence_and_config(cam, "Vista", frames=a["frames"])
ur.save_new_assets("Materials")      # the level save does not save new assets
ur.save_level()
shot.render_line(level, seq, cfg, out)
