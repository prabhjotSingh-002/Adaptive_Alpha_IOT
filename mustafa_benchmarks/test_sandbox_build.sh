#!/bin/bash
set -euo pipefail

echo "=== Testing Sandbox Build for Speck (Profile 3) and Present (Profile 4) ==="

TMP_DIR="/tmp/sandbox_firmware"
rm -rf "$TMP_DIR"
cp -r /workspace/firmware "$TMP_DIR"
rm -rf "$TMP_DIR/sensor/build" "$TMP_DIR/root/build"
cp /workspace/mustafa_benchmarks/crypto/speck.h "$TMP_DIR/crypto/"

cp /workspace/mustafa_benchmarks/crypto/speck.c "$TMP_DIR/crypto/"
cp /workspace/mustafa_benchmarks/crypto/present.h "$TMP_DIR/crypto/"
cp /workspace/mustafa_benchmarks/crypto/present.c "$TMP_DIR/crypto/"
cp /workspace/mustafa_benchmarks/crypto/secure_packet.h "$TMP_DIR/crypto/"
cp /workspace/mustafa_benchmarks/crypto/secure_packet.c "$TMP_DIR/crypto/"

# Patch Makefile to include speck.c and present.c and set CONTIKI absolute path
sed -i 's/PROJECT_SOURCEFILES +=/PROJECT_SOURCEFILES += speck.c present.c/' "$TMP_DIR/Makefile"
sed -i 's|CONTIKI = .*|CONTIKI = /workspace/external/contiki-ng|' "$TMP_DIR/Makefile"
sed -i 's|include ../crypto/ascon-backend.mk|# include ../crypto/ascon-backend.mk|' "$TMP_DIR/Makefile"


# Patch project-conf.h to allow profiles 3 and 4
sed -i 's/LAB_PROFILE != 2/LAB_PROFILE != 2 \&\& LAB_PROFILE != 3 \&\& LAB_PROFILE != 4/' "$TMP_DIR/project-conf.h"

# Patch sensor.c and root.c
sed -i 's/LAB_PROFILE == 1 || LAB_PROFILE == 2/LAB_PROFILE >= 1/g' "$TMP_DIR/sensor/sensor.c"
sed -i 's/LAB_PROFILE == 1 || LAB_PROFILE == 2/LAB_PROFILE >= 1/g' "$TMP_DIR/root/root.c"

echo "=== Configured for Speck (Profile 3, Batch Cap 2) ==="
cat << 'EOF' > "$TMP_DIR/generated-conf.h"
#define LAB_BATCH_CAP 2u
#define LAB_DEADLINE_MS 3000u
#define LAB_PERIOD_MS 1000u
#define LAB_WARMUP_MS 60000u
#define LAB_TOTAL_READINGS 24u
#define LAB_LAST_NODE 5u
#define LAB_PAYLOAD_BUDGET 67u
#define LAB_RESERVED_BYTES 16u
#define LAB_FLUSH_LEAD_MS 125u
#define LAB_RADIO_OFF_UNTIL 0u
#define LAB_CPU_WORK_ITERATIONS 0u
#define LAB_ENERGY_SAMPLE_MS 125u
#define LAB_DEPLETION_NODE 0u
#define LAB_ENERGY_MODEL 1u
#define LAB_POWER_MV 3000u
#define LAB_POWER_CPU 4626000u
#define LAB_POWER_LPM 427100u
#define LAB_POWER_TX 16974000u
#define LAB_POWER_LISTEN 18374000u
#define LAB_ENERGY_BUDGET 4097000000ULL
#define LAB_ENERGY_TELEMETRY 1u
#define LAB_SCHEMA 2u
#define LAB_CONFIG_ID 99999u
#define LAB_DUAL_PROFILE 0u
#define LAB_SWITCH_TEST 0u
#define LAB_RADIO_LOSS_TEST 0u
#define LAB_REORDER_TEST 0u
#define LAB_CRITICAL_READING 0u
#define LAB_PROFILE 3u
#define LAB_ROOT_RESET_TEST 0u
#define LAB_ATTACK_TEST 0u
#define LAB_POLICY_MODE 0u
EOF

echo "--- Building sensor.z1 for Speck ---"
make -C "$TMP_DIR/sensor" clean
make -C "$TMP_DIR/sensor" -j1 sensor.z1 TARGET=z1

echo "--- Building root.z1 for Speck ---"
make -C "$TMP_DIR/root" clean
make -C "$TMP_DIR/root" -j1 root.z1 TARGET=z1

echo "SPECK BUILD SUCCESSFUL!"
msp430-size "$TMP_DIR/sensor/build/z1/sensor.z1"
msp430-size "$TMP_DIR/root/build/z1/root.z1"

echo "=== Configured for Present (Profile 4, Batch Cap 2) ==="
sed -i 's/#define LAB_PROFILE 3u/#define LAB_PROFILE 4u/' "$TMP_DIR/generated-conf.h"
echo "--- Building sensor.z1 for Present ---"
make -C "$TMP_DIR/sensor" clean
make -C "$TMP_DIR/sensor" -j1 sensor.z1 TARGET=z1

echo "--- Building root.z1 for Present ---"
make -C "$TMP_DIR/root" clean
make -C "$TMP_DIR/root" -j1 root.z1 TARGET=z1

echo "PRESENT BUILD SUCCESSFUL!"
msp430-size "$TMP_DIR/sensor/build/z1/sensor.z1"
msp430-size "$TMP_DIR/root/build/z1/root.z1"

echo "=== ALL SANDBOX BUILDS PASSED ==="
