#!/usr/bin/env bash
set -euo pipefail
cd /workspace
mkdir -p results/phase_03/unit
gcc -std=c11 -Wall -Wextra -Werror -pedantic -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Itests/security/support -Iexternal/contiki-ng/os -Ifirmware/crypto \
  firmware/crypto/aes_ccm.c external/contiki-ng/os/lib/ccm-star.c \
  external/contiki-ng/os/lib/aes-128.c tests/security/test_aes_ccm.c \
  -o results/phase_03/unit/test_aes_ccm
ASAN_OPTIONS=detect_leaks=1 results/phase_03/unit/test_aes_ccm
gcc -std=c11 -Wall -Wextra -Werror -pedantic -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Itests/security/support -Iexternal/contiki-ng/os -Ifirmware/crypto -Ifirmware/common \
  firmware/crypto/aes_ccm.c firmware/crypto/secure_packet.c firmware/common/protocol.c \
  external/contiki-ng/os/lib/ccm-star.c external/contiki-ng/os/lib/aes-128.c \
  tests/security/test_secure_packet.c -o results/phase_03/unit/test_secure_packet
ASAN_OPTIONS=detect_leaks=1 results/phase_03/unit/test_secure_packet
