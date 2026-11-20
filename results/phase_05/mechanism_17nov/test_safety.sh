#!/usr/bin/env bash
set -euo pipefail
cd /workspace
result_dir=$(mktemp -d results/phase_05/mechanism_17nov/sanitizer-XXXXXXXX)
gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer -g -Ifirmware/policy -Ifirmware/common -Ifirmware/aggregate firmware/policy/policy.c firmware/aggregate/aggregate.c tests/unit/test_policy_safety.c -o "$result_dir/test_policy_safety"
ASAN_OPTIONS=detect_leaks=1 "$result_dir/test_policy_safety"
sha256sum "$result_dir/test_policy_safety"
