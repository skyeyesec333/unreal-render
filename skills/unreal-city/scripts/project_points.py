#!/usr/bin/env python3
"""Where do things fall in a camera's frame? For finding what lies under a fault, whether a landmark is hidden, and
what a frame should contain that it does not. Everything is in the scene's own frame: metres, x east, y north, z up.

  # named points
  python3 project_points.py --cam -455,40,70 --aim -720,360,110 --focal 20  tower_top=-757,393,318 spire=-3094,2183,79

  # every mapped building the camera should see within 300 m (layout.json: buildings with x, y, w, d, h)
  python3 project_points.py --cam -560,-800,38 --aim -468,-731,8 --focal 28 --layout layout.json --within 300

Prints pixel x, y (origin top left) and the distance along the view. A point outside 0..width, 0..height is off frame.
Two things at nearly the same pixel: the nearer one hides the other. --sensor is the filmback width in mm (default 36),
--size the frame (default 1920x1080). Standard library only."""
import argparse, json, math

def camera(cam, aim, focal, sensor, w, h):
    sub = lambda a, b: tuple(x - y for x, y in zip(a, b)); dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    cross = lambda a, b: (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    unit = lambda a: tuple(x / math.sqrt(dot(a, a)) for x in a)
    fw = unit(sub(aim, cam)); rt = unit(cross(fw, (0, 0, 1))); up = cross(rt, fw); k = focal / sensor * w
    def project(p):
        d = sub(p, cam); z = dot(d, fw)
        if z < 0.5: return None
        return (w / 2 + dot(d, rt) / z * k, h / 2 - dot(d, up) / z * k, z)
    return project

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    v3 = lambda s: tuple(float(v) for v in s.split(","))
    ap.add_argument("--cam", type=v3, required=True); ap.add_argument("--aim", type=v3, required=True)
    ap.add_argument("--focal", type=float, default=20.0); ap.add_argument("--sensor", type=float, default=36.0)
    ap.add_argument("--size", default="1920x1080"); ap.add_argument("--layout"); ap.add_argument("--within", type=float, default=300.0)
    ap.add_argument("points", nargs="*")
    import sys
    argv = sys.argv[1:]; fixed = []                                   # "--cam -455,40,70": a leading minus is a number here, not an option
    while argv:
        t = argv.pop(0)
        if t in ("--cam", "--aim") and argv: t = t + "=" + argv.pop(0)
        fixed.append(t)
    a = ap.parse_args(fixed); w, h = (int(v) for v in a.size.split("x")); P = camera(a.cam, a.aim, a.focal, a.sensor, w, h)
    for item in a.points:
        name, xyz = item.split("="); p = P(v3(xyz))
        print("%-18s %s" % (name, "behind the camera" if p is None else "x %6.0f  y %6.0f  at %6.0f m%s" % (p[0], p[1], p[2], "" if 0 <= p[0] <= w and 0 <= p[1] <= h else "  (off frame)")))
    if a.layout:
        rows = []
        for b in json.load(open(a.layout))["buildings"]:
            if math.dist((b["x"], b["y"]), a.cam[:2]) > a.within: continue
            foot, top = P((b["x"], b["y"], 0.0)), P((b["x"], b["y"], b.get("h", 10.0)))
            if foot and -0.2 * w <= foot[0] <= 1.2 * w: rows.append((foot[2], b, foot, top))
        print("%d mapped buildings within %.0f m that the camera faces, nearest first:" % (len(rows), a.within))
        for z, b, foot, top in sorted(rows, key=lambda r: r[0]):
            print("  at %5.0f m  foot x %5.0f y %5.0f  top y %5.0f  %3.0fx%-3.0f h %-4.0f  (%.0f, %.0f)  %s" % (z, foot[0], foot[1], top[1] if top else -1,
                  b["w"], b["d"], b.get("h", 0), b["x"], b["y"], b.get("name") or ""))

if __name__ == "__main__": main()
