#!/usr/bin/env python3
"""Numbers that tell a rendered night frame from a photograph. Run it on your frames AND on your reference photographs:
the targets are whatever the photographs measure, not numbers from memory.

  python3 frame_stats.py frame-0.png frame-8.png ref/boat.jpg
  python3 frame_stats.py --box 640,960,1300,1080 frame-0.png ref/boat.jpg     # one region only (x0,y0,x1,y1)

Per image: size; share of pixels above 230 and above 200 (what clips: lamps, signs, their reflections); the 99th, 50th
and 10th percentile of brightness; share under 8 (pure black: no air); the mean of the top 8% of rows as "sky" and its
red over blue. Needs numpy and Pillow."""
import sys
import numpy as np
from PIL import Image

def stats(path, box=None):
    im = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
    if box: im = im[box[1]:box[3], box[0]:box[2]]
    g = 0.299 * im[..., 0] + 0.587 * im[..., 1] + 0.114 * im[..., 2]
    h, w = g.shape
    top = im[:max(1, int(h * 0.08))].reshape(-1, 3).mean(0)
    return dict(name=path.split("/")[-1], w=w, h=h, over230=(g > 230).mean() * 100, over200=(g > 200).mean() * 100,
                p99=np.percentile(g, 99), p50=np.percentile(g, 50), p10=np.percentile(g, 10), black=(g < 8).mean() * 100,
                sky=top.mean(), rb=top[0] / max(top[2], 0.1))

def main(argv):
    box = None
    if argv and argv[0] == "--box": box = [int(v) for v in argv[1].split(",")]; argv = argv[2:]
    if not argv: print(__doc__); return 1
    print("%-28s %9s  %7s %7s  %4s %4s %4s  %6s  %5s %5s" % ("image", "size", ">230 %", ">200 %", "p99", "p50", "p10", "<8 %", "sky", "R/B"))
    for p in argv:
        s = stats(p, box)
        print("%-28s %4dx%-4d  %7.2f %7.2f  %4.0f %4.0f %4.0f  %6.1f  %5.1f %5.2f" % (s["name"][:28], s["w"], s["h"], s["over230"], s["over200"],
              s["p99"], s["p50"], s["p10"], s["black"], s["sky"], s["rb"]))
    return 0

if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
