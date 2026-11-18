#!/usr/bin/env python3
"""Will a measured job fit a shared machine's rules? Run before requesting anything.

  python3 fit_check.py budget.json --ram-limit 8 --gpu-free 10016 --gpu-margin 512 [--threads-limit 4]

budget.json is measure_job.py's (or measure_job.ps1's) summary. --ram-limit is the box's rule for guest jobs in GiB;
--gpu-free is the GPU memory free once the box has made room (MiB), --gpu-margin what its broker keeps back.
Exit 0 if everything fits, 1 if not, with what to ask the box's owner for. Standard library only."""
import argparse, json, sys
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("budget"); ap.add_argument("--ram-limit", type=float, required=True); ap.add_argument("--gpu-free", type=float); ap.add_argument("--gpu-margin", type=float, default=0.0); ap.add_argument("--threads-limit", type=int)
a = ap.parse_args(); b = json.load(open(a.budget)); ask = b["ask_for"]; ok = True
ram = ask.get("ram_gib")
if ram is None: print("RAM: not measured"); ok = False
elif ram > a.ram_limit: print("RAM: DOES NOT FIT. needs %s GiB (peak %s MiB in phase '%s'); the limit is %s GiB. Ask the owner for %s GiB, or do not run it there." % (ram, b["peak_ram_mib"], b.get("peak_ram_phase"), a.ram_limit, ram)); ok = False
else: print("RAM: fits (%s GiB of %s)" % (ram, a.ram_limit))
g = ask.get("gpu_mib")
if a.gpu_free is not None:
    if g is None: print("GPU memory: not measured")
    elif g + a.gpu_margin > a.gpu_free: print("GPU memory: DOES NOT FIT. needs %s MiB + %s margin; %s free" % (g, int(a.gpu_margin), int(a.gpu_free))); ok = False
    else: print("GPU memory: fits. Request %s MiB (%s + %s margin <= %s free)" % (g, g, int(a.gpu_margin), int(a.gpu_free)))
if a.threads_limit and (b.get("peak_processes") or 0) > a.threads_limit + 3:
    print("CPU: the job ran %s processes at once; the limit is %s threads. Pin it (taskset) and cap its workers before the run." % (b["peak_processes"], a.threads_limit))
if b.get("stopped_at_ram_cap"): print("NOTE: the measured run was stopped at its RAM cap, so the true peak is higher than recorded."); ok = False
sys.exit(0 if ok else 1)
