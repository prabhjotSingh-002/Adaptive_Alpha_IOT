"""Offline two-second action demand from causal queue and calibration inputs."""
from collections import deque

HORIZON_MS = 2000


def expected_batches(queued_ages_ms, next_arrival_ms, arrival_interval_ms,
                     cap, deadline_ms, horizon_ms=HORIZON_MS):
    """Project successful submissions with FIFO age, cap and deadline triggers.

    An unknown arrival interval is represented by None. The caller decides
    whether that state has enough evidence to support a forecast.
    """
    if (cap not in (1, 2, 4) or deadline_ms <= 0 or horizon_ms < 0
            or any(age < 0 for age in queued_ages_ms)
            or (next_arrival_ms is None) != (arrival_interval_ms is None)
            or (arrival_interval_ms is not None
                and (arrival_interval_ms <= 0 or next_arrival_ms < 0))):
        raise ValueError("Invalid queue projection inputs")
    if any(a < b for a, b in zip(queued_ages_ms, queued_ages_ms[1:])):
        raise ValueError("Queue ages must be in FIFO order")

    queue = deque(-age for age in queued_ages_ms)
    batches = []
    # The sensor drains the entire existing backlog when the cap shrinks
    # below occupancy, before processing the next generated reading.
    if len(queue) > cap:
        while queue:
            size = min(cap, len(queue))
            batches.append(size)
            for _ in range(size):
                queue.popleft()

    arrival = horizon_ms + 1 if next_arrival_ms is None else next_arrival_ms
    now = 0
    while True:
        if queue and (len(queue) >= cap or queue[0] + deadline_ms <= now):
            batches.append(len(queue))
            queue.clear()
        deadline = max(now, queue[0] + deadline_ms) if queue else horizon_ms + 1
        now = min(arrival, deadline)
        if now > horizon_ms:
            return tuple(batches)
        if arrival == now and arrival < deadline:
            queue.append(now)
            arrival += arrival_interval_ms


def forecast_bounds_nj(background, batches, packet_costs, current, candidate, transitions):
    """Sum calibrated (lower, upper) nJ bounds, or return None if unsupported."""
    if background is None:
        return None
    costs = [background, *(packet_costs.get((candidate, size)) for size in batches)]
    if current != candidate:
        costs.append(transitions.get((current, candidate)))
    if any(cost is None for cost in costs):
        return None
    if any(lower < 0 or upper < lower for lower, upper in costs):
        raise ValueError("Invalid energy bounds")
    return sum(cost[0] for cost in costs), sum(cost[1] for cost in costs)


def affordable(bounds, residual_nj):
    """Return None for unsupported or uncertain forecasts."""
    if bounds is None:
        return None
    lower, upper = bounds
    # The energy model marks depletion at zero remaining.
    if upper < residual_nj:
        return True
    if lower >= residual_nj:
        return False
    return None
