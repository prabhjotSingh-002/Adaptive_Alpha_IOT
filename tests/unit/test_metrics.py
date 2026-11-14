import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "host"))
from metrics import summarize, radio_summary
from parse_logs import parse

class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.config = {"period_ms":1000,"deadline_ms":3000,"readings_per_sensor":2,"reserved_bytes":16,"payload_budget":67}
        self.events = [
            {"node_id":2,"event_type":"READY","cap":1,"period_ms":1000,"deadline_ms":3000,"total":2},
            {"node_id":2,"event_type":"GEN","reading_id":1,"created_ms":60000,"value":201,"sim_time_ms":60250},
            {"node_id":2,"event_type":"GEN","reading_id":2,"created_ms":61000,"value":202,"sim_time_ms":61250},
            {"node_id":2,"event_type":"TX","counter":1,"count":1,"bytes":21,"hold_ms":0,"first_id":1,"last_id":1},
            {"node_id":2,"event_type":"TX","counter":2,"count":1,"bytes":21,"hold_ms":0,"first_id":2,"last_id":2},
            {"node_id":1,"event_type":"RX","sender":2,"counter":1,"reading_id":1,"created_ms":60000,"value":201,"duplicate":0,"sim_time_ms":60300},
            {"node_id":2,"event_type":"DONE","generated":2}]
    def result(self): return summarize(self.events,[],self.config,[2],1)
    def test_dynamic_policy_batch(self):
        self.config.update(profile=1, phase=5, mode='B6', policy_repair_version=1, mode_policy={'B6':2})
        policy={'node_id':2,'event_type':'POLICY','profile':1,'cap':2,'reason':5}
        self.events.insert(3,policy)
        tx=self.events[4]
        tx.update(count=2,bytes=47,last_id=2,profile=1)
        self.events[-2]["auth_ok"] = True
        self.events += [{"node_id":1,"event_type":"ROOT_READY","profile":1}, {"node_id":1,"event_type":"CONTEXT_READY","profile":1}, {"node_id":2,"event_type":"CONTEXT_READY","profile":1}]
        del self.events[5]
        self.assertEqual(self.result()['packets_submitted'],1)
        policy['cap']=1
        with self.assertRaises(ValueError): self.result()

    def test_known_delivery_and_global_latency(self):
        result=self.result(); self.assertEqual(result["reading_pdr"],.5); self.assertEqual(result["p95_delay_ms"],50); self.assertEqual(result["packets_submitted"],2)
    def test_duplicate_not_counted_twice(self):
        rx=copy.deepcopy(self.events[-2]);rx["duplicate"]=1;self.events.append(rx)
        self.assertEqual(self.result()["unique_delivered"],1); self.assertEqual(self.result()["duplicates"],1)
    def test_missing_generator_fails(self):
        del self.events[1]
        with self.assertRaises(ValueError): self.result()
    def test_missing_done_fails(self):
        self.events.pop()
        with self.assertRaises(ValueError): self.result()
    def test_bad_deadline_fails(self):
        self.events[3]["hold_ms"]=3001
        with self.assertRaises(ValueError): self.result()
    def test_corruption_fails(self):
        self.events[-2]["value"]=999
        with self.assertRaises(ValueError): self.result()
    def test_unlogged_submission_loss_fails(self):
        del self.events[4]
        with self.assertRaises(ValueError): self.result()
    def test_stale_config_fails(self):
        self.events[0]["cap"]=4
        with self.assertRaises(ValueError): self.result()
    def test_parse_incomplete_and_malformed(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"testlog";p.write_text("1,2,RSLAB,2,GEN,1,0,201\n")
            with self.assertRaises(ValueError):parse(p,"fixture")
            p.write_text("1,2,RSLAB,3,GEN,1,0,201\nPHASE2_COMPLETE\nTEST OK\n")
            with self.assertRaises(ValueError):parse(p,"fixture")
    def test_secure_accounting_requires_authentication_and_context(self):
        self.config["profile"] = 1
        for event in self.events:
            if event["event_type"] == "TX": event["bytes"] += 16
            if event["event_type"] == "RX": event["auth_ok"] = True
        self.events += [{"node_id":1, "event_type":"ROOT_READY", "profile":1},
                        {"node_id":1, "event_type":"CONTEXT_READY", "profile":1},
                        {"node_id":2, "event_type":"CONTEXT_READY", "profile":1}]
        self.assertEqual(self.result()["unique_authenticated_delivered"], 1)
        next(e for e in self.events if e["event_type"] == "RX")["auth_ok"] = False
        with self.assertRaises(ValueError): self.result()
    def test_ascon_accounting_and_unknown_profile(self):
        self.config["profile"] = 2
        for event in self.events:
            if event["event_type"] == "TX": event["bytes"] += 16
            if event["event_type"] == "RX": event["auth_ok"] = True
        self.events += [{"node_id":1, "event_type":"ROOT_READY", "profile":2},
                        {"node_id":1, "event_type":"CONTEXT_READY", "profile":2},
                        {"node_id":2, "event_type":"CONTEXT_READY", "profile":2}]
        self.assertEqual(self.result()["unique_authenticated_delivered"], 1)
        self.assertIn("Ascon", self.result()["security"])
        self.config["profile"] = 255
        with self.assertRaises(ValueError): self.result()
    def test_secure_packet_cannot_double_count_tag_budget(self):
        self.config.update(profile=1, payload_budget=37)
        for event in self.events:
            if event["event_type"] == "TX": event["bytes"] = 37
            if event["event_type"] == "RX": event["auth_ok"] = True
        self.events += [{"node_id":1, "event_type":"ROOT_READY", "profile":1},
                        {"node_id":1, "event_type":"CONTEXT_READY", "profile":1},
                        {"node_id":2, "event_type":"CONTEXT_READY", "profile":1}]
        self.assertEqual(self.result()["packets_submitted"], 2)
    def test_phase4_completion_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"testlog"
            p.write_text("1,2,RSLAB,2,DONE,2\nPHASE2_COMPLETE\nTEST OK\n")
            with self.assertRaises(ValueError): parse(p,"fixture",profile=2,phase=4)
            p.write_text("1,2,RSLAB,2,DONE,2\nPHASE4_COMPLETE\nTEST OK\n")
            self.assertEqual(len(parse(p,"fixture",profile=2,phase=4)[0]),1)
    def test_energy_telemetry_missing_regression_and_wrap(self):
        self.config["energy_telemetry"] = True
        with self.assertRaises(ValueError): self.result()
        for node in (1,2):
            self.events.append({"node_id":node,"event_type":"ENERGY_TIMER","frequency":32768,"bits":16})
            for time, ticks in ((125000,1),(250000,2)):
                self.events.append({"node_id":node,"event_type":"ENERGY_RAW","sim_time_us":time,
                                    "cpu":ticks,"lpm":ticks,"deep":0,"tx":0,"listen":ticks})
        self.assertFalse(self.result()["energy_measurement"]["model_validated"])
        self.events[-1]["cpu"] = 0
        with self.assertRaises(ValueError): self.result()
        self.events[-1]["cpu"] = 2
        self.events[-1]["sim_time_us"] = 2125000
        with self.assertRaises(ValueError): self.result()

    def test_schema2_packet_identity_and_metadata(self):
        self.config.update(profile=1, schema_version=2, config_id=7, dual_profile=True, switch_test=False)
        for e in self.events:
            if e["event_type"] in ("TX", "RX"):
                e.update(profile=1, epoch=1)
            if e["event_type"] == "TX": e["bytes"] += 16
            if e["event_type"] == "RX": e["auth_ok"] = True
        self.events += [{"node_id":1,"event_type":"ROOT_READY","profile":1}]
        for node in (1,2):
            self.events += [{"node_id":node,"event_type":"CONTEXT_READY","profile":1},
                            {"node_id":node,"event_type":"META2","config_id":7,"profile":1,"profile_count":2,"switch_test":0}]
        self.events += [{"node_id":1,"event_type":"PACKET","sender":2,"profile":1,"epoch":1,"counter":1}]
        self.assertEqual(self.result()["packet_pdr"], .5)
        next(e for e in self.events if e["event_type"] == "RX")["profile"] = 2
        with self.assertRaises(ValueError): self.result()

    def test_schema2_completion_and_legacy_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/"testlog"
            p.write_text("1,2,RSLAB,2,TX2,1,1,1,1,37,0,1,1\nPHASE4_SCHEMA2_COMPLETE\nTEST OK\n")
            self.assertEqual(parse(p,"fixture",1,4,2)[0][0]["profile"],1)
            with self.assertRaises(ValueError): parse(p,"fixture",1,4,1)
            p.write_text(p.read_text()+"PHASE4_COMPLETE\n")
            with self.assertRaises(ValueError): parse(p,"fixture",1,4,2)

    def test_protected_rejection_reason_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "testlog"
            p.write_text("1,1,RSLAB,1,REJECT_DETAIL,37,6\nPHASE4_COMPLETE\nTEST OK\n")
            event = parse(p, "fixture", profile=2, phase=4)[0][0]
            self.assertEqual(event["event_type"], "REJECT")
            self.assertEqual(event["reason"], 6)
            self.assertFalse(event["header_authenticated"])
            with self.assertRaises(ValueError): parse(p, "fixture", profile=0, phase=4)
            p.write_text("1,1,RSLAB,1,REJECT_DETAIL,37,0\nPHASE4_COMPLETE\nTEST OK\n")
            with self.assertRaises(ValueError): parse(p, "fixture", profile=2, phase=4)

    def test_radio_fragment_dispatch_at_mac_boundary(self):
        # Classic data frame, compressed PAN, short src/destination: header 9 bytes.
        prefix="418800cdab01000200"
        frames=[{"hex":prefix+"c0010001"},{"hex":prefix+"e001000101"},{"hex":prefix+"6000c0"}]
        result=radio_summary(frames)
        self.assertEqual(result["captured_frame_bytes"], sum(len(bytes.fromhex(f["hex"])) for f in frames))
        self.assertEqual(result["fragment_frames"],2);self.assertEqual(result["unclassified_data_frames"],0)
if __name__ == "__main__":unittest.main()
