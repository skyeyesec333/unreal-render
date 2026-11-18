#!/usr/bin/env bash
# ue-remote.sh: drive headless Unreal on a Windows render PC over SSH from this machine.
#
#   ue-remote.sh setup                         copy ue.ps1 and the helpers to <work>/scripts; make args/ and logs/
#   ue-remote.sh check                         read-only: engine, project, plugins, exposure setting, GPU, disks, busy?
#   ue-remote.sh push <file.py|file.json>...   a build script to <work>/scripts, an arguments file to <work>/args
#   ue-remote.sh run <script.py> [<args.json>] [--timeout MIN] [--detach]
#   ue-remote.sh render <map> <sequence> <config> [--res WxH] [--timeout MIN] [--detach]
#   ue-remote.sh status                        is a job running, the last log lines and report
#   ue-remote.sh fetch <render-folder-name> <local-dest>          copy only; nothing on the PC is removed
#   ue-remote.sh fetch-log <file-name> <local-dest>               a report, log or .camera.json from <work>/logs
#
# Settings (environment): UR_HOST  the PC's SSH target (an ~/.ssh/config alias or user@host)
#                         UR_WORK  the work folder on the PC, forward slashes, no spaces, e.g. C:/Users/<you>/ue-work
# Every value sent to the PC is checked against a pattern first; remote output is printed as plain text only.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SKILL=$(cd "$HERE/.." && pwd)
die() { echo "ue-remote: $*" >&2; exit 2; }
clean() { LC_ALL=C tr -cd '[:print:]\n\t'; }

HOST=${UR_HOST:-}; WORK=${UR_WORK:-}
[ -n "$HOST" ] || die "set UR_HOST (the render PC's SSH target)"
[ -n "$WORK" ] || die "set UR_WORK (the work folder on the PC, e.g. C:/Users/<you>/ue-work)"
[[ $HOST =~ ^[A-Za-z0-9._@-]+$ && $HOST != -* ]] || die "UR_HOST: letters, digits, . _ - @ only, not starting with -"
[[ $WORK =~ ^[A-Za-z]:/[A-Za-z0-9._/-]+$ && $WORK != *..* ]] || die "UR_WORK: a drive path with forward slashes and no spaces, e.g. C:/Users/you/ue-work"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=30)
PS="powershell -NoProfile -ExecutionPolicy Bypass -File $WORK/scripts/ue.ps1"

rps() { "${SSH[@]}" -- "$HOST" "$PS $*" 2>&1 | clean; return "${PIPESTATUS[0]}"; }
need() { [ $# -ge 2 ] && [ -n "$2" ] || die "$1 needs a value"; }
asset_ok() { [[ $1 =~ ^/Game(/[A-Za-z0-9_][A-Za-z0-9_.-]*)+$ ]] || die "not an asset path like /Game/Folder/Name: $1"; }

cmd=${1:-}; [ -n "$cmd" ] || { sed -n '2,15p' "$0"; exit 2; }; shift
case $cmd in
  setup)
    "${SSH[@]}" -- "$HOST" "powershell -NoProfile -Command New-Item -ItemType Directory -Force -Path $WORK/scripts/ue,$WORK/args,$WORK/logs | Out-Null" 2>&1 | clean
    scp -q -o BatchMode=yes "$HERE/ue.ps1" "$HERE/export_camera.py" "$SKILL/examples/city_from_layout.py" "$HOST:$WORK/scripts/"
    scp -q -o BatchMode=yes "$HERE"/ue/*.py "$HOST:$WORK/scripts/ue/"
    echo "copied ue.ps1, export_camera.py, city_from_layout.py and the helpers to $WORK/scripts"
    echo "next: put ue.json in $WORK (see references/setup.md), then: ue-remote.sh check" ;;

  check)  rps -Mode check ;;
  status) rps -Mode status ;;

  push)
    [ $# -gt 0 ] || die "push <file>..."
    for f in "$@"; do
      [ -f "$f" ] || die "no such file: $f"
      b=$(basename -- "$f")
      case $b in
        *.py)   [[ $b =~ ^[A-Za-z0-9_-]+\.py$ ]] || die "script name: letters, digits, _ - only: $b"; dest="$WORK/scripts/" ;;
        *.json) [[ $b =~ ^[A-Za-z0-9_.-]+\.json$ && $b != -* ]] || die "args name: letters, digits, _ - . only: $b"; python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$f" || die "not valid JSON: $f"; dest="$WORK/args/" ;;
        *) die "push takes .py build scripts and .json argument files only: $b" ;;
      esac
      scp -q -o BatchMode=yes -- "$f" "$HOST:$dest" && echo "pushed $b -> $dest"
    done ;;

  run)
    [ $# -ge 1 ] || die "run <script.py> [<args.json>] [--timeout MIN] [--detach]"
    s=$1; shift; [[ $s =~ ^[A-Za-z0-9_-]+\.py$ ]] || die "script name: letters, digits, _ - only"
    extra=""
    if [ $# -gt 0 ] && [[ $1 != --* ]]; then
      [[ $1 =~ ^[A-Za-z0-9_.-]+\.json$ && $1 != -* ]] || die "args file name: letters, digits, _ - . only (push it first)"
      extra="-ArgsFile $WORK/args/$1"; shift
    fi
    while [ $# -gt 0 ]; do case $1 in
      --timeout) need "$@"; [[ $2 =~ ^[0-9]+$ ]] || die "--timeout minutes"; extra="$extra -TimeoutMin $2"; shift 2 ;;
      --detach) extra="$extra -Detach"; shift ;;
      *) die "unknown $1" ;; esac; done
    # shellcheck disable=SC2086  # $extra is built only from checked values and must split into flags
    rps -Mode script -Script "$s" $extra ;;

  render)
    [ $# -ge 3 ] || die "render <map> <sequence> <config> [--res WxH] [--timeout MIN] [--detach]"
    m=$1 q=$2 c=$3; shift 3; asset_ok "$m"; asset_ok "$q"; asset_ok "$c"
    extra=""
    while [ $# -gt 0 ]; do case $1 in
      --res) need "$@"; [[ $2 =~ ^([0-9]{2,4})x([0-9]{2,4})$ ]] || die "--res WxH"; extra="$extra -ResX ${BASH_REMATCH[1]} -ResY ${BASH_REMATCH[2]}"; shift 2 ;;
      --timeout) need "$@"; [[ $2 =~ ^[0-9]+$ ]] || die "--timeout minutes"; extra="$extra -TimeoutMin $2"; shift 2 ;;
      --detach) extra="$extra -Detach"; shift ;;
      *) die "unknown $1" ;; esac; done
    # shellcheck disable=SC2086  # as above
    rps -Mode render -Map "$m" -Sequence "$q" -Config "$c" $extra ;;

  fetch)
    [ $# -eq 2 ] || die "fetch <render-folder-name> <local-dest>"
    n=$1 dest=$2; [[ $n =~ ^[A-Za-z0-9_]+$ ]] || die "render folder name: letters, digits, _ only (as printed after RENDERS-TO)"
    root=$(rps -Mode renders | tr -d '\r' | sed -n 's/^renders //p' | head -1)
    [[ $root =~ ^[A-Za-z]:[/\\][A-Za-z0-9._/\\-]+$ ]] || die "could not read the renders folder from the PC"
    root=${root//\\//}
    if [ -e "$dest" ] && [ -n "$(ls -A -- "$dest" 2>/dev/null)" ]; then die "$dest exists and is not empty: pick a new folder"; fi
    mkdir -p -- "$dest"
    scp -r -q -o BatchMode=yes -- "$HOST:$root/$n" "$dest/" && echo "copied $root/$n -> $dest/$n (left on the PC)" ;;

  fetch-log)
    [ $# -eq 2 ] || die "fetch-log <file-name> <local-dest>"
    n=$1 dest=$2; [[ $n =~ ^[A-Za-z0-9_.-]+$ && $n != -* && $n != *..* ]] || die "file name: letters, digits, _ - . only"
    mkdir -p -- "$dest"
    scp -q -o BatchMode=yes -- "$HOST:$WORK/logs/$n" "$dest/" && echo "copied $n -> $dest/" ;;

  *) sed -n '2,15p' "$0"; exit 2 ;;
esac
