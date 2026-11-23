#!/bin/bash
set -e
cd /workspace/legacy_stack/firmware

echo "=== COMPILING STATIC AES k=4 BASELINE ==="
rm -rf obj_z1 *.z1 *.co contiki-z1.a
make root.z1 TARGET=z1 DEFINES=LAB_BATCH_CAP=4,LAB_PROFILE=1,LAB_ENABLE_AES=1,IS_ROOT=1 > /dev/null 2>&1
rm -rf sensor.z1 sensor.co obj_z1/queuebuf.o contiki-z1.a
make sensor.z1 TARGET=z1 DEFINES=LAB_BATCH_CAP=4,LAB_PROFILE=1,LAB_ENABLE_AES=1 > /dev/null 2>&1
msp430-size sensor.z1 root.z1

echo "=== COMPILING PLAN B AES (ENABLE_DYN_BATCH=1, ENABLE_SPIKE_TRACE=1) ==="
rm -rf obj_z1 *.z1 *.co contiki-z1.a
make root.z1 TARGET=z1 DEFINES=LAB_BATCH_CAP=4,LAB_PROFILE=1,LAB_ENABLE_AES=1,IS_ROOT=1 > /dev/null 2>&1
rm -rf sensor.z1 sensor.co obj_z1/queuebuf.o contiki-z1.a
make sensor.z1 TARGET=z1 DEFINES=LAB_BATCH_CAP=4,LAB_PROFILE=1,LAB_ENABLE_AES=1,ENABLE_DYN_BATCH=1,ENABLE_SPIKE_TRACE=1 > /dev/null 2>&1
msp430-size sensor.z1 root.z1

echo "=== COMPILING PLAN B SPECK (ENABLE_DYN_BATCH=1, ENABLE_SPIKE_TRACE=1) ==="
rm -rf obj_z1 *.z1 *.co contiki-z1.a
make root.z1 TARGET=z1 DEFINES=LAB_BATCH_CAP=4,LAB_PROFILE=3,LAB_ENABLE_SPECK=1,IS_ROOT=1 > /dev/null 2>&1
rm -rf sensor.z1 sensor.co obj_z1/queuebuf.o contiki-z1.a
make sensor.z1 TARGET=z1 DEFINES=LAB_BATCH_CAP=4,LAB_PROFILE=3,LAB_ENABLE_SPECK=1,ENABLE_DYN_BATCH=1,ENABLE_SPIKE_TRACE=1 > /dev/null 2>&1
msp430-size sensor.z1 root.z1
