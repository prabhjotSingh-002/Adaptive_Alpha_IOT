import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'host'))
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
if __name__=='__main__':unittest.main()
