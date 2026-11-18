#!/bin/sh
# Start a command when something else has finished, without the classic mistake: a loop that greps the process list
# for the first job's command line also matches ITSELF (its own command line holds the same words, because it is about
# to run them) and waits for ever. So this waits on things the waiter does not contain.
#
#   queue_after.sh --file <path> -- <command...>              start when <path> exists (e.g. the first job's last output)
#   queue_after.sh --remote <user@host> <name> -- <command>   start when no process named <name>* runs on that machine
#                                                             (Windows over OpenSSH, or anything with pgrep)
#   queue_after.sh --pid <pid> -- <command...>                start when that local process has gone
#
# Simplest of all, when you start both jobs yourself: run them in one shell,  first ; second
set -eu
mode=$1; shift
case "$mode" in
  --file) target=$1; shift ;;
  --pid) target=$1; shift ;;
  --remote) host=$1; target=$2; shift 2 ;;
  *) sed -n '2,12p' "$0"; exit 2 ;;
esac
[ "$1" = "--" ] && shift
busy() {
  case "$mode" in
    --file) [ ! -e "$target" ] ;;
    --pid) kill -0 "$target" 2>/dev/null ;;
    --remote) n=$(ssh -o ConnectTimeout=10 "$host" "tasklist 2>NUL | findstr /i /b \"$target\" || pgrep -f \"^[^ ]*$target\" 2>/dev/null" 2>/dev/null | wc -l); [ "$n" -gt 0 ] ;;
  esac
}
while busy; do sleep 10; done
sleep 10            # let the first job's last files land
exec "$@"
