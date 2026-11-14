#!/usr/bin/env bash
set -euo pipefail
cd /workspace
mkdir -p results/phase_02/unit
gcc -std=c11 -Wall -Wextra -Werror -pedantic -g -fsanitize=address,undefined -fno-omit-frame-pointer -Ifirmware/common -Ifirmware/aggregate firmware/common/protocol.c firmware/aggregate/aggregate.c tests/unit/test_core.c -o results/phase_02/unit/test_core
ASAN_OPTIONS=detect_leaks=1 results/phase_02/unit/test_core
python3 -m unittest discover -s tests/unit -p 'test_*.py' -v
