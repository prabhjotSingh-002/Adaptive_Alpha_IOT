"""Normalize simulator-global RSLAB events; reject malformed/incomplete traces."""
import json
from pathlib import Path
FIELDS = {"GEN": ["reading_id", "created_ms", "value"], "TX": ["counter", "count", "bytes", "hold_ms", "first_id", "last_id"], "RX": ["sender", "counter", "reading_id", "created_ms", "value", "duplicate"], "DROP": ["reading_id", "reason"], "READY": ["cap", "deadline_ms", "period_ms", "total"], "DONE": ["generated"], "ROOT_READY": ["profile"], "ERROR": ["reason"], "REJECT": ["length"]}
FIELDS["REJECT_DETAIL"] = ["length", "reason"]
FIELDS["RX_AUTH"] = FIELDS["RX"]
FIELDS["RESET_PROBE"] = ["counter"]
FIELDS["INJECT"] = ["case"]
FIELDS["BOOT_REQUEST"] = ["profile"]
FIELDS["CONTEXT_READY"] = ["profile"]
FIELDS["ENERGY_MODEL"] = ["model_id", "total_nj", "remaining_nj"]
FIELDS["DEPLETED"] = ["total_nj"]
FIELDS["REMOVED"] = ["terminal"]
FIELDS["LOSS"] = ["active"]
FIELDS["CRITICAL"] = ["reading_id"]
FIELDS["SCHEDULE"] = ["local_ms", "warmup_ms", "period_ms", "total"]
FIELDS["STACK"] = ["reserved", "used"]
FIELDS["ROUTE"] = ["parent", "rank"]
FIELDS["ENERGY_TIMER"] = ["frequency", "bits"]
FIELDS["ENERGY_RAW"] = ["cpu", "lpm", "deep", "tx", "listen"]
FIELDS["META2"] = ["config_id", "profile", "profile_count", "switch_test"]
FIELDS["TX2"] = ["profile", "epoch"] + FIELDS["TX"]
FIELDS["RX2"] = ["sender", "profile", "epoch"] + FIELDS["RX"][1:]
FIELDS["PACKET2"] = ["sender", "profile", "epoch", "counter"]
FIELDS["POLICY_TIME"] = ["ticks", "frequency"]
FIELDS["POLICY"] = ["profile", "cap", "reason", "residual_nj", "oldest_hold_ms", "queue_count"]
FIELDS["FEATURE"] = ["rate_hz_x100", "samples", "age_ms"]
FIELDS["SWITCH"] = ["old_profile", "new_profile", "old_cap", "new_cap", "reason"]
def parse(path, run_id, profile=0, phase=None, schema=1):
    if profile not in (0, 1, 2): raise ValueError("Unsupported profile")
    text = Path(path).read_text()
    marker = "PHASE4_COMPLETE" if phase == 4 else "PHASE2_COMPLETE"
    if phase == 5: marker = "PHASE4_SCHEMA2_COMPLETE"
    if schema == 2 and phase not in (4, 5): raise ValueError("Schema 2 requires Phase 4 or 5")
    if schema == 2: marker = "PHASE4_SCHEMA2_COMPLETE"
    if schema not in (1, 2): raise ValueError("Unsupported schema")
    if "TEST OK" not in text.splitlines() or marker not in text.splitlines():
        raise ValueError("Incomplete/failed Cooja trace")
    if schema == 2 and any(line.startswith("PHASE") and line.endswith("COMPLETE") and line != marker for line in text.splitlines()):
        raise ValueError("Contradictory completion marker")
    events, frames = [], []
    for line in text.splitlines():
        if line.startswith("RADIO,"):
            _, time, node, raw = line.split(",", 3)
            frames.append({"sim_time_us": int(time), "node_id": int(node), "hex": raw})
            continue
        if ",RSLAB," not in line:
            continue
        timestamp, mote, payload = line.split(",", 2)
        prefix, node, kind, *values = payload.split(",")
        if prefix != "RSLAB" or int(mote) != int(node) or kind not in FIELDS or len(values) != len(FIELDS[kind]):
            raise ValueError("Malformed RSLAB event: " + line)
        event = {"run_id": run_id, "sim_time_us": int(timestamp), "sim_time_ms": int(timestamp) / 1000, "node_id": int(node), "event_type": kind}
        event.update(zip(FIELDS[kind], map(int, values)))
        if kind in ("META2", "TX2", "RX2", "PACKET2") and schema != 2:
            raise ValueError("Schema 2 event in legacy trace")
        if schema == 2 and kind in ("TX", "RX", "RX_AUTH"):
            raise ValueError("Legacy packet event in schema 2 trace")
        if kind in ("TX2", "RX2", "PACKET2"):
            if event["profile"] not in (1, 2) or event["epoch"] != 1:
                raise ValueError("Invalid packet context")
            event["event_type"] = {"TX2":"TX", "RX2":"RX", "PACKET2":"PACKET"}[kind]
            if kind == "RX2": event["auth_ok"] = True
        if kind == "REJECT_DETAIL":
            if profile not in (1, 2) or not 1 <= event["reason"] <= 7:
                raise ValueError("Invalid protected rejection reason")
            event["event_type"] = "REJECT"
            event["header_authenticated"] = False
        if kind in ("RX", "RX_AUTH"):
            if (kind == "RX_AUTH") != (profile in (1, 2)):
                raise ValueError("Received event inconsistent with configured security profile")
            event["event_type"] = "RX"
            event["auth_ok"] = kind == "RX_AUTH"
        events.append(event)
    if not events: raise ValueError("No RSLAB events")
    return events, frames
