import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'host'))
from mechanism_checks import policy_wire,root_reset,depletion

class MechanismTests(unittest.TestCase):
    def reset_events(self):
        return [dict(node_id=1,event_type='BOOT_REQUEST',sim_time_us=0),
                dict(node_id=1,event_type='RX',sim_time_us=1000,auth_ok=True),
                dict(node_id=1,event_type='BOOT_REQUEST',sim_time_us=2000),
                dict(node_id=2,event_type='RESET_PROBE',sim_time_us=3000),
                dict(node_id=1,event_type='REJECT',sim_time_us=4000,reason=4)]
    def test_root_reset_requires_probes_locked_rejections_and_no_accept(self):
        es=self.reset_events();self.assertEqual(root_reset(es)['post_reset_acceptances'],0)
        with self.assertRaises(ValueError):root_reset([e for e in es if e['event_type']!='RESET_PROBE'])
        es[-1]['reason']=6
        with self.assertRaises(ValueError):root_reset(es)
        es=self.reset_events()+[dict(node_id=1,event_type='PACKET',sim_time_us=5000)]
        with self.assertRaises(ValueError):root_reset(es)
    def test_policy_tx_rx_and_measured_features_are_checked(self):
        cfg={'mode':'P1','mode_policy':{'P1':3}}
        es=[dict(node_id=2,event_type='FEATURE',rate_hz_x100=0,samples=0,age_ms=2**32-1,sim_time_ms=0),
            dict(node_id=2,event_type='POLICY',profile=1,cap=1,reason=6),
            dict(node_id=2,event_type='GEN',created_ms=0,sim_time_ms=1),
            dict(node_id=2,event_type='TX',profile=1,epoch=1,counter=1,count=1,first_id=1,last_id=1),
            dict(node_id=1,event_type='RX',sender=2,profile=1,epoch=1,counter=1,reading_id=1,auth_ok=True)]
        self.assertEqual(policy_wire(es,cfg)['authenticated_packets_matched_to_tx'],1)
        bad=copy.deepcopy(es);bad[-1]['profile']=2
        with self.assertRaises(ValueError):policy_wire(bad,cfg)
        bad=copy.deepcopy(es);bad[0]['rate_hz_x100']=100
        with self.assertRaises(ValueError):policy_wire(bad,cfg)
        bad=copy.deepcopy(es);bad[3]['count']=2
        with self.assertRaises(ValueError):policy_wire(bad,cfg)
    def test_depletion_checks_energy_close_and_terminal_rf(self):
        es=[dict(node_id=2,event_type='ENERGY_MODEL',remaining_nj=0,total_nj=100,sim_time_us=1000),
            dict(node_id=2,event_type='DEPLETED',total_nj=100,sim_time_us=2000),
            dict(node_id=2,event_type='REMOVED',terminal=1,sim_time_us=2000)]
        c={'energy_budget_nj':100,'deplete_node':0};r={'2':{'reconciled':True,'total_nj':100}}
        self.assertEqual(depletion(es,[],c,r)['depleted_nodes'],[2])
        with self.assertRaises(ValueError):depletion(es,[dict(node_id=2,sim_time_us=2001)],c,r)
        es[0]['remaining_nj']=1
        with self.assertRaises(ValueError):depletion(es,[],c,r)
