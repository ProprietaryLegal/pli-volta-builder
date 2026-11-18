#!/bin/bash
# window_driver.sh CONF TAG PHASE [ARM] : a skeleton of the test-window driver. One pass per phase, no retries,
# no fallbacks. Fill CONF (templates/window.conf) for your server; keep everything machine-specific there.
#
# PHASES
#   check            read-only: CONF complete, the arm files exist, the Xid count readable. Starts nothing.
#   stop             stop what serves (STOP_SERVING_CMD); the cards must read empty (CARDS_EMPTY_CMD exits 0).
#   boot ARM         start ARM on the TEST port (arms/ARM.env holds its switches; every new switch default-off),
#                    wait for health up to BOOT_TIMEOUT_S, then run arms/ARM.bootchecks (one check per line).
#   judge ARM        run arms/ARM.lines: one acceptance line per row, "NAME<TAB>COMMAND". The lines were written
#                    into the plan BEFORE this window's data. COMMAND exit 0 = PASS, 1 = FAIL, 3 = INCONCLUSIVE,
#                    anything else = INCONCLUSIVE (a tool that did not finish is not a pass).
#   stoparm ARM      stop ARM (STOP_ARM_CMD), cards empty.
#   servestate       the serving record against the configuration now (scripts/serving_record.py check).
#   servedefault     boot the serving configuration on the PUBLIC port, only on a MATCHING record; send no request.
#
# EXIT CODES (each phase appends one line "WIN-<TAG> <PHASE> EXIT=<n> (<reason>)" to LOG_DIR/<TAG>/phases.log)
#   0 done | 9 usage or a precondition (nothing done) | 14 the Xid count changed: STOP HERE, start nothing, stop
#   nothing more, report to the owner (crash rule) | 20 a stop failed | 30 a boot or a boot check failed |
#   33 an acceptance line FAILED | 34 an acceptance line INCONCLUSIVE | 36 the serving record is stale (the full
#   check is owed on the test port before anything serves)
#
# RULES THIS SKELETON KEEPS (references/standing-rules.md says why)
#   - A boot timeout is a failure (30) with the log's tail printed; do not raise the limit, find the cause.
#   - Nothing is booted twice in one window: a failed arm is stopped and the chain moves on or returns.
#   - The Xid count is read before and after every phase.
#   - Never edit this file while a window runs it: install a new copy under a new name and switch the chain.
#   - Every pattern a boot check applies to a log was first run on a real log (scripts/log_patterns.py certify).
set -u -o pipefail

CONF=${1:?usage: window_driver.sh CONF TAG PHASE [ARM]}
TAG=${2:?TAG}
PHASE=${3:?PHASE}
ARM=${4:-}
# shellcheck source=/dev/null
source "$CONF" || { echo "cannot read $CONF"; exit 9; }
HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$LOG_DIR/$TAG"
mkdir -p "$OUT"

end() {  # end EXIT REASON
  local line
  line="WIN-$TAG $PHASE${ARM:+ $ARM} EXIT=$1 ($2) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "$line" | tee -a "$OUT/phases.log"
  exit "$1"
}

need() { for v in "$@"; do [ -n "${!v:-}" ] || end 9 "CONF lacks $v"; done; }
need LOG_DIR XID_COUNT_CMD START_ARM_CMD STOP_ARM_CMD HEALTH_CMD BOOT_TIMEOUT_S CARDS_EMPTY_CMD TEST_PORT SERVE_PORT

xid_now() { bash -c "$XID_COUNT_CMD"; }
XID0=$(xid_now) || end 9 "the Xid count cannot be read"
xid_guard() {
  local now
  now=$(xid_now) || end 14 "the Xid count cannot be read any more"
  [ "$now" = "$XID0" ] || end 14 "Xid count changed $XID0 -> $now: stop nothing more, start nothing, report"
}

arm_file() { [ -n "$ARM" ] || end 9 "phase $PHASE needs an ARM"; [ -f "$ARMS_DIR/$ARM.$1" ] || end 9 "missing $ARMS_DIR/$ARM.$1"; }

case "$PHASE" in
  check)
    [ -d "${ARMS_DIR:-}" ] || end 9 "ARMS_DIR missing"
    end 0 "configuration complete; Xid count $XID0"
    ;;
  stop)
    bash -c "${STOP_SERVING_CMD:?}" >>"$OUT/stop.log" 2>&1 || end 20 "the serving stop command failed"
    bash -c "$CARDS_EMPTY_CMD" || end 20 "cards not empty after the stop"
    xid_guard
    end 0 "stopped; cards empty"
    ;;
  boot)
    arm_file env
    arm_file bootchecks
    [ -e "$OUT/booted.$ARM" ] && end 9 "arm $ARM was already booted in window $TAG: nothing is booted twice"
    touch "$OUT/booted.$ARM"
    ( set -a; source "$ARMS_DIR/$ARM.env"; set +a; PORT=$TEST_PORT bash -c "$START_ARM_CMD" ) >"$OUT/$ARM.boot.log" 2>&1 &
    t0=$(date +%s)
    until bash -c "PORT=$TEST_PORT $HEALTH_CMD" >/dev/null 2>&1; do
      xid_guard
      if [ $(( $(date +%s) - t0 )) -ge "$BOOT_TIMEOUT_S" ]; then
        tail -n 30 "$OUT/$ARM.boot.log"
        end 30 "no health after ${BOOT_TIMEOUT_S}s: find the cause (log tail above); do not raise the limit"
      fi
      sleep 2
    done
    n=0
    while IFS= read -r chk; do
      [ -z "$chk" ] || [ "${chk:0:1}" = "#" ] && continue
      n=$((n + 1))
      BOOT_LOG="$OUT/$ARM.boot.log" bash -c "$chk" >>"$OUT/$ARM.bootchecks.out" 2>&1 || end 30 "boot check $n failed: $chk"
    done <"$ARMS_DIR/$ARM.bootchecks"
    xid_guard
    end 0 "booted on :$TEST_PORT in $(( $(date +%s) - t0 ))s; $n boot check(s) PASS"
    ;;
  judge)
    arm_file lines
    worst=0; fails=""; inconc=""
    while IFS=$'\t' read -r name cmd; do
      [ -z "$name" ] || [ "${name:0:1}" = "#" ] && continue
      PORT=$TEST_PORT bash -c "$cmd" >"$OUT/$ARM.line-$name.out" 2>&1
      rc=$?
      case $rc in
        0) echo "line $name PASS" ;;
        1) echo "line $name FAIL"; fails="$fails $name" ;;
        *) echo "line $name INCONCLUSIVE (exit $rc)"; inconc="$inconc $name" ;;
      esac
      xid_guard
    done <"$ARMS_DIR/$ARM.lines"
    [ -n "$fails" ] && end 33 "FAIL:$fails${inconc:+; INCONCLUSIVE:$inconc}"
    [ -n "$inconc" ] && end 34 "INCONCLUSIVE:$inconc (not a pass)"
    end 0 "every line PASS"
    ;;
  stoparm)
    [ -n "$ARM" ] || end 9 "stoparm needs an ARM"
    PORT=$TEST_PORT bash -c "$STOP_ARM_CMD" >>"$OUT/stop.log" 2>&1 || end 20 "the arm's stop failed"
    bash -c "$CARDS_EMPTY_CMD" || end 20 "cards not empty after stopping $ARM"
    xid_guard
    end 0 "arm $ARM stopped"
    ;;
  servestate)
    python3 "$HERE/serving_record.py" check "${SERVE_CONFIG_JSON:?}" "${SERVE_RECORD:?}"
    rc=$?
    [ $rc -eq 0 ] && end 0 "record MATCH"
    end 36 "record stale or missing: the full check is owed on :$TEST_PORT"
    ;;
  servedefault)
    python3 "$HERE/serving_record.py" check "${SERVE_CONFIG_JSON:?}" "${SERVE_RECORD:?}" || end 36 "no matching record: refuse to serve"
    ( PORT=$SERVE_PORT bash -c "${START_SERVING_CMD:?}" ) >"$OUT/serving.boot.log" 2>&1 &
    t0=$(date +%s)
    until bash -c "PORT=$SERVE_PORT $HEALTH_CMD" >/dev/null 2>&1; do
      xid_guard
      [ $(( $(date +%s) - t0 )) -ge "$BOOT_TIMEOUT_S" ] && { tail -n 30 "$OUT/serving.boot.log"; end 30 "the serving boot has no health"; }
      sleep 2
    done
    end 0 "serving on :$SERVE_PORT from a matching record (no request sent)"
    ;;
  *) end 9 "unknown phase $PHASE" ;;
esac
