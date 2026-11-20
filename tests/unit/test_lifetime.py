import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'host'))
from demand_schedule import run_horizon_ms, scheduled_offsets_ms
from lifetime import lifetime_summary
class LifetimeTests(unittest.TestCase):
    def case(self,n=3,dead=None,delivered=None):
        clients=list(range(2,n+2))
        config={'warmup_ms':0,'period_ms':1000,'readings_per_sensor':30,'deadline_ms':0,'drain_ms':15000}
        events=[{'event_type':'SCHEDULE','node_id':i,'sim_time_ms':0,'local_ms':0,'warmup_ms':0,'period_ms':1000,'total':30} for i in clients]
        planned={(i,r) for i in clients for r in range(1,31)}
        if delivered is None: delivered={(i,r):{'sim_time_ms':(r-1)*1000+100} for i,r in planned}
        return lifetime_summary(events,config,clients,dead or {},planned,delivered)
    def test_no_death_censored_not_observed(self):
        result=self.case();self.assertFalse(result['fnd']['event']);self.assertTrue(result['hnd']['censored']);self.assertEqual(result['fnd']['time_ms'],45000);self.assertFalse(result['functional']['event'])
    def test_odd_even_hnd_and_simultaneous_deaths(self):
        for n in (3,4):
            result=self.case(n,{2:{'sim_time_ms':10000},3:{'sim_time_ms':10000}})
            self.assertEqual(result['hnd']['time_ms'],10000);self.assertTrue(result['hnd']['event'])
    def test_persistent_service_loss_and_planned_denominator(self):
        result=self.case(delivered={});self.assertEqual(result['functional']['crossing_ms'],15000);self.assertEqual(result['functional']['confirmation_ms'],25000);self.assertEqual(result['scheduled_shortfall'],90)
    def test_middle_period_schedule_matches_sensor_segment_boundaries(self):
        config = dict(warmup_ms=60000, period_ms=500, middle_period_ms=4000,
                      readings_per_sensor=27, deadline_ms=3000, drain_ms=15000)
        offsets, end = scheduled_offsets_ms(config)
        self.assertEqual(offsets[:9], list(range(60000, 64500, 500)))
        self.assertEqual(offsets[9:18], list(range(68000, 104000, 4000)))
        self.assertEqual(offsets[18:], list(range(100500, 105000, 500)))
        self.assertEqual(end, 105000)
        self.assertEqual(run_horizon_ms(config), 123000)
if __name__=='__main__':unittest.main()
