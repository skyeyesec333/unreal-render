#!/usr/bin/env python3
"""Measure what a job really needs before asking a shared machine for it: system RAM, GPU memory, CPU load, by phase.

Run it ON THE WORKER, around the smallest real job (one frame of a test level, not the whole sequence):

  python3 measure_job.py --label lm-test --out budget.json -- <command and its arguments>
  python3 measure_job.py --label lm-test --ram-cap 22 --out budget.json -- <command ...>     # kill the job's whole tree at 22 GiB
  python3 measure_job.py --mark "Movie Pipeline" --log Saved/Logs/Project.log ...            # name a phase when this text appears in a log

Every few seconds it adds up the memory of the command and everything it started (shader workers included), reads the
GPU (nvidia-smi, if there is one), and the machine's load. It writes the samples as CSV beside the output and a summary:
peak RAM and when, peak GPU memory, peak per phase, and a suggested allowance (peak plus 15%, rounded up).

Why: a render that fits the GPU can still take a machine down by its system RAM. A project that loads a large sample
(tens of GB of content) may need 20 GiB of RAM for a level whose frames use 6 GB of GPU memory, and the first run on a
machine compiles shaders with one worker per core. Measure on a machine you own, or under --ram-cap on a shared one,
BEFORE requesting a lane; request what was measured, not a guess.

POSIX only (Linux, macOS). On Windows use measure_job.ps1. Standard library only."""
import argparse, json, math, os, signal, subprocess, sys, time

def tree(root):
    """pids of root and all its descendants, with their resident memory in KiB"""
    out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True).stdout
    kids, rss = {}, {}
    for line in out.splitlines():
        try: pid, ppid, r = (int(v) for v in line.split())
        except ValueError: continue
        kids.setdefault(ppid, []).append(pid); rss[pid] = r
    todo, seen = [root], []
    while todo:
        p = todo.pop()
        if p in seen: continue
        seen.append(p); todo += kids.get(p, [])
    return seen, sum(rss.get(p, 0) for p in seen)

def gpu(pids):
    """(MiB used by these pids, MiB used on the whole first GPU) or (None, None) without nvidia-smi"""
    try:
        whole = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout.split()
        apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout
        mine = 0
        for line in apps.splitlines():
            try: pid, m = (int(v) for v in line.replace(" ", "").split(","))
            except ValueError: continue
            if pid in pids: mine += m
        return mine, int(whole[0]) if whole else None
    except Exception:
        return None, None

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="job"); ap.add_argument("--out", default="budget.json"); ap.add_argument("--every", type=float, default=5.0)
    ap.add_argument("--ram-cap", type=float, help="GiB: stop the job's whole process tree if it passes this")
    ap.add_argument("--log", help="a log file the job writes, to name phases from"); ap.add_argument("--mark", action="append", default=[], help="text in --log that starts a new phase (repeatable)")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(); cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd: ap.error("give the command after --")
    child = subprocess.Popen(cmd, start_new_session=True); t0 = time.time()
    rows, phase, seen_marks, capped = [], "start", set(), False
    csv = open(os.path.splitext(a.out)[0] + ".csv", "w"); csv.write("seconds,phase,ram_mib,gpu_job_mib,gpu_all_mib,load1,processes\n")
    while child.poll() is None:
        pids, kib = tree(child.pid); g_job, g_all = gpu(pids)
        try: load = os.getloadavg()[0]
        except OSError: load = 0.0
        if a.log and a.mark and os.path.exists(a.log):
            try: text = open(a.log, errors="ignore").read()
            except OSError: text = ""
            for m in a.mark:
                if m not in seen_marks and m in text: seen_marks.add(m); phase = m
        row = dict(t=round(time.time() - t0), phase=phase, ram=kib // 1024, gpu_job=g_job, gpu_all=g_all, load=round(load, 1), n=len(pids)); rows.append(row)
        csv.write("%(t)s,%(phase)s,%(ram)s,%(gpu_job)s,%(gpu_all)s,%(load)s,%(n)s\n" % row); csv.flush()
        if a.ram_cap and kib / 1048576 > a.ram_cap:
            capped = True
            try: os.killpg(child.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError): pass
            time.sleep(8)
            try: os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError): pass       # already gone (macOS answers "not permitted" for a group that has just exited)
            break
        time.sleep(a.every)
    code = child.wait(); csv.close()
    def peak(key, rs): vals = [r[key] for r in rs if r[key] is not None]; return max(vals) if vals else None
    phases = {}
    for r in rows: phases.setdefault(r["phase"], []).append(r)
    top = max(rows, key=lambda r: r["ram"]) if rows else None
    up = lambda v, step: None if v is None else int(math.ceil(v * 1.15 / step) * step)
    s = dict(label=a.label, command=" ".join(cmd), exit_code=code, seconds=round(time.time() - t0), stopped_at_ram_cap=capped,
             peak_ram_mib=peak("ram", rows), peak_ram_at_seconds=top["t"] if top else None, peak_ram_phase=top["phase"] if top else None,
             peak_gpu_job_mib=peak("gpu_job", rows), peak_gpu_all_mib=peak("gpu_all", rows), peak_load=peak("load", rows), peak_processes=peak("n", rows),
             by_phase={k: dict(peak_ram_mib=peak("ram", v), peak_gpu_job_mib=peak("gpu_job", v), seconds=v[-1]["t"] - v[0]["t"]) for k, v in phases.items()},
             ask_for=dict(ram_gib=None if not rows else math.ceil(peak("ram", rows) * 1.15 / 1024), gpu_mib=up(peak("gpu_job", rows) or peak("gpu_all", rows), 256)),
             note="ask_for is the peak plus 15%. A first run on a machine also compiles shaders: measure a second run for the steady figure.")
    json.dump(s, open(a.out, "w"), indent=1)
    print("%s: exit %s in %ss%s" % (a.label, code, s["seconds"], "  STOPPED at the RAM cap" if capped else ""))
    print("  RAM peak %s MiB (%s, at %ss)   GPU peak %s MiB (job) / %s MiB (card)   load %s   processes %s" % (s["peak_ram_mib"], s["peak_ram_phase"], s["peak_ram_at_seconds"], s["peak_gpu_job_mib"], s["peak_gpu_all_mib"], s["peak_load"], s["peak_processes"]))
    print("  ask for: %s GiB RAM, %s MiB GPU memory   ->  %s" % (s["ask_for"]["ram_gib"], s["ask_for"]["gpu_mib"], a.out))
    return code

if __name__ == "__main__": sys.exit(main())
