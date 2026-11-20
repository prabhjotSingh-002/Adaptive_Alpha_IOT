"""Prospective sensor demand shared by runner and lifetime analysis."""


def scheduled_offsets_ms(config):
    """Return generation offsets and the first slot after the workload."""
    period = config["period_ms"]
    middle_period = config.get("middle_period_ms", period)
    total = config["readings_per_sensor"]
    third = total // 3
    offset = config["warmup_ms"]
    offsets = []
    for index in range(total):
        offsets.append(offset)
        # The sensor increments generated before choosing the next interval.
        generated = index + 1
        offset += middle_period if third <= generated < 2 * third else period
    return offsets, offset


def run_horizon_ms(config):
    _, end = scheduled_offsets_ms(config)
    return end + config["deadline_ms"] + config["drain_ms"]
