"""Thousands of copies of a mesh in one draw: an instanced static mesh component on a PLAIN actor.

    a, c = instances.holder(mesh, [material], "Neon_Pink")
    instances.add(c, transforms)                              # list of unreal.Transform
    instances.add(c, transforms, custom=[[0.3], [0.9], ...])  # per-instance custom data, one list per instance

Traps this guards against:
  * a Blueprint actor holding the component re-runs its construction script on save and drops the materials, then the
    instances. A plain unreal.Actor with the component added to the actor itself (SubobjectDataSubsystem) keeps them.
  * setting num_custom_data_floats as a property empties the component. Add the instances first, then call
    set_num_custom_data_floats and set_custom_data_value.
  * per-instance writes are slow from Python (roughly 30 minutes for a million values): batch what you can, and only
    write custom data the material actually reads.
  * the mesh's material must have the instanced-mesh usage flag (materials.fresh sets it).
"""
import unreal
import ur

_sds = None


def holder(mesh, mats, label, folder_path="MyRenders/Instances", mobility=unreal.ComponentMobility.STATIC):
    global _sds
    if _sds is None:
        _sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    a = ur.spawn(unreal.Actor, label=label, path=folder_path)
    handles = _sds.k2_gather_subobject_data_for_instance(a)
    params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=unreal.InstancedStaticMeshComponent)
    _sds.add_new_subobject(params)
    c = a.get_component_by_class(unreal.InstancedStaticMeshComponent)
    if c is None:
        raise SystemExit("could not add an instanced mesh component to " + label)
    c.set_mobility(mobility)
    c.set_static_mesh(mesh)
    for i, m in enumerate(mats or []):
        if m:
            c.set_material(i, m)
    return a, c


def add(c, transforms, custom=None):
    """add instances (world space), then their custom data in the order the component needs"""
    if not transforms:
        return 0
    if custom:
        if len(custom) != len(transforms):
            raise SystemExit("custom data: one list per instance (%d for %d)" % (len(custom), len(transforms)))
        if c.get_instance_count():
            raise SystemExit("custom data: give a component all its instances in one add() (only tried that way)")
    c.add_instances(transforms, False, True)
    if custom:
        n = len(custom[0])
        c.set_num_custom_data_floats(n)
        for i, vals in enumerate(custom):
            for j in range(n):
                c.set_custom_data_value(i, j, float(vals[j]), False)
    return len(transforms)


def xf(x, y, z, roll=0.0, pitch=0.0, yaw=0.0, sx=1.0, sy=1.0, sz=1.0):
    """a transform in Unreal units (centimetres)"""
    return unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(roll, pitch, yaw), unreal.Vector(sx, sy, sz))
