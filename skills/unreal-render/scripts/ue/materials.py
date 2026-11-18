"""Materials made by script, with the flags that keep them from silently turning into the default material.

    m = materials.fresh("M_Neon")                     # <ROOT>/Materials/M_Neon, usage flags set
    col = materials.vector(m, "Color", (0.3, 0.8, 1.0), -600, 0)
    k = materials.scalar(m, "Strength", 18000.0, -600, 120)
    ...
    materials.finish(m)                               # recompile + save
    mi = materials.instance(m, "MI_Neon_Pink", vectors={"Color": (1, 0.2, 0.7)})   # saved too

Traps this guards against:
  * a material used on instanced static meshes (or Nanite meshes) needs bUsedWithInstancedStaticMeshes (and
    bUsedWithNanite): without it the game renderer swaps in the default material with only a "missing usage flag"
    line in the log. Every neon ring and sign in a city came out unlit before this.
  * material instances made by script are new assets: save them (instance() does), the level save does not.
  * emissive values are in real-world units at physical exposure: with EV exposure (ExtendDefaultLuminanceRange on),
    a lit window wants thousands, not 1-20. Calibrate against the scene's exposure with one test frame.
"""
import unreal
import ur

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
USAGE = ("used_with_instanced_static_meshes", "used_with_nanite")


def fresh(name, sub="Materials"):
    """a material with no expressions: made, or emptied if it exists (materials are code, rebuilt each run)"""
    ur.name(name)  # validates the characters
    base = ur.folder(sub)
    path = "%s/%s" % (base, name)
    if lib.does_asset_exist(path):
        m = lib.load_asset(path)
        mel.delete_all_material_expressions(m)
    else:
        m = tools.create_asset(name, base, unreal.Material, unreal.MaterialFactoryNew())
    for k in USAGE:
        try:
            m.set_editor_property(k, True)
        except Exception as e:
            ur.say("usage flag %s not set: %s" % (k, e))
    return m


def node(m, cls, x, y):
    return mel.create_material_expression(m, cls, x, y)


def scalar(m, pname, v, x, y):
    e = node(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", pname); e.set_editor_property("default_value", float(v))
    return e


def vector(m, pname, rgb, x, y):
    e = node(m, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", pname)
    e.set_editor_property("default_value", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return e


def custom(m, code, inputs, out_type, x, y):
    """an HLSL Custom node; inputs are names, connected afterwards with mel.connect_material_expressions"""
    e = node(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property("code", code); e.set_editor_property("output_type", out_type)
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", n); ins.append(ci)
    e.set_editor_property("inputs", ins)
    return e


def finish(m):
    mel.recompile_material(m)
    lib.save_loaded_asset(m)
    ur.say("material", m.get_path_name())
    return m


def emissive(name, rgb, strength):
    """an unlit emissive in a colour, e.g. neon trim; strength in real-world units (thousands at night exposure)"""
    m = fresh(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    col = vector(m, "Color", rgb, -600, 0); k = scalar(m, "Strength", strength, -600, 120)
    mul = node(m, unreal.MaterialExpressionMultiply, -300, 50)
    mel.connect_material_expressions(col, "", mul, "A"); mel.connect_material_expressions(k, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    return finish(m)


def instance(parent, name, scalars=None, vectors=None, sub="Materials"):
    """a material instance with parameters set, saved"""
    ur.name(name)
    base = ur.folder(sub)
    path = "%s/%s" % (base, name)
    mi = lib.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        name, base, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    for k, v in (scalars or {}).items():
        mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
    for k, v in (vectors or {}).items():
        mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    mel.update_material_instance(mi)
    lib.save_loaded_asset(mi)
    return mi
