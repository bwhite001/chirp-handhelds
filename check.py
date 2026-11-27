#!/usr/bin/env python3
"""Check channels.csv against each radio's CHIRP driver. Usage: python3 check.py [CHIRP_SOURCE_DIR]"""
import pathlib
import sys

sys.path[1:1] = sys.argv[1:]
from chirp import directory
from chirp.drivers import generic_csv

RADIOS = [("Quansheng", "UV-K5"), ("Baofeng", "UV-5R Mini"), ("Baofeng", "UV-25")]
HAM = [(144e6, 148e6), (430e6, 450e6)]

directory.import_drivers()
source = generic_csv.CSVRadio(str(pathlib.Path(__file__).with_name("channels.csv")))
low, high = source.get_features().memory_bounds
memories = [m for m in (source.get_memory(n) for n in range(low, high + 1)) if not m.empty]
failures = []
for vendor, model in RADIOS:
    cls = next(c for c in directory.DRV_TO_RADIO.values() if (c.VENDOR, c.MODEL) == (vendor, model))
    radio = cls(None)
    features = radio.get_features()
    for mem in memories:
        problem = None
        new = mem.dupe()
        new.power = features.valid_power_levels[0]
        errors = [m for m in radio.validate_memory(new) if m.__class__.__name__ == "ValidationError"]
        tx = new.freq + {"+": new.offset, "-": -new.offset}.get(new.duplex, 0)
        name = mem.name.rstrip()
        if errors:
            problem = "; ".join(map(str, errors))
        elif not features.memory_bounds[0] <= mem.number <= features.memory_bounds[1]:
            problem = "past the radio's last memory"
        elif len(name) > features.valid_name_length or radio.filter_name(name).rstrip() != name:
            problem = "name would be shortened or altered"
        elif new.duplex not in features.valid_duplexes:
            problem = f"duplex {new.duplex!r} not supported"
        elif new.duplex != "off" and not any(lo <= tx <= hi for lo, hi in HAM):
            problem = f"can transmit on {tx / 1e6} MHz, outside the amateur bands"
        if problem:
            failures.append(f"{model} #{mem.number} {mem.name}: {problem}")
    print(f"{vendor} {model}: {len(memories)} channels checked")
print("\n".join(failures) or "all passed")
sys.exit(1 if failures or not memories else 0)
