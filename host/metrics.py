"""Only source of final Phase 2 diagnostic metrics; no authenticated claims."""
from demand_schedule import run_horizon_ms
import math

def percentile(values, fraction):
    if not values: return None
    data = sorted(values); x = (len(data) - 1) * fraction
    lo = math.floor(x); hi = math.ceil(x)
    return data[lo] + (data[hi] - data[lo]) * (x - lo)

def radio_summary(frames):
    fragments, data_frames, unknown = 0, 0, 0
    sizes = []
    for frame in frames:
        data = bytes.fromhex(frame["hex"]); sizes.append(len(data))
        if len(data) < 3: raise ValueError("Truncated MAC capture")
        fcf = int.from_bytes(data[:2], "little")
        if (fcf & 7) != 1: continue
        data_frames += 1
        # Pinned native Cooja uses classic 802.15.4 framing; reject unsupported layouts.
        if fcf & 8 or fcf & 256 or ((fcf >> 12) & 3) > 1:
            unknown += 1; continue
        dest, source = (fcf >> 10) & 3, (fcf >> 14) & 3
        if dest == 1 or source == 1: unknown += 1; continue
        offset = 3
        if dest: offset += 2 + (2 if dest == 2 else 8)
        if source: offset += (0 if dest and fcf & 64 else 2) + (2 if source == 2 else 8)
        if offset >= len(data): unknown += 1; continue
        if (data[offset] & 248) in (192, 224): fragments += 1
    return {"captured_frames": len(frames), "captured_frame_bytes": sum(sizes), "data_frames": data_frames, "max_frame_bytes": max(sizes, default=0), "fragment_frames": fragments, "unclassified_data_frames": unknown}

def summarize(events, frames, config, clients, cap):
    generated, transmitted, dropped, delivered = {}, set(), set(), {}
    policy_timing = []
    measured_features = []
    policy_state = {}
    packets = {}; done = set(); ready = set(); duplicates = 0
    profile = config.get("profile", 0)
    if profile not in (0, 1, 2): raise ValueError("Unsupported profile")
    cipher = {0: "N0", 1: "AES-128-CCM", 2: "Ascon-AEAD128"}[profile]
    if config.get('dual_profile') and config.get('mode_policy',{}).get(config.get('mode'),0):
        cipher = 'dual-profile AEAD (AES-128-CCM / Ascon-AEAD128)'
    deceased = {}; removed = {}; stacks = {}
    contexts = set(); root_ready = False
    metadata = set(); accepted_packets = set()
    schema = config.get("schema_version", 1)
    def packet_key(node, event):
        return (node, event.get("profile", profile), event.get("epoch", 1), event["counter"])

    injections = []; rejects = []; boot_requests = []
    rejection_reasons = {}
    energy_timers = {}; energy_last = {}; energy_samples = {}
    for e in events:
        node, kind = e["node_id"], e["event_type"]
        if kind == "STACK":
            if not config.get("energy_telemetry") or e["used"] + 128 >= e["reserved"]: raise ValueError("Invalid/exhausted stack guard")
            stacks[node] = max(stacks.get(node,0), e["used"])
        if kind == "DEPLETED":
            if not config.get("lifetime") or node not in clients or node in deceased: raise ValueError("Invalid terminal depletion")
            deceased[node] = e
        if kind == "REMOVED":
            if node not in deceased or node in removed or e["terminal"] != 1: raise ValueError("Unverified simulator cutoff")
            removed[node] = e
        if node in deceased and kind in ("GEN","TX","BOOT_REQUEST","CONTEXT_READY"):
            raise ValueError("Activity after depletion")
        if kind in ("ENERGY_TIMER", "ENERGY_RAW"):
            if not config.get("energy_telemetry"): raise ValueError("Unexpected energy instrumentation")
            if kind == "ENERGY_TIMER":
                if node in energy_timers or e["frequency"] <= 0 or e["bits"] < 16: raise ValueError("Invalid energy timer")
                energy_timers[node] = e
            else:
                if node not in energy_timers: raise ValueError("Energy counters before timer identity")
                counters = tuple(e[k] for k in ("cpu","lpm","deep","tx","listen"))
                previous = energy_last.get(node)
                if previous and (e["sim_time_us"] <= previous[0] or any(a < b for a,b in zip(counters,previous[1]))): raise ValueError("Invalid energy counter progression")
                if previous and e["sim_time_us"] - previous[0] >= (2 ** energy_timers[node]["bits"]) * 1000000 / energy_timers[node]["frequency"]: raise ValueError("Unsafe Energest wrap cadence")
                energy_last[node] = (e["sim_time_us"], counters)
                energy_samples[node] = energy_samples.get(node,0) + 1
        if kind == "META2":
            if (node in metadata and not ((config.get("root_reset_test") and node == 1) or (config.get("sensor_reset_test") and node == 2))) or (e["config_id"], e["profile"], e["profile_count"], e["switch_test"]) != (config["config_id"], profile, 2 if config.get("dual_profile") else 1, int(bool(config.get("switch_test")))):
                raise ValueError("Runtime configuration mismatch")
            metadata.add(node)
        if kind == "PACKET":
            identity = packet_key(e["sender"], e)
            if node != 1 or identity in accepted_packets: raise ValueError("Invalid accepted packet")
            accepted_packets.add(identity)
        if kind == "BOOT_REQUEST":
            boot_requests.append(e)
        if kind == "RESET_PROBE" and (not config.get("root_reset_test") or node != 2 or e["counter"] != 1): raise ValueError("Unexpected reset probe")
        if kind == "ERROR": raise ValueError("Firmware error: " + str(e))
        if kind == "REJECT":
            if not (config.get("attack_test") or config.get("root_reset_test") or config.get("provision_fault")): raise ValueError("Unexpected rejection: " + str(e))
            rejects.append(e)
            reason = str(e.get("reason", "legacy_unspecified"))
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        if kind == "INJECT":
            if not config.get("attack_test") or node != 2: raise ValueError("Unexpected test injection")
            injections.append(e)
        if kind == "CONTEXT_READY":
            if profile not in (1, 2) or e["profile"] != profile or node in contexts: raise ValueError("Invalid context activation")
            contexts.add(node)
        if kind == "ROOT_READY":
            if node != 1 or e["profile"] != profile or root_ready: raise ValueError("Invalid root profile")
            root_ready = True
        if kind == "READY":
            if (e["cap"], e["period_ms"], e["deadline_ms"], e["total"]) != (cap, config["period_ms"], config["deadline_ms"], config["readings_per_sensor"]): raise ValueError("Stale firmware configuration")
            ready.add(node)
        if kind == "GEN":
            key = (node, e["reading_id"])
            if key in generated: raise ValueError("Repeated generated ID")
            generated[key] = e
        if kind == "DONE":
            if e["generated"] != config["readings_per_sensor"]: raise ValueError("Incorrect DONE count")
            done.add(node)
        if kind == "DROP":
            key = (node, e["reading_id"])
            if key in dropped: raise ValueError("Repeated drop")
            dropped.add(key)
        if kind == 'FEATURE':
            if config.get('phase') != 5 or node not in clients or not 0 <= e['rate_hz_x100'] <= 65535 or not 0 <= e['samples'] <= 8 or not 0 <= e['age_ms'] <= 2**32-1:
                raise ValueError('Invalid measured traffic feature')
            measured_features.append(e)
        if kind == "POLICY_TIME":
            if config.get('phase') != 5 or node not in clients or e['ticks'] < 0 or e['frequency'] <= 0:
                raise ValueError('Invalid policy timing')
            policy_timing.append(e['ticks']/e['frequency'])
        if kind == "POLICY":
            fit = min(4, (config['payload_budget'] - config['reserved_bytes'] - 11)//10)
            if config.get('phase') != 5 or node not in clients or e['profile'] not in (1,2) or e['cap'] not in (1,2,4) or e['cap'] > fit:
                raise ValueError('Invalid policy action')
            policy_state[node] = (e['profile'], e['cap'])
        if kind == "TX":
            active_cap = cap
            if config.get('phase') == 5 and config.get('policy_repair_version') and config.get('mode_policy',{}).get(config.get('mode'),0):
                if node not in policy_state: raise ValueError('Submission before policy action')
                selected, active_cap = policy_state[node]
                if e.get('profile',profile) != selected: raise ValueError('TX profile differs from policy')
            key = packet_key(node, e)
            if key in packets or not 1 <= e["count"] <= active_cap or e["bytes"] != 11 + 10 * e["count"] + (16 if profile in (1, 2) else 0) or e["bytes"] + (0 if profile in (1, 2) else config["reserved_bytes"]) > config["payload_budget"] or e["last_id"] - e["first_id"] + 1 != e["count"] or e["hold_ms"] > config["deadline_ms"]:
                raise ValueError("Invalid submission/count/byte/deadline bound")
            packets[key] = e
            for rid in range(e["first_id"], e["last_id"] + 1):
                reading = (node, rid)
                if reading in transmitted: raise ValueError("Repeated submission")
                transmitted.add(reading)
        if kind == "RX":
            if e.get("auth_ok", False) != (profile in (1, 2)): raise ValueError("Incorrect RX authentication status")
            key = (e["sender"], e["reading_id"])
            if node != 1 or e["duplicate"] not in (0, 1): raise ValueError("Invalid root event")
            if e["duplicate"]: duplicates += 1; continue
            if key in delivered: raise ValueError("Root failed unique accounting")
            delivered[key] = e
    if config.get("sensor_reset_test"):
        resets=[e for e in boot_requests if e["node_id"]==2]
        if len(resets)!=2: raise ValueError("Missing sensor replacement boot")
        if not any(e["event_type"]=="RX" and e["sender"]==2 and e["sim_time_us"]<resets[-1]["sim_time_us"] for e in events): raise ValueError("Missing authenticated traffic before sensor reset")
        if any(e["node_id"]==2 and e["event_type"] in ("TX","GEN","CONTEXT_READY") and e["sim_time_us"]>=resets[-1]["sim_time_us"] for e in events): raise ValueError("Sensor resumed after reset")
    planned = {(node, rid) for node in clients for rid in range(1, config["readings_per_sensor"] + 1)}
    if config.get("sensor_reset_test"): planned={key for key in planned if key[0]!=2 or key[1]==1}
    expected = set(generated) if config.get("lifetime") else planned
    if config.get("lifetime"):
        horizon=run_horizon_ms(config) * 1000
        for node in clients:
            if node not in deceased and node in energy_last and horizon-energy_last[node][0] > 2000000:
                raise ValueError("Missing survivor final telemetry")
        for node,terminal in deceased.items():
            snapshots=[e for e in events if e["node_id"]==node and e["event_type"]=="ENERGY_MODEL"]
            if not snapshots or snapshots[-1]["total_nj"]!=terminal["total_nj"] or terminal["total_nj"] < config["energy_budget_nj"]:
                raise ValueError("Unverified exhausted budget")
        if config.get("bottleneck") and deceased:
            cutoff=deceased.get(2,{}).get("sim_time_us")
            if cutoff is None or not any(e["event_type"]=="ROUTE" and e["node_id"]==3 and e["parent"]==2 and e["sim_time_us"]<cutoff for e in events):
                raise ValueError("Missing actual bottleneck parent path")
            if not any(e["event_type"]=="RX" and e["sender"]==3 and e["sim_time_us"]<cutoff for e in events):
                raise ValueError("No downstream traffic before forwarder depletion")
        if set(deceased) != set(removed): raise ValueError("Missing terminal cutoff")
        for node in clients:
            ids = sorted(rid for n,rid in generated if n==node)
            if ids != list(range(1,len(ids)+1)) or len(ids)>config["readings_per_sensor"]: raise ValueError("Invalid live generation prefix")
        for frame in frames:
            if frame["node_id"] in removed and frame["sim_time_us"] > removed[frame["node_id"]]["sim_time_us"]:
                raise ValueError("Radio transmission after whole-node removal")
    if config.get("provision_fault"):
        if contexts!=set(clients) or root_ready or not rejects or delivered: raise ValueError("Incomplete provisioning did not lock complete root set")
    elif profile in (1, 2) and (contexts != set(clients) | {1} or not root_ready): raise ValueError("Missing security activation")
    if set(generated) != expected or done | set(deceased) | ({2} if config.get("sensor_reset_test") else set()) != set(clients) or ready != set(clients): raise ValueError("Missing generator/READY/DONE events")
    if transmitted & dropped or transmitted | dropped != expected: raise ValueError("Readings not fully accounted at sender")
    if config.get("energy_telemetry") and (set(energy_last) != set(clients) | {1} or any(n < 2 for n in energy_samples.values())):
        raise ValueError("Missing energy telemetry")
    if schema == 2:
        if metadata != set(clients) | {1}: raise ValueError("Missing schema metadata")
        if not accepted_packets <= set(packets): raise ValueError("Unknown accepted packet")
        rx_packets = {packet_key(e["sender"], e) for e in events if e["event_type"] == "RX"}
        if rx_packets != accepted_packets: raise ValueError("Packet/reading evidence mismatch")
    if config.get("switch_test"):
        for node in clients:
            sent = [e for e in events if e["node_id"] == node and e["event_type"] == "TX"]
            if len(sent) < 3 or [(e["profile"], e["counter"]) for e in sent[:3]] != [(1,1),(2,1),(1,2)]:
                raise ValueError("Missing profile-return transmissions or incorrect retained counters")
    delays = []
    for key, rx in delivered.items():
        if key not in transmitted or packet_key(key[0], rx) not in packets: raise ValueError("Received unknown reading/packet")
        gen = generated[key]
        if (rx["created_ms"], rx["value"]) != (gen["created_ms"], gen["value"]): raise ValueError("Payload corruption")
        tx = packets[packet_key(key[0], rx)]
        if not tx["first_id"] <= key[1] <= tx["last_id"]: raise ValueError("Packet membership mismatch")
        delay = rx["sim_time_ms"] - gen["sim_time_ms"]
        if delay < 0: raise ValueError("Negative global delay")
        delays.append(delay)
    if config.get("attack_test"):
        cases = list(range(1,9 if schema == 2 else 8))
        if [e["case"] for e in injections] != cases or len(rejects) != len(cases):
            raise ValueError("Missing injection or rejection")
        if not any(e["event_type"] == "DROP" and e["node_id"] == 2 and e["reason"] == 99 for e in events):
            raise ValueError("Missing intentional pre-submission loss")
        controls = [e for e in events if e["event_type"] == "RX" and e["sender"] == 2 and not e["duplicate"]]
        if not controls or controls[0]["sim_time_us"] >= injections[0]["sim_time_us"] or controls[-1]["sim_time_us"] <= injections[-1]["sim_time_us"]:
            raise ValueError("Missing valid controls surrounding injections")
        if not any(e["counter"] > 2 for e in controls): raise ValueError("No valid traffic after counter gap")
        for idx, inj in enumerate(injections):
            end = injections[idx+1]["sim_time_us"] if idx+1 < len(injections) else float("inf")
            if sum(inj["sim_time_us"] <= x["sim_time_us"] < end for x in rejects) != 1:
                raise ValueError("Injection did not produce exactly one timely receiver rejection")
    if config.get("root_reset_test"):
        roots = [e for e in boot_requests if e["node_id"] == 1]
        if len(roots) != 2: raise ValueError("Root replacement did not produce two boot requests")
        reset_at = roots[1]["sim_time_us"]
        if not any(e["event_type"] == "RX" and e["sim_time_us"] < reset_at for e in events):
            raise ValueError("Missing valid receive before root replacement")
        if any(e["event_type"] == "RX" and e["sim_time_us"] >= reset_at for e in events):
            raise ValueError("Root accepted traffic after reset without grant")
        if not any(e["sim_time_us"] >= reset_at for e in rejects):
            raise ValueError("No traffic reached locked root after replacement")
    if config.get("critical_reading"):
        triggers=[e for e in events if e["event_type"]=="CRITICAL"]
        if {e["node_id"] for e in triggers} != set(clients) or len(triggers)!=len(clients): raise ValueError("Missing critical trigger")
        for e in triggers:
            if e["reading_id"]!=config["critical_reading"]: raise ValueError("Wrong critical reading")
            sends=[p for p in packets.values() if p["node_id"]==e["node_id"] and p["first_id"]<=e["reading_id"]<=p["last_id"]]
            if len(sends)!=1 or not 0<=sends[0]["sim_time_us"]-e["sim_time_us"]<=125000: raise ValueError("Critical event did not flush")
            if (e["node_id"],e["reading_id"]) not in delivered: raise ValueError("Critical reading not authenticated at root")
    if config.get("radio_loss_test"):
        loss=[e for e in events if e["event_type"]=="LOSS"]
        if [e["active"] for e in loss]!=[1,0] or loss[1]["sim_time_us"]<=loss[0]["sim_time_us"]: raise ValueError("Missing radio-loss interval")
        if not any(f["node_id"]==2 and loss[0]["sim_time_us"]<=f["sim_time_us"]<=loss[1]["sim_time_us"] for f in frames): raise ValueError("No actual RF attempts during loss")
        if (2,2) in delivered or (2,2) in dropped or not any(e["event_type"]=="RX" and e["sender"]==2 and e["counter"]>2 for e in events): raise ValueError("Radio loss/recovery not established")
    if config.get("reorder_test"):
        order=[e["counter"] for e in events if e["event_type"]=="RX" and e["sender"]==2 and not e["duplicate"]]
        if 2 not in order or 3 not in order or order.index(3)>=order.index(2): raise ValueError("Actual receive reordering not observed")
    lifetime = None
    policy_switches = []
    policy_actions = []
    for e in events:
        if e["event_type"] == "SWITCH":
            policy_switches.append(e)
        if e["event_type"] == "POLICY":
            policy_actions.append(e)
    if config.get("lifetime"):
        from lifetime import lifetime_summary
        lifetime = lifetime_summary(events,config,clients,deceased,planned,delivered)
    network_energy = sum(v["total_nj"] for k,v in config.get("energy_reconciliation",{}).items() if int(k) in clients) if config.get("power_model") else None
    radio = radio_summary(frames)
    return {"security": "dual-profile return security test" if config.get("switch_test") else (cipher + " security test" if any(config.get(k) for k in ("attack_test","root_reset_test","sensor_reset_test","provision_fault","radio_loss_test","reorder_test","critical_reading")) else cipher + " authenticated pilot") if profile in (1, 2) else "N0: unprotected diagnostic pilot", "network_energy_nj":network_energy, "energy_per_delivered_reading_nj":network_energy/len(delivered) if network_energy is not None and delivered else None, "energy_window":"boot_to_horizon_including_warmup_and_drain" if network_energy is not None else None, "lifetime": lifetime, "stack_max_usage": stacks, "energy_measurement": {"scope":"component_model" if config.get("power_model") else "raw_counters_only", "model_validated":bool(config.get("energy_reconciliation")), "reconciliation":config.get("energy_reconciliation"), "samples":energy_samples} if config.get("energy_telemetry") else None, "security_test_injections": len(injections), "security_test_rejections": len(rejects), "rejection_reasons": rejection_reasons, "unique_authenticated_delivered": len(delivered) if profile in (1, 2) else 0, "generated": len(generated), "submitted_readings": len(transmitted), "explicit_drops": len(dropped), "unique_delivered": len(delivered), "missing_readings": len(expected - set(delivered)), "packets_submitted": len(packets), "packets_accepted": len(accepted_packets) if schema == 2 else None, "packet_pdr": len(accepted_packets) / len(packets) if schema == 2 and packets else None, "application_packet_bytes": sum(e["bytes"] for e in packets.values()), "reading_pdr": len(delivered) / len(expected) if expected else None, "p95_delay_ms": percentile(delays, .95), "max_hold_ms": max((p["hold_ms"] for p in packets.values()), default=0), "duplicates": duplicates, "batch_counts": sorted({p["count"] for p in packets.values()}), "radio": radio, "policy": {"total_policy_ticks": len(policy_actions), "measured_feature_events":len(measured_features), "profile_changes":sum(e["old_profile"]!=e["new_profile"] for e in policy_switches), "cap_changes":sum(e["old_cap"]!=e["new_cap"] for e in policy_switches), "startup_assignments":len({e["node_id"] for e in policy_actions}), "fallback_actions":sum(e["reason"] in (1,9,10) for e in policy_actions), "decision_and_apply_seconds":sum(policy_timing) if policy_timing else None, "timing_samples":len(policy_timing), "total_switches": len(policy_switches), "switch_reasons": {str(e["reason"]): sum(1 for s in policy_switches if s["reason"]==e["reason"]) for e in policy_switches}, "profiles_used": sorted({e["profile"] for e in policy_actions}), "caps_used": sorted({e["cap"] for e in policy_actions})} if policy_actions else None}
