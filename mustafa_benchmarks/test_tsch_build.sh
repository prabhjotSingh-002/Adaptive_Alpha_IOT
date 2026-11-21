#!/bin/bash
set -eu
TMP=/tmp/test_tsch
rm -rf "$TMP"
cp -r /workspace/firmware "$TMP"
cd "$TMP/sensor"

cat > ../generated-conf.h << 'EOF'
#define LAB_BATCH_CAP 1u
#define LAB_DEADLINE_MS 35000u
#define LAB_PERIOD_MS 10000u
#define LAB_WARMUP_MS 60000u
#define LAB_TOTAL_READINGS 8u
#define LAB_LAST_NODE 5u
#define LAB_PAYLOAD_BUDGET 67u
#define LAB_RESERVED_BYTES 16u
#define LAB_FLUSH_LEAD_MS 125u
#define LAB_RADIO_OFF_UNTIL 0u
#define LAB_CPU_WORK_ITERATIONS 0u
#define LAB_ENERGY_SAMPLE_MS 1000u
#define LAB_DEPLETION_NODE 0u
#define LAB_ENERGY_MODEL 0u
#define LAB_ENERGY_TELEMETRY 1u
#define LAB_SCHEMA 2u
#define LAB_CONFIG_ID 99999u
#define LAB_DUAL_PROFILE 0u
#define LAB_SWITCH_TEST 0u
#define LAB_RADIO_LOSS_TEST 0u
#define LAB_REORDER_TEST 0u
#define LAB_CRITICAL_READING 0u
#define LAB_PROFILE 0u
#define LAB_ROOT_RESET_TEST 0u
#define LAB_ATTACK_TEST 0u
#define LAB_POLICY_MODE 0u
EOF

sed -i 's|CONTIKI = .*|CONTIKI = /workspace/external/contiki-ng|' ../Makefile
sed -i 's|include ../crypto/ascon-backend.mk|# include ../crypto/ascon-backend.mk|' ../Makefile
make sensor.z1 TARGET=z1 MAKE_MAC=MAKE_MAC_TSCH
msp430-size build/z1/sensor.z1
