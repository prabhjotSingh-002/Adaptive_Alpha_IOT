#!/bin/bash
set -e
gcc -O2 -I/workspace/mustafa_benchmarks/crypto \
    /workspace/mustafa_benchmarks/crypto/speck.c \
    /workspace/mustafa_benchmarks/crypto/present.c \
    /workspace/mustafa_benchmarks/crypto/test_all_ciphers.c \
    -o /tmp/test_all
/tmp/test_all
