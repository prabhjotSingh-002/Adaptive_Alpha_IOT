#!/usr/bin/env bash
set -euo pipefail
cd /workspace
exec 9>results/phase_02/.runner.lock
flock -n 9 || { echo "Another writer owns generated config/build directories" >&2; exit 1; }
mkdir -p results/phase_04/unit
backend=${ASCON_IMPL:-ref}
case "$backend" in
  ref) extra_sources=() ;;
  opt32_lowsize) extra_sources=(external/ascon-c/crypto_aead/asconaead128/opt32_lowsize/crypto_aead.c external/ascon-c/crypto_aead/asconaead128/opt32_lowsize/permutations.c external/ascon-c/crypto_aead/asconaead128/opt32_lowsize/update.c) ;;
  *) echo "Unsupported backend: $backend" >&2; exit 2 ;;
esac
output_dir=$(mktemp -d "results/phase_04/unit/${backend}-XXXXXXXX")
printf 'Backend: %s\nArtifacts: %s\n' "$backend" "$output_dir"
gcc -std=c11 -Wall -Wextra -Werror -pedantic -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Ifirmware/crypto -Iexternal/ascon-c/tests -Iexternal/ascon-c/crypto_aead/asconaead128/$backend \
  firmware/crypto/ascon_aead.c external/ascon-c/crypto_aead/asconaead128/$backend/aead.c "${extra_sources[@]}" \
  tests/security/test_ascon_aead.c -o "$output_dir"/test_ascon_aead
ASAN_OPTIONS=detect_leaks=1 "$output_dir"/test_ascon_aead
gcc -std=c11 -Wall -Wextra -Werror -pedantic -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Ifirmware/crypto -Iexternal/ascon-c/tests -Iexternal/ascon-c/crypto_aead/asconaead128/$backend \
  firmware/crypto/ascon_aead.c external/ascon-c/crypto_aead/asconaead128/$backend/aead.c "${extra_sources[@]}" \
  tests/security/test_ascon_vectors.c -o "$output_dir"/test_ascon_vectors
ASAN_OPTIONS=detect_leaks=1 "$output_dir"/test_ascon_vectors \
  external/ascon-c/crypto_aead/asconaead128/LWC_AEAD_KAT_128_128.txt
gcc -std=c11 -Wall -Wextra -Werror -pedantic -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -DLAB_ENABLE_ASCON -Itests/security/support -Iexternal/contiki-ng/os -Ifirmware/common \
  -Ifirmware/crypto -Iexternal/ascon-c/tests -Iexternal/ascon-c/crypto_aead/asconaead128/$backend \
  firmware/crypto/ascon_aead.c firmware/crypto/aes_ccm.c firmware/crypto/secure_packet.c firmware/crypto/boot_gate.c \
  firmware/common/protocol.c external/contiki-ng/os/lib/ccm-star.c external/contiki-ng/os/lib/aes-128.c \
  external/ascon-c/crypto_aead/asconaead128/$backend/aead.c "${extra_sources[@]}" tests/security/test_ascon_packet.c \
  -o "$output_dir"/test_ascon_packet
ASAN_OPTIONS=detect_leaks=1 "$output_dir"/test_ascon_packet
