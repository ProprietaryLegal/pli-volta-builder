#!/bin/bash
# Runs every script's hand-worked self-test and the driver's CPU test. CPU only, Python 3 standard library and bash.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
S="$HERE/../scripts"
fails=0
for s in hill_climb identity_judge closeness_judge speed_band log_patterns serving_record mem_sampler timebudget_parse boundary_check; do
  if python3 "$S/$s.py" --self-test >/tmp/pvb-selftest.$$ 2>&1; then echo "PASS $s"; else echo "FAIL $s"; cat /tmp/pvb-selftest.$$; fails=$((fails+1)); fi
done
rm -f /tmp/pvb-selftest.$$
if timeout 120 bash "$HERE/test_window_driver.sh" >/dev/null 2>&1; then echo "PASS window_driver"; else echo "FAIL window_driver (run tests/test_window_driver.sh to see why)"; fails=$((fails+1)); fi
[ $fails = 0 ] && echo "ALL PASS" || echo "$fails FAILED"
exit $fails
