#!/usr/bin/env bash
set -euo pipefail
cd /home/user/contiki-ng
{
  java -version
  gcc --version
  make --version
  msp430-gcc --version
  arm-none-eabi-gcc --version
} > /workspace/results/phase_01/toolchain.log 2>&1
cd tools/cooja
./gradlew --no-daemon --max-workers=1 -Dorg.gradle.jvmargs=-Xmx1024m installDist > /workspace/results/phase_01/cooja-build.log 2>&1
./build/install/cooja/bin/cooja --no-gui --contiki=/home/user/contiki-ng --logdir=/workspace/results/phase_01 /workspace/simulations/scenarios/phase1-rpl-9.csc > /workspace/results/phase_01/cooja-run.log 2>&1
