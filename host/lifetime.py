"""Lifetime/service events over a fixed battery-node population and demand."""
import math

def lifetime_summary(events,config,clients,deceased,planned,delivered):
    horizon=config['warmup_ms']+config['period_ms']*config['readings_per_sensor']+config['deadline_ms']+config['drain_ms']
    deaths=sorted(e['sim_time_ms'] for e in deceased.values())
    def event_at(index):
        return {'event':len(deaths)>=index,'time_ms':deaths[index-1] if len(deaths)>=index else horizon,'censored':len(deaths)<index}
    schedules={e['node_id']:e for e in events if e['event_type']=='SCHEDULE'}
    if set(schedules)!=set(clients): raise ValueError('Missing prospective demand schedule')
    demand=[]
    for n in clients:
        e=schedules[n]
        if (e['warmup_ms'],e['period_ms'],e['total'])!=(config['warmup_ms'],config['period_ms'],config['readings_per_sensor']): raise ValueError('Demand mismatch')
        offset=e['sim_time_ms']-e['local_ms']
        demand.extend(((n,r),offset+config['warmup_ms']+(r-1)*config['period_ms']) for r in range(1,e['total']+1))
    # Frozen engineering service definition: 10s cohort, 5s delivery bound,
    # <95% service persisting for 10s, evaluated at 1s resolution.
    crossing=None; confirmed=None; observed_crossing=None
    for t in range(config['warmup_ms']+15000,horizon+1,1000):
        cohort=[(key,created) for key,created in demand if t-15000 < created <= t-5000]
        if not cohort: crossing=None; continue
        good=sum(key in delivered and delivered[key]['sim_time_ms']<=created+5000 for key,created in cohort)
        if good / len(cohort) < .95:
            if crossing is None: crossing=t
            if t-crossing>=10000:
                observed_crossing=crossing; confirmed=t; break
        else: crossing=None
    return {'battery_nodes':list(clients),'fnd':event_at(1),'hnd':event_at(math.ceil(len(clients)/2)),
            'functional':{'event':confirmed is not None,'crossing_ms':observed_crossing,'confirmation_ms':confirmed,'censor_ms':horizon if confirmed is None else None},
            'scheduled_readings':len(planned),'scheduled_delivered':len(delivered),'scheduled_shortfall':len(planned)-len(delivered),
            'service_window_ms':10000,'service_persistence_ms':10000,'delivery_bound_ms':5000,'service_minimum':.95}
