#!/bin/bash
# CPU test of scripts/window_driver.sh with a fake "server" (a sleep process) and a fake Xid counter (a file).
# Expected exit codes are the ones the driver's header defines; each case says why by hand.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
D=$(mktemp -d)
trap 'kill $(cat "$D/pid" 2>/dev/null) 2>/dev/null; rm -rf "$D"' EXIT
DRV="$HERE/../scripts/window_driver.sh"
mkdir -p "$D/arms" "$D/logs"
echo 4 >"$D/xid"
cat >"$D/window.conf" <<EOF
LOG_DIR=$D/logs
ARMS_DIR=$D/arms
TEST_PORT=18001
SERVE_PORT=18000
XID_COUNT_CMD="cat $D/xid"
START_ARM_CMD="sleep 60 & echo \\\$! > $D/pid; wait"
STOP_ARM_CMD="kill \\\$(cat $D/pid)"
STOP_SERVING_CMD="true"
HEALTH_CMD="test -s $D/pid"
CARDS_EMPTY_CMD="true"
BOOT_TIMEOUT_S=5
EOF
printf 'SWITCH_X=0\n' >"$D/arms/off.env"
printf '# boot checks\ngrep -q . %s/pid\n' "$D" >"$D/arms/off.bootchecks"
printf 'ok\ttrue\n' >"$D/arms/off.lines"
printf 'SWITCH_X=1\n' >"$D/arms/bad.env"
printf 'false\n' >"$D/arms/bad.bootchecks"
printf 'ident\ttrue\nspeed\texit 3\n' >"$D/arms/inc.lines"
printf 'ident\texit 1\nspeed\texit 3\n' >"$D/arms/fail.lines"

fails=0
expect() {  # expect WANT DESCRIPTION -- args
  local want=$1 what=$2; shift 3
  bash "$DRV" "$D/window.conf" "$@" >"$D/out" 2>&1
  local got=$?
  if [ "$got" = "$want" ]; then echo "ok   $what: exit $got"; else echo "FAIL $what: exit $got, want $want"; cat "$D/out"; fails=$((fails+1)); fi
}
expect 0  "check passes on a complete configuration" -- w1 check
expect 9  "unknown phase is a usage error" -- w1 nonsense
expect 0  "boot of arm off: health, one boot check" -- w1 boot off
expect 9  "the same arm is never booted twice in a window" -- w1 boot off
expect 0  "judge: one line PASS" -- w1 judge off
expect 0  "stoparm" -- w1 stoparm off
rm -f "$D/pid"
expect 30 "a failing boot check stops the arm's boot (30)" -- w1 boot bad
kill "$(cat "$D/pid" 2>/dev/null)" 2>/dev/null; rm -f "$D/pid"
expect 34 "a line that exits 3 is INCONCLUSIVE (34), not a pass" -- w1 judge inc
expect 33 "FAIL decides before INCONCLUSIVE (33)" -- w1 judge fail
# Xid changes during a phase: the counter file changes before the judge's guard reads it
printf 'flip\techo 5 > %s/xid\n' "$D" >"$D/arms/xid.lines"
expect 14 "an Xid change ends the phase with 14" -- w1 judge xid
echo 4 >"$D/xid"
lines=$(grep -c "^WIN-w1 " "$D/logs/w1/phases.log")
[ "$lines" = 10 ] && echo "ok   one phases.log line per phase ($lines)" || { echo "FAIL phases.log has $lines lines, want 10"; fails=$((fails+1)); }
[ $fails = 0 ] && echo "window_driver test: PASS" || echo "window_driver test: $fails FAILED"
exit $fails
