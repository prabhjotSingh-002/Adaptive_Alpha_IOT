#!/usr/bin/env bash
set -euo pipefail
cd /workspace
exec 9>results/phase_02/.runner.lock
flock -n 9
output_dir=$(mktemp -d results/phase_04/unit/energy-XXXXXXXX)
printf 'Artifacts: %s\n' "$output_dir"
gcc -std=c11 -Wall -Wextra -Werror -pedantic -g -fsanitize=address,undefined -fno-omit-frame-pointer -Ifirmware/energy firmware/energy/energy.c tests/unit/test_energy.c -o "$output_dir/test_energy"
ASAN_OPTIONS=detect_leaks=1 "$output_dir/test_energy"
