"""Verify firmware energy totals with the shared production C calculator."""
import subprocess

def reconcile(events,config,executable,nodes):
    model=config['power_model']; result={}
    for node in nodes:
        raw=[e for e in events if e['node_id']==node and e['event_type']=='ENERGY_RAW']
        logged=[e for e in events if e['node_id']==node and e['event_type']=='ENERGY_MODEL']
        # Allow exactly one trailing ENERGY_RAW at the horizon boundary (simulation
        # may terminate between the RAW emission and the subsequent MODEL emission).
        if not raw or len(raw) > len(logged)+1 or len(logged) > len(raw): raise ValueError('Missing model/counter snapshots')
        raw = raw[:len(logged)]  # discard the trailing unmatched horizon raw if present
        budget=config['energy_budget_nj'] if node!=1 and (not config['deplete_node'] or node==config['deplete_node']) else 2**64-1
        args=[str(executable),str(model['frequency']),str(model['millivolts']),*[str(n) for n in model['nanoamps']],str(budget)]
        text=''.join(' '.join(str(e[k]) for k in ('cpu','lpm','deep','tx','listen'))+'\n' for e in raw)
        run=subprocess.run(args,input=text,text=True,capture_output=True,check=True)
        rows=[[int(x) for x in line.split()] for line in run.stdout.splitlines()]
        computed=[row[0] for row in rows]
        if any(len(row)!=6 or sum(row[1:])!=row[0] for row in rows): raise ValueError("Component conservation failure")
        if computed!=[e['total_nj'] for e in logged] or any(e['model_id']!=model['id'] for e in logged): raise ValueError('Energy conservation/reconciliation failure')
        if any(e['remaining_nj']!=max(0,budget-e['total_nj']) for e in logged): raise ValueError('Residual budget mismatch')
        bounds=[]
        for adjustment in (-model["cpu_curve_uncertainty_nanoamps"],model["cpu_curve_uncertainty_nanoamps"]):
            varied=model["nanoamps"][:]; varied[0]+=adjustment
            sensitivity_args=[str(executable),str(model["frequency"]),str(model["millivolts"]),*[str(n) for n in varied],str(2**64-1)]
            sensitivity=subprocess.run(sensitivity_args,input=text,text=True,capture_output=True,check=True)
            bounds.append(int(sensitivity.stdout.splitlines()[-1].split()[0]))
        result[str(node)]={'total_nj':computed[-1], 'samples':len(raw),'reconciled':True,
                           'state_contributions_nj':dict(zip(('cpu_with_idle_radio','lpm_with_idle_radio','deep','tx_increment','listen_increment'),rows[-1][1:])),
                           'fixed_trace_cpu_current_sensitivity_nj':bounds}
    return result
