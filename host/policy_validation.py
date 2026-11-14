"""Fail closed on policy configuration outside firmware representations."""
def validate_policy_config(config):
    if config.get('phase') != 5:
        return
    widths = {'b3_threshold_nj_hi':64,'b3_threshold_nj_lo':64,
              'p1_transition_cost_nj':64,'p1_margin_nj':64,'p1_min_dwell_ms':32,
              'payload_budget':8,'reserved_bytes':8}
    for key,bits in widths.items():
        value=config.get(key)
        if type(value) is not int or not 0 <= value < 2**bits:
            raise ValueError('Invalid policy field: '+key)
    if config['b3_threshold_nj_lo'] >= config['b3_threshold_nj_hi']:
        raise ValueError('Policy thresholds require low < high')
    if type(config.get('b6_profile')) is not int or config['b6_profile'] not in (1,2):
        raise ValueError('Invalid B6 profile')
    costs=config.get('p1_cost_nj',[[0]*3 for _ in range(2)])
    if not isinstance(costs,list) or len(costs)!=2 or any(not isinstance(row,list) or len(row)!=3 or any(type(v) is not int or not 0<=v<2**64 for v in row) for row in costs):
        raise ValueError('Invalid policy cost table')
