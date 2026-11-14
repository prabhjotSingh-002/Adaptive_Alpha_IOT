#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_
#include "generated-conf.h"
/* RPL source-route graph counts the root as a node. */
#define NETSTACK_MAX_ROUTE_ENTRIES LAB_LAST_NODE
#if LAB_SCHEMA == 2
/* Same bounded packet-queue configuration in all Phase 4 controls. */
#define QUEUEBUF_CONF_NUM 4
#endif
#ifndef LAB_SCHEMA
#define LAB_SCHEMA 1u
#endif
#ifndef LAB_DUAL_PROFILE
#define LAB_DUAL_PROFILE 0u
#endif
#ifndef LAB_SWITCH_TEST
#define LAB_SWITCH_TEST 0u
#endif
#ifndef LAB_FLUSH_LEAD_MS
#define LAB_FLUSH_LEAD_MS 0u
#endif
#ifndef LAB_RADIO_OFF_UNTIL
#define LAB_RADIO_OFF_UNTIL 0u
#endif
#ifndef LAB_CPU_WORK_ITERATIONS
#define LAB_CPU_WORK_ITERATIONS 0u
#endif
#ifndef LAB_ENERGY_MODEL
#define LAB_ENERGY_MODEL 0u
#endif
#ifndef LAB_DEPLETION_NODE
#define LAB_DEPLETION_NODE 0u
#endif
#ifndef LAB_ENERGY_SAMPLE_MS
#define LAB_ENERGY_SAMPLE_MS 125u
#endif
#ifndef LAB_ENERGY_TELEMETRY
#define LAB_ENERGY_TELEMETRY 0u
#endif
#if LAB_ENERGY_TELEMETRY
#define ENERGEST_CONF_ON 1
#endif
#define LAB_PROFILE_COUNT (LAB_DUAL_PROFILE ? 2u : 1u)
#ifndef LAB_PROFILE
#define LAB_PROFILE 0u
#endif
#if LAB_PROFILE != 0 && LAB_PROFILE != 1 && LAB_PROFILE != 2
#error Unsupported LAB_PROFILE
#endif
#ifndef LAB_RADIO_LOSS_TEST
#define LAB_RADIO_LOSS_TEST 0u
#endif
#ifndef LAB_REORDER_TEST
#define LAB_REORDER_TEST 0u
#endif
#ifndef LAB_CRITICAL_READING
#define LAB_CRITICAL_READING 0u
#endif
#define LAB_ATTACK_CASES (LAB_SCHEMA == 2 ? 8u : 7u)
#ifndef LAB_ROOT_RESET_TEST
#define LAB_ROOT_RESET_TEST 0u
#endif
#ifndef LAB_ATTACK_TEST
#define LAB_ATTACK_TEST 0u
#endif
/* Phase 5 policy defaults */
#ifndef LAB_POLICY_MODE
#define LAB_POLICY_MODE 0u
#endif
#ifndef LAB_B3_THRESHOLD_NJ_HI
#define LAB_B3_THRESHOLD_NJ_HI 0u
#endif
#ifndef LAB_B3_THRESHOLD_NJ_LO
#define LAB_B3_THRESHOLD_NJ_LO 0u
#endif
#ifndef LAB_B6_PROFILE
#define LAB_B6_PROFILE 1u
#endif
#ifndef LAB_P1_TRANSITION_COST_NJ
#define LAB_P1_TRANSITION_COST_NJ 0u
#endif
#ifndef LAB_P1_MIN_DWELL_MS
#define LAB_P1_MIN_DWELL_MS 0u
#endif
#ifndef LAB_P1_MARGIN_NJ
#define LAB_P1_MARGIN_NJ 0u
#endif
#endif

#ifndef LAB_P1_COSTS
#define LAB_P1_COSTS {{0,0,0},{0,0,0}}
#endif
