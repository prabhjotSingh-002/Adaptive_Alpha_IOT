import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "host"))
from topologies import configure_layout, positions, validate_layout


class TopologyTests(unittest.TestCase):
    def test_legacy_preserved(self):
        for clients in (2, 8):
            sim = ET.parse(ROOT / "simulations/scenarios/phase1-rpl-9.csc").getroot().find("simulation")
            before = [ET.tostring(m) for m in sim.findall("mote")][:clients+1]
            configure_layout(sim, clients, "legacy")
            self.assertEqual(before, [ET.tostring(m) for m in sim.findall("mote")])

    def test_radio_graphs(self):
        for name, expected_edges in (("grid16", 24), ("tree16", 15)):
            points = positions(name)
            edges = [(i,j) for i in range(16) for j in range(i+1,16)
                     if sum((a-b)**2 for a,b in zip(points[i], points[j])) <= 50**2]
            self.assertEqual(len(edges), expected_edges)
            seen = {0}
            for _ in range(16):
                seen |= {j for i,j in edges if i in seen} | {i for i,j in edges if j in seen}
            self.assertEqual(len(seen), 16)
            if name == "tree16":
                self.assertEqual([e for e in edges if 0 in e], [(0,1)])
            sim = ET.parse(ROOT / "simulations/scenarios/phase1-rpl-9.csc").getroot().find("simulation")
            configure_layout(sim,15,name)
            ids = [int(i.find("id").text) for m in sim.findall("mote")
                   for i in m.findall("interface_config") if "MoteID" in (i.text or "")]
            self.assertEqual(ids, list(range(1,17)))

    def test_invalid_combinations(self):
        for args in ((15,"legacy"),(8,"grid16"),(15,"tree16","z1"),(15,"grid16","cooja",True)):
            with self.assertRaises(ValueError):
                validate_layout(*args)


if __name__ == "__main__":
    unittest.main()
