#!/usr/bin/env python3
"""A real district's layout for an Unreal city, from OpenStreetMap (data © OpenStreetMap contributors, ODbL: credit it
wherever the renders are shown). Runs on your own machine, not in Unreal.

  1. Download buildings and streets for a small box from Overpass (the query is overpass-query.txt; paste it at
     https://overpass-turbo.eu with your box, Export > raw data, or POST it to an Overpass API endpoint you are allowed
     to use). Keep the box small: a couple of km across is already ~10,000 buildings.
  2. python3 osm_layout.py overpass.json layout.json --origin LON,LAT
     -> {"origin": [lon, lat], "buildings": [{x, y, w, d, yaw, h, src}], "roads": [{kind, pts}]}
     in local metres round the origin (x east, y north). Each footprint becomes its best-fitting rotated rectangle;
     the height is the mapped height, else floors x 3.4 m, else an estimate from the footprint's size.
  3. Copy layout.json to the PC's args folder and run city_from_layout.py through ue.ps1.
"""
import argparse, json, math, re, sys


def number(s):
    m = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", s or "")
    return float(m.group(1)) if m else None


def obb(pts):
    """the minimum-area rectangle round a polygon, trying each edge's direction"""
    best = None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        a = math.atan2(y1 - y0, x1 - x0); ca, sa = math.cos(a), math.sin(a)
        us = [x * ca + y * sa for x, y in pts]; vs = [-x * sa + y * ca for x, y in pts]
        area = (max(us) - min(us)) * (max(vs) - min(vs))
        if best is None or area < best[0]:
            cu, cv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
            best = (area, cu * ca - cv * sa, cu * sa + cv * ca, max(us) - min(us), max(vs) - min(vs), math.degrees(a))
    _, cx, cy, w, d, yaw = best
    if d > w:
        w, d, yaw = d, w, yaw + 90
    return cx, cy, w, d, yaw


def estimate(w, d, x, y):
    """a height for an unmapped building, varied but repeatable: small footprints low, large ones taller"""
    area = w * d
    jitter = abs(x * 7 + y * 13) % 1.0
    if area < 120: return 7 + 6 * jitter
    if area < 600: return 12 + 20 * jitter
    if area < 2500: return 20 + 40 * jitter
    return 40 + 120 * jitter


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("overpass_json"); ap.add_argument("out_json")
    ap.add_argument("--origin", required=True, help="LON,LAT of the level's origin")
    ap.add_argument("--min-size", type=float, default=2.0, help="skip footprints narrower than this (m)")
    a = ap.parse_args()
    try:
        lon0, lat0 = (float(v) for v in a.origin.split(","))
    except ValueError:
        sys.exit("--origin must be LON,LAT")
    if not (-180 <= lon0 <= 180 and -90 <= lat0 <= 90):
        sys.exit("--origin out of range")
    my = 111320.0; mx = 111320.0 * math.cos(math.radians(lat0))
    local = lambda lon, lat: ((lon - lon0) * mx, (lat - lat0) * my)

    with open(a.overpass_json, encoding="utf-8") as f:
        d = json.load(f)
    buildings, roads = [], []
    for e in d.get("elements", []):
        t = e.get("tags", {}); g = e.get("geometry")
        if not g: continue
        pts = [local(p["lon"], p["lat"]) for p in g]
        if "building" in t and len(pts) >= 4:
            if pts[0] == pts[-1]: pts = pts[:-1]
            cx, cy, w, dd, yaw = obb(pts)
            if dd < a.min_size: continue
            h = number(t.get("height")); src = "height"
            if h is None and number(t.get("building:levels")) is not None:
                h = number(t.get("building:levels")) * 3.4; src = "levels"
            if h is None:
                h = estimate(w, dd, cx, cy); src = "estimate"
            buildings.append(dict(x=round(cx, 1), y=round(cy, 1), w=round(w, 1), d=round(dd, 1), yaw=round(yaw, 1), h=round(h, 1), src=src))
        elif "highway" in t:
            roads.append(dict(kind=t["highway"], pts=[[round(x, 1), round(y, 1)] for x, y in pts]))

    with open(a.out_json, "w", encoding="utf-8") as f:
        json.dump(dict(origin=[lon0, lat0], buildings=buildings, roads=roads), f)
    src = {k: sum(1 for b in buildings if b["src"] == k) for k in ("height", "levels", "estimate")}
    print(f"{len(buildings)} buildings {src}, {len(roads)} roads -> {a.out_json}")


if __name__ == "__main__":
    main()
