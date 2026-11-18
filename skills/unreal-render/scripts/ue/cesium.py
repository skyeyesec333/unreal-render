"""Optional: a real place under the scene with Cesium for Unreal (the plugin must be installed and enabled).

    geo = cesium.georeference(lon, lat)                    # the origin of the level at that spot
    cesium.tileset(geo, ion_asset_id, token_file)          # e.g. Google Photorealistic 3D Tiles through Cesium ion
    cesium.sun(geo, lon, lat, (2026, 11, 17), solar_hour=18.3, tz=7.0)
    p = cesium.to_unreal(geo, lon, lat, height_m)          # where a real place is, in Unreal cm

The ion token is read from a file you name (keep it outside every repo); it ends up stored in the level asset on the
PC, so never commit or share that project.

Traps:
  * set the georeference's STORED properties (origin_placement, origin_latitude/longitude/height) as well as calling
    the setter: the setter alone left the saved level at Cesium's default origin.
  * CesiumSunSky works out the sun from its own globe anchor, which starts at 0, 0: move the anchor to the site or the
    sun is where it would be off West Africa (a black sky at your afternoon).
  * aim cameras with to_unreal() on both ends: Cesium's frame at the origin is East +X, South +Y, Up +Z, and guessing
    the axes had the camera facing away from the target.
  * Google's 3D tiles carry the daylight they were photographed in: at night they render black, and a lit city has to
    come from your own geometry. Turn off world bounds checks (Cesium asks for it).
Licences: Cesium ion's free tier is for non-commercial use; Google's Photorealistic 3D Tiles through your own Google
key need a billing account. Check both before frames go on a commercial site.
"""
import os
import unreal
import ur


def georeference(lon, lat, height=0.0):
    geo = ur.spawn(unreal.CesiumGeoreference, label="Georeference", path="MyRenders/Geo")
    try:
        geo.set_editor_property("origin_placement", unreal.OriginPlacement.CARTOGRAPHIC_ORIGIN)
    except Exception as e:
        ur.say("origin placement: %s" % e)
    geo.set_editor_property("origin_latitude", float(lat))
    geo.set_editor_property("origin_longitude", float(lon))
    geo.set_editor_property("origin_height", float(height))
    geo.set_origin_longitude_latitude_height(unreal.Vector(float(lon), float(lat), float(height)))
    ur.say("georeference origin", geo.get_origin_longitude_latitude_height())
    try:
        ws = unreal.EditorLevelLibrary.get_editor_world().get_world_settings()
        ws.set_editor_property("enable_world_bounds_checks", False)
    except Exception as e:
        ur.say("world bounds checks not changed: %s" % e)
    return geo


def tileset(geo, ion_asset_id, token_file, label="Tiles"):
    if not os.path.isfile(token_file):
        raise SystemExit("token file not found: %s" % token_file)
    with open(token_file, encoding="utf-8") as f:
        token = f.read().strip()
    if not token or any(ch.isspace() for ch in token):
        raise SystemExit("token file must hold one token")
    t = ur.spawn(unreal.Cesium3DTileset, label=label, path="MyRenders/Geo")
    try:
        t.set_editor_property("georeference", geo)
    except Exception as e:
        ur.say("tileset georeference: %s" % e)
    t.set_editor_property("ion_asset_id", int(ion_asset_id))
    t.set_editor_property("ion_access_token", token)
    ur.say("tileset ion asset %d (token %d chars)" % (int(ion_asset_id), len(token)))
    return t


def sun(geo, lon, lat, date, solar_hour, tz):
    s = ur.spawn(unreal.CesiumSunSky, label="SunSky", path="MyRenders/Geo")
    anchor = s.get_component_by_class(unreal.CesiumGlobeAnchorComponent)
    anchor.set_editor_property("georeference", geo)
    anchor.move_to_longitude_latitude_height(unreal.Vector(float(lon), float(lat), 0.0))
    for k, v in dict(year=int(date[0]), month=int(date[1]), day=int(date[2]), solar_time=float(solar_hour), time_zone=float(tz)).items():
        try:
            s.set_editor_property(k, v)
        except Exception as e:
            ur.say("sunsky %s: %s" % (k, e))
    try:
        s.update_sun()
    except Exception as e:
        ur.say("update_sun: %s" % e)
    ur.say("sun anchor lat %.4f lon %.4f" % (anchor.get_latitude(), anchor.get_longitude()))
    return s


def to_unreal(geo, lon, lat, height_m):
    return geo.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(float(lon), float(lat), float(height_m)))
