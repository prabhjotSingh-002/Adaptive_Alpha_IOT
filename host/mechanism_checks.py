"""Raw-event acceptance checks; unit fixtures are never research results."""

def policy_wire(events, config):
    policy = {}; features = {}; generations = {}; packets = {}; actions = []
    feature_count = 0
    active = config.get('mode_policy', {}).get(config.get('mode'), 0)
    if not active: return None
    for e in events:
        node, kind = e['node_id'], e['event_type']
        if kind == 'GEN':
            state = generations.setdefault(node, {'last':None, 'intervals':[], 'global':None})
            if state['last'] is not None:
                delta = (e['created_ms'] - state['last']) & 0xffffffff
                if delta > 0x7fffffff: state['intervals'] = []
                elif delta: state['intervals'] = (state['intervals']+[delta])[-8:]
            state['last'] = e['created_ms']; state['global'] = e['sim_time_ms']
        if kind == 'FEATURE':
            state = generations.get(node, {'last':None,'intervals':[],'global':None})
            intervals = state['intervals']; n = len(intervals); total = sum(intervals)
            expected = min(65535,100000*n//total) if total else 0
            stale = max(1000,2*total//n) if n else 1000
            if e['age_ms'] > stale: expected = 0
            if e['samples'] != n or e['rate_hz_x100'] != expected:
                raise ValueError('Measured traffic feature differs from generated intervals')
            if state['global'] is None:
                if e['age_ms'] != 0xffffffff: raise ValueError('Invalid startup rate age')
            elif abs(e['age_ms'] - (e['sim_time_ms']-state['global'])) > 125:
                raise ValueError('Measured traffic feature age mismatch')
            features[node] = e; feature_count += 1
        if kind == 'POLICY':
            if node not in features: raise ValueError('Policy before measured-feature identity')
            policy[node] = e; actions.append(e)
        if kind == 'TX':
            a = policy.get(node)
            if a is None or e['profile'] != a['profile'] or e['count'] > a['cap']:
                raise ValueError('Sealed TX differs from active policy')
            key=(node,e['profile'],e['epoch'],e['counter'])
            if key in packets: raise ValueError('Repeated sealed packet identity')
            packets[key]=e
    received = set()
    for e in events:
        if e['event_type'] != 'RX': continue
        key=(e['sender'],e['profile'],e['epoch'],e['counter'])
        if not e.get('auth_ok') or key not in packets:
            raise ValueError('Authenticated RX has no matching sealed TX/policy')
        tx=packets[key]
        if not tx['first_id'] <= e['reading_id'] <= tx['last_id']:
            raise ValueError('Authenticated reading outside sealed packet range')
        received.add(key)
    switches=[e for e in events if e['event_type']=='SWITCH']
    previous_wire = {}; wire_changes = 0
    for e in packets.values():
        n=e['node_id']
        if n in previous_wire and previous_wire[n]!=e['profile']: wire_changes+=1
        previous_wire[n]=e['profile']
    return {'measured_feature_events':feature_count,'sealed_packets_matched_to_policy':len(packets),
            'authenticated_packets_matched_to_tx':len(received),
            'tx_profiles':sorted({e['profile'] for e in packets.values()}),
            'rx_profiles':sorted({p[1] for p in received}),
            'profile_changes':sum(e['old_profile']!=e['new_profile'] for e in switches),
            'wire_profile_changes':wire_changes,
            'cap_changes':sum(e['old_cap']!=e['new_cap'] for e in switches),
            'startup_assignments':len({e['node_id'] for e in actions}),
            'fallback_actions':sum(e['reason'] in (1,9,10) for e in actions),
            'scope':'measured local traffic and cost-aware policy; residual-aware P1 ranking unvalidated'}


def root_reset(events):
    roots=[e for e in events if e['event_type']=='BOOT_REQUEST' and e['node_id']==1]
    if len(roots)!=2: raise ValueError('Root reset requires two actual root boots')
    cutoff=roots[-1]['sim_time_us']
    before=[e for e in events if e['event_type']=='RX' and e['sim_time_us']<cutoff and e.get('auth_ok')]
    probes=[e for e in events if e['event_type']=='RESET_PROBE' and e['node_id']==2 and e['sim_time_us']>=cutoff]
    rejects=[e for e in events if e['event_type']=='REJECT' and e['node_id']==1 and e['sim_time_us']>=cutoff]
    if not before or not probes or not rejects: raise ValueError('Missing pre-reset control/post-reset probe/rejection')
    if any(e['event_type'] in ('RX','PACKET','CONTEXT_READY','ROOT_READY') and e['node_id']==1 and e['sim_time_us']>=cutoff for e in events):
        raise ValueError('Root accepted/reactivated after reset without a fresh grant')
    if any(e.get('reason')!=4 for e in rejects): raise ValueError('Post-reset rejection is not locked-context refusal')
    return {'reset_boot_us':cutoff,'authenticated_readings_before_reset':len(before),'post_reset_probes':len(probes),
            'locked_context_rejections':len(rejects),'post_reset_acceptances':0,
            'scope':'fail-closed reset without regrant; no availability/recovery claim'}


def depletion(events, frames, config, reconciliation):
    dead={e['node_id']:e for e in events if e['event_type']=='DEPLETED'}
    removed={e['node_id']:e for e in events if e['event_type']=='REMOVED'}
    if dead.keys()!=removed.keys(): raise ValueError('Missing terminal removal')
    for node,e in dead.items():
        models=[x for x in events if x['event_type']=='ENERGY_MODEL' and x['node_id']==node]
        if not models or models[-1]['remaining_nj']!=0 or models[-1]['total_nj']!=e['total_nj'] or e['total_nj']<config['energy_budget_nj']:
            raise ValueError('Final exhausted energy sample mismatch')
        account=reconciliation.get(str(node),reconciliation.get(node,{}))
        if not account.get('reconciled') or account['total_nj']!=e['total_nj']:
            raise ValueError('Terminal total does not match production-C reconciliation')
        if any(x['node_id']==node and x['event_type'] in ('GEN','TX','POLICY','FEATURE','CONTEXT_READY','BOOT_REQUEST') and x['sim_time_us']>e['sim_time_us'] for x in events):
            raise ValueError('Application activity after terminal depletion')
        if any(f['node_id']==node and f['sim_time_us']>removed[node]['sim_time_us'] for f in frames):
            raise ValueError('Radio/forwarding activity after node removal')
    return {'depleted_nodes':sorted(dead),'removed_nodes':sorted(removed),'post_death_application_or_rf_violations':0,
            'bounded_budget_nodes':'all sensors' if not config.get('deplete_node') else [config['deplete_node']],
            'root_budget':'unbounded','scope':'component-model terminal mechanism; no comparative lifetime gain claim'}
