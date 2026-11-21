#!/bin/bash
set -e
msp430-gcc -mmcu=msp430f2617 -O2 -I/workspace/mustafa_benchmarks/crypto \
    -c /workspace/mustafa_benchmarks/crypto/speck.c -o /tmp/speck.o
msp430-gcc -mmcu=msp430f2617 -O2 -I/workspace/mustafa_benchmarks/crypto \
    -c /workspace/mustafa_benchmarks/crypto/present.c -o /tmp/present.o
echo "MSP430 GCC COMPILED BOTH SPECK AND PRESENT SUCCESSFULLY!"
msp430-size /tmp/speck.o /tmp/present.o
