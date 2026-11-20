"""Deterministic layouts using the existing native mote template and UDGM."""
from copy import deepcopy


def validate_layout(clients, topology, target="cooja", bottleneck=False):
    if topology == "legacy":
        if not 1 <= clients <= 8:
            raise ValueError("legacy layout supports 1–8 sensors")
    elif topology in ("grid16", "tree16"):
        if clients != 15 or bottleneck:
            raise ValueError("16-node layouts require --clients 15 and no --bottleneck")
        if target != "cooja":
            raise ValueError("16-node Z1 memory/stack qualification is pending; use --target cooja")
    else:
        raise ValueError("Unknown topology")


def positions(topology):
    if topology == "grid16":
        return [(38 * (i % 4), 38 * (i // 4)) for i in range(16)]
    if topology == "tree16":
        # Root -> single relay -> three disjoint chains (5, 5, 4 sensors).
        return ([(0, 0), (40, 0)] + [(40 + 40*i, 0) for i in range(1, 6)]
                + [(40, 40*i) for i in range(1, 6)]
                + [(40, -40*i) for i in range(1, 5)])
    raise ValueError("No generated coordinates for legacy layout")


def configure_layout(simulation, clients, topology):
    validate_layout(clients, topology)
    motes = simulation.findall("mote")
    if topology == "legacy":
        for mote in motes[clients + 1:]:
            simulation.remove(mote)
        return
    sensor_template = motes[1]
    for mote in motes:
        simulation.remove(mote)
    for index, (x, y) in enumerate(positions(topology)):
        mote = deepcopy(motes[0] if index == 0 else sensor_template)
        for interface in mote.findall("interface_config"):
            if "MoteID" in (interface.text or ""):
                interface.find("id").text = str(index + 1)
            if "Position" in (interface.text or ""):
                for axis, value in (("x", x), ("y", y), ("z", 0)):
                    interface.find(axis).text = str(value)
        simulation.append(mote)
