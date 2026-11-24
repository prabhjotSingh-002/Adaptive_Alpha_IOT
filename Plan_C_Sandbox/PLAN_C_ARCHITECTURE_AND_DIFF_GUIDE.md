# Plan C Architecture & Exact Source Diff Guide

**Date**: November 24, 2026  
**Status**: Uncommitted Working Tree (Branch: `plan_b_adaptive_batching`, Base Commit: `aff3cd8`)  
**Strict Safety Guarantee**: Zero commits executed. The entire workspace can be reverted instantly using:
```bash
git checkout -- . && git clean -fd
```

---

## 1. Architectural Motivation & Theoretical Foundations

### 1.1 The MRHOF Parent Flapping Vulnerability (Issue B1)
In Contiki 2.7 RPL MRHOF (`core/net/rpl/rpl-mrhof.c`), the default hysteresis threshold for switching preferred parents is governed by:
```c
#define PARENT_SWITCH_THRESHOLD_DIV 2   /* min_diff = 128 / 2 = 64 raw (0.5 ETX) */
```
When channel contention occurs in dense central clusters (such as Zolertia Z1 nodes 3, 4, 7, 8, 10), ContikiMAC 8 Hz strobing introduces short-term EWMA link fluctuations:
1. When node 4 sends a packet to parent node 3, CSMA backoff or a single dropped strobe increments node 3's link ETX slightly.
2. If another neighbor (e.g. node 8 or 7) has an EWMA metric that is temporarily 65 units (0.51 ETX) lower, node 4 immediately switches its preferred parent.
3. This triggers a flurry of RPL DAO messages, route updates, and ContikiMAC strobes.
4. The sudden route switch shifts traffic to node 8, causing congestion on node 8 and flipping the metric differential back in favor of node 3.
5. In Plan B Seed 345678, this cyclic parent flapping caused nodes 4 and 8 to burn **2.30 mW** and **2.68 mW**, collapsing PDR to **33.93%**.

#### The Hysteresis Fix
By setting `PARENT_SWITCH_THRESHOLD_DIV = 1`, the minimum required metric improvement before switching parents is increased from **0.5 ETX (64 raw)** to **1.0 ETX (128 raw)**:
$$\Delta \text{ETX}_{\text{switch}} \ge 1.0$$
This cleanly dampens transient link noise while allowing permanent link breaks to switch smoothly.

---

### 1.2 RPL-Aware Leaf RDC Suppression (Issue D)
In 6LoWPAN / RPL mesh topologies, nodes fall into two structural categories:
1. **Relay Nodes (Routers)**: Nodes with one or more child routing entries (`uip_ds6_route_num_routes() > 0`). These nodes MUST keep their ContikiMAC receiver active at 8 Hz to listen for incoming forwarded traffic.
2. **Leaf Nodes**: Peripheral edge nodes (`uip_ds6_route_num_routes() == 0`). No downstream nodes ever route through a leaf node.

#### Theoretical Listen Energy Waste
At 8 Hz check rate, ContikiMAC turns on the CC2420 radio 8 times per second. Even with phase optimization, idle listening and hearing non-destined neighbor strobes consumes:
$$P_{\text{listen}} \approx 0.40 - 0.50 \text{ mW}$$
For a leaf node generating a batch only once every 40 seconds (at $k=4$), keeping the radio listening for 40 seconds of zero incoming traffic wastes over **95% of its radio energy**.

#### The Leaf RDC Sleep State Machine
1. **Discovery & Stabilization**: The node monitors routing tables. If `uip_ds6_route_num_routes() == 0` and the node has joined a valid RPL DAG with a preferred parent for $\ge 2$ consecutive 10s ticks (20s stability window), it enters `LEAF_SLEEP_MODE`.
2. **Radio Powerdown**: Calls `NETSTACK_RDC.off(0)`, which powers down the CC2420 and cancels the ContikiMAC rtimer periodic wakeups.
3. **Transmission Wakeup**: When a sensor batch is ready to flush (`do_flush == true`), the node powers on ContikiMAC (`NETSTACK_RDC.on()`), transmits the 6LoWPAN batch via `simple_udp_sendto()`, and starts a **5.0-second post-TX guard timer** (`ctimer_set(&leaf_sleep_timer, CLOCK_SECOND * 5, leaf_sleep_timer_cb, NULL)`).
4. **Fragmentation Safety**: The 5.0s window provides ample time for 107-byte 2-frame 6LoWPAN reassembly, CSMA backoffs, and link-layer ACKs to complete cleanly.
5. **Self-Healing**: If at any time `uip_ds6_route_num_routes() > 0` (a child attaches) or the DAG preferred parent is lost, the node immediately wakes up and returns to permanent relay mode.

---

## 2. Complete Code Diffs

### 2.1 File 1: `legacy_stack/contiki-2.7/core/net/rpl/rpl-mrhof.c`

```diff
--- a/legacy_stack/contiki-2.7/core/net/rpl/rpl-mrhof.c
+++ b/legacy_stack/contiki-2.7/core/net/rpl/rpl-mrhof.c
@@ -80,7 +80,11 @@
 #define DEFAULT_LINK_METRIC     RPL_INIT_LINK_METRIC
 
 /* Default threshold for switching preferred parent. */
+#ifdef ENABLE_MRHOF_HYST
+#define PARENT_SWITCH_THRESHOLD_DIV 1   /* 1.0 ETX (128 raw) hysteresis */
+#else
 #define PARENT_SWITCH_THRESHOLD_DIV 2   /* Contiki 2.7 default: 0.5 ETX (64 raw) */
+#endif
 
 /* Reject parents that have a higher link metric than the following. */
 #define MAX_LINK_METRIC         RPL_MAX_PATH_COST
```

---

### 2.2 File 2: `legacy_stack/firmware/sensor.c`

```diff
--- a/legacy_stack/firmware/sensor.c
+++ b/legacy_stack/firmware/sensor.c
@@ -21,6 +21,19 @@
 #include "net/rpl/rpl.h"
 #include "dyn_batch.h"
 
+#if ENABLE_LEAF_RDC_SLEEP
+#include "net/uip-ds6-route.h"
+#include "net/netstack.h"
+#include "sys/ctimer.h"
+static struct ctimer leaf_sleep_timer;
+static uint8_t is_leaf_sleeping = 0;
+static uint8_t zero_route_ticks = 0;
+static uint8_t leaf_mode_active = 0;
+static uint16_t stat_sleep_cycles = 0;
+
+static void leaf_sleep_timer_cb(void *ptr) {
+  (void)ptr;
+  if(leaf_mode_active) {
+    is_leaf_sleeping = 1;
+    NETSTACK_RDC.off(0);
+  }
+}
+#endif
+
@@ -141,6 +154,34 @@
     printf("RSLAB,%u,ENERGY_RAW,%lu,%lu,0,%lu,%lu\n", (unsigned)node_id, cpu, lpm, tx, rx);
 
+#if ENABLE_LEAF_RDC_SLEEP
+    if(seconds_elapsed >= 110 && (readings_sent >= 4 || batch_counter > 1)) {
+      rpl_dag_t *curr_dag = rpl_get_any_dag();
+      int nroutes = uip_ds6_route_num_routes();
+      bool has_parent = (curr_dag != NULL && curr_dag->joined && curr_dag->preferred_parent != NULL);
+
+      if(nroutes == 0 && has_parent) {
+        if(zero_route_ticks < 255) zero_route_ticks++;
+        if(zero_route_ticks >= 2) {
+          leaf_mode_active = 1;
+          if(!is_leaf_sleeping) {
+            is_leaf_sleeping = 1;
+            stat_sleep_cycles++;
+            NETSTACK_RDC.off(0);
+          }
+        }
+      } else {
+        zero_route_ticks = 0;
+        leaf_mode_active = 0;
+        if(is_leaf_sleeping) {
+          is_leaf_sleeping = 0;
+          ctimer_stop(&leaf_sleep_timer);
+          NETSTACK_RDC.on();
+        }
+      }
+    }
+#endif
+
@@ -207,6 +248,13 @@
       /* Flush batch if capacity reached or all readings generated */
       if(do_flush) {
+#if ENABLE_LEAF_RDC_SLEEP
+        if(is_leaf_sleeping) {
+          is_leaf_sleeping = 0;
+          ctimer_stop(&leaf_sleep_timer);
+          NETSTACK_RDC.on();
+        }
+#endif
         lab_batch batch;
@@ -242,6 +290,12 @@
             simple_udp_sendto(&sensor_conn, wire, wire_len, &root_addr);
             printf("RSLAB,%u,TX\n", (unsigned)node_id);
             lab_commit_on_send(&agg_queue, batch.count);
+#if ENABLE_LEAF_RDC_SLEEP
+            if(leaf_mode_active) {
+              /* Post-TX guard: keep awake for 5.0s to allow CSMA retries, fragments & ACK */
+              ctimer_set(&leaf_sleep_timer, CLOCK_SECOND * 5, leaf_sleep_timer_cb, NULL);
+            }
+#endif
```

---

## 3. Revert and Commit Procedures

### How to Instant-Revert (Return to Locked Plan B)
If you decide not to retain Plan C or wish to return strictly to the clean `plan_b_adaptive_batching` branch:
```bash
# 1. Reset all tracked files
git checkout -- .

# 2. Remove any untracked runner files or outputs
git clean -fd
```
This restores `rpl-mrhof.c` and `sensor.c` with zero residual changes.

### How to Commit Plan C (If Accepted)
If you wish to create a dedicated branch for Plan C:
```bash
git checkout -b plan_c_cross_layer
git add legacy_stack/contiki-2.7/core/net/rpl/rpl-mrhof.c legacy_stack/firmware/sensor.c legacy_stack/runners/run_plan_c_matrix.py legacy_stack/runners/build_master_comparison.py legacy_stack/runners/generate_plan_c_plots.py Plan_C_Sandbox/
git commit -m "feat(cross-layer): implement Plan C MRHOF hysteresis and RPL leaf RDC suppression"
```
