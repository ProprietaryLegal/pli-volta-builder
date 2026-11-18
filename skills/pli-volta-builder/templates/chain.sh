#!/bin/bash
# chain_<name>.sh TAG : one window. Stop what serves, run the arms in order (one change per boot, `off` first), return
# by the pair rule. The LAST LINE always says what serves, or exactly what does NOT serve and which commands may follow
# on the owner's word. No retries; an arm that fails is stopped and the chain goes on to the next arm and the way back.
set -u
TAG=${1:?TAG}; CONF=/path/to/build/window.conf; D="bash /path/to/build/window/window_driver.sh $CONF $TAG"
ARMS=${ARMS:-"off variantA variantB"}
last() { echo "CHAIN $TAG $1 $(date -u +%FT%TZ)"; exit "${2:-0}"; }
$D check || last "REFUSED: check failed; nothing done" 9
$D stop; rc=$?; [ $rc = 14 ] && last "Xid count changed: nothing more started; report to the owner" 14
[ $rc = 0 ] || last "STOPPED at stop (exit $rc); NOTHING SERVES; next, on the owner's word: $D servedefault" 20
results=""
for A in $ARMS; do
  $D boot "$A"; rc=$?
  [ $rc = 14 ] && last "Xid count changed during boot of $A: nothing more stopped or started" 14
  if [ $rc = 0 ]; then $D judge "$A"; rc=$?; [ $rc = 14 ] && last "Xid count changed during $A" 14; fi
  results="$results $A=$rc"
  $D stoparm "$A" || last "STOPPED: arm $A did not stop; NOTHING SERVES; results:$results" 20
  [ "$A" = off ] && [ $rc != 0 ] && { results="$results (off failed: the remaining arms have no reference)"; break; }
done
$D servestate || last "DONE arms:$results; the serving record is STALE: run the full check on the test port, then servedefault; NOTHING SERVES" 36
$D servedefault || last "DONE arms:$results; the serving boot FAILED; NOTHING SERVES; next, on the owner's word: the fallback" 30
last "DONE arms:$results (0 PASS, 33 FAIL, 34 INCONCLUSIVE, 30 boot); THE BUILD SERVES on its public port"
