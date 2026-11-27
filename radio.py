#!/usr/bin/env python3
"""Program handhelds from channels.csv using CHIRP's drivers, without the CHIRP application."""
import argparse
import builtins
import csv
import datetime
import logging
import pathlib
import sys
import tempfile
import urllib.request
import warnings

# The CSV's Group column is ours, and CHIRP logs it as unknown.
logging.getLogger("chirp.drivers.generic_csv").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=FutureWarning, module="chirp")
builtins.__dict__.setdefault("_", lambda text: text)  # some CHIRP drivers expect gettext to be installed

try:
    import serial
    from serial.tools import list_ports
    from chirp import directory, import_logic
    from chirp.drivers import generic_csv
except ImportError as e:
    sys.exit(f"{e}\nInstall CHIRP's drivers: sudo apt install chirp")

HERE = pathlib.Path(__file__).resolve().parent
ALIASES = {"k5": "Quansheng_UV-K5", "mini": "Baofeng_UV-5R_Mini", "uv25": "Baofeng_UV-25"}
HAM = [(144e6, 148e6), (430e6, 450e6)]
RECEIVE_ONLY = {"marine", "cb"}


def load_channels(source, marine="on", cb="on", chlrs="off"):
    """Return (selected, left_out, source_features, own_numbers). Each entry is a CHIRP memory."""
    if source.startswith("https://"):
        local = pathlib.Path(tempfile.mkdtemp()) / "channels.csv"
        with urllib.request.urlopen(source, timeout=30) as response:
            local.write_bytes(response.read())
        source = str(local)
    with open(source, newline="", encoding="utf-8-sig") as f:
        groups = {int(row["Location"]): row["Group"] for row in csv.DictReader(f)}
    parsed = generic_csv.CSVRadio(source)
    off = {name for name, state in (("marine", marine), ("cb", cb), ("chlrs", chlrs)) if state == "off"}
    selected, left_out = [], []
    for number, group in sorted(groups.items()):
        mem = parsed.get_memory(number)
        if mem.empty:
            sys.exit(f"memory {number} in {source} did not load")
        if group in RECEIVE_ONLY:
            mem.duplex, mem.offset = "off", 0
        tx = mem.freq + {"+": mem.offset, "-": -mem.offset}.get(mem.duplex, 0)
        if mem.duplex != "off" and (mem.duplex not in ("", "+", "-") or not any(lo <= tx <= hi for lo, hi in HAM)):
            sys.exit(f"memory {number} {mem.name}: would transmit outside the amateur bands; set Duplex to off")
        (left_out if group in off else selected).append(mem)
    if len(groups) != len(selected) + len(left_out) or not selected:
        sys.exit(f"{source}: duplicate memory numbers, or nothing selected")
    return selected, left_out, parsed.get_features(), {number for number, group in groups.items() if group == "mine"}


def radio_class(name):
    directory.import_drivers()
    try:
        return directory.get_radio(ALIASES.get(name, name))
    except Exception:
        sys.exit(f"unknown radio {name!r}: use {', '.join(ALIASES)} or a CHIRP radio id")


def check(args):
    selected, _left_out, _features, own = load_channels(args.csv, chlrs="on")  # every group
    failures, shortened = [], []
    for name in ALIASES:
        radio = radio_class(name)(None)
        features = radio.get_features()
        for mem in selected:
            new = mem.dupe()
            new.power = features.valid_power_levels[0]
            errors = [m for m in radio.validate_memory(new) if m.__class__.__name__ == "ValidationError"]
            text = mem.name.rstrip()
            if errors:
                failures.append(f"{name} #{mem.number} {text}: {'; '.join(map(str, errors))}")
            elif not features.memory_bounds[0] <= mem.number <= features.memory_bounds[1]:
                failures.append(f"{name} #{mem.number} {text}: past the radio's last memory")
            elif mem.number in own and len(text) > features.valid_name_length:
                shortened.append(f"{name} #{mem.number} {text} -> {radio.filter_name(text).rstrip()}")
            elif len(text) > features.valid_name_length or radio.filter_name(text).rstrip() != text:
                failures.append(f"{name} #{mem.number} {text}: name would be shortened or altered")
            elif mem.duplex not in features.valid_duplexes:
                failures.append(f"{name} #{mem.number} {text}: duplex {mem.duplex!r} not supported")
        print(f"{name}: {len(selected)} channels checked")
    if shortened:
        print("your names that this radio will shorten:", *shortened, sep="\n  ")
    print("\n".join(failures) or "all passed")
    return 1 if failures else 0


def show(args):
    selected, left_out, _features, _own = load_channels(args.csv, args.marine, args.cb, args.chlrs)
    for m in selected:
        shift = {"off": "RX only", "": "simplex"}.get(m.duplex, f"{m.duplex}{m.offset / 1e6:g}")
        tone = f"{m.rtone} Hz" if m.tmode == "Tone" else ""
        print(f"{m.number:>4}  {m.name:<10}  {m.freq / 1e6:>10.4f}  {shift:<8} {m.mode:<4} {tone}")
    print(f"{len(selected)} channels, {len(left_out)} left out")


def build_image(radio_name, base, out, args):
    """Write the selected channels into a copy of a downloaded image."""
    cls = radio_class(radio_name)
    radio = directory.get_radio_by_image(str(base))
    wanted = (cls.VENDOR, cls.MODEL, cls.VARIANT)
    if (radio.VENDOR, radio.MODEL, radio.VARIANT) != wanted:
        sys.exit(f"{base} is a {radio.VENDOR} {radio.MODEL} image, not {radio_name}")
    selected, left_out, source_features, _own = load_channels(args.csv, args.marine, args.cb, args.chlrs)
    for mem in selected:
        radio.set_memory(import_logic.import_mem(radio, source_features, mem))
    # A slot is cleared only if it still holds the channel this list put there.
    cleared = 0
    for mem in left_out:
        current = radio.get_memory(mem.number)
        if not current.empty and current.freq == mem.freq:
            radio.erase_memory(mem.number)
            cleared += 1
    radio.save_mmap(str(out))
    print(f"{out}: {len(selected)} channels written, {cleared} cleared; other memories and settings unchanged")


class Port(serial.Serial):
    """CHIRP drivers expect the port to take trace messages."""

    def log(self, message):
        logging.getLogger("radio.serial").debug(message)


def open_radio(cls, port):
    line = Port(baudrate=cls.BAUD_RATE, rtscts=cls.HARDWARE_FLOW, timeout=0.25)
    line.dtr, line.rts = cls.WANTS_DTR, cls.WANTS_RTS
    line.port = port
    line.open()
    return cls(line)


def progress(status):
    print(f"\r{status.msg} {status.cur}/{status.max}   ", end="", file=sys.stderr, flush=True)


def download_image(radio_name, port, out):
    if not str(out).endswith(".img"):
        sys.exit("the image file name must end in .img")
    radio = open_radio(radio_class(radio_name), port)
    radio.status_fn = progress
    try:
        radio.sync_in()
        radio.save_mmap(str(out))
    finally:
        radio.pipe.close()
    print(f"\nsaved {out}")


def upload_image(radio_name, port, image, assume_yes):
    cls = radio_class(radio_name)
    loaded = directory.get_radio_by_image(str(image))
    if (loaded.VENDOR, loaded.MODEL, loaded.VARIANT) != (cls.VENDOR, cls.MODEL, cls.VARIANT):
        sys.exit(f"{image} is a {loaded.VENDOR} {loaded.MODEL} image, not {radio_name}")
    if not assume_yes and input(f"Write {image} to the radio on {port}? [y/N] ").strip().lower() != "y":
        sys.exit("not written")
    radio = open_radio(cls, port)
    radio.status_fn = progress
    try:
        radio.load_mmap(str(image))
        radio.sync_out()
    finally:
        radio.pipe.close()
    print("\nupload finished; power the radio off and on")


def program(args):
    """Back up the radio, build from that backup, upload."""
    folder = HERE / "backups"
    folder.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup, new = folder / f"{args.radio}-{stamp}.img", folder / f"{args.radio}-{stamp}-new.img"
    download_image(args.radio, args.port, backup)
    build_image(args.radio, backup, new, args)
    upload_image(args.radio, args.port, new, args.yes)
    print(f"to undo: radio.py upload -r {args.radio} -p {args.port} -i {backup}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    channels = argparse.ArgumentParser(add_help=False)
    channels.add_argument("--csv", default=str(HERE / "channels.csv"), help="file or https:// URL")
    channels.add_argument("--marine", choices=["on", "off"], default="on", help="marine channels (receive only)")
    channels.add_argument("--cb", choices=["on", "off"], default="on", help="UHF CB channels (receive only)")
    channels.add_argument("--chlrs", choices=["on", "off"], default="off", help="Central Highlands link repeaters")
    radio = argparse.ArgumentParser(add_help=False)
    radio.add_argument("-r", "--radio", required=True, help="k5, mini, uv25 or a CHIRP radio id")
    port = argparse.ArgumentParser(add_help=False)
    port.add_argument("-p", "--port", required=True, help="for example /dev/ttyUSB0 or COM3")
    yes = argparse.ArgumentParser(add_help=False)
    yes.add_argument("-y", "--yes", action="store_true", help="don't ask before writing to the radio")

    def add(name, run, parents, text):
        sub = commands.add_parser(name, parents=parents, help=text)
        sub.set_defaults(run=run)
        return sub

    add("ports", lambda a: print("\n".join(f"{p.device}  {p.description}" for p in list_ports.comports()
                                           if p.hwid != "n/a") or "no serial ports found"), [], "list serial ports")
    add("list", show, [channels], "show the channels that would be written")
    add("check", check, [channels], "check the channels against all three radios")
    add("download", lambda a: download_image(a.radio, a.port, a.out), [radio, port], "read the radio to an image"
        ).add_argument("-o", "--out", required=True)
    build = add("build", lambda a: build_image(a.radio, a.image, a.out, a), [radio, channels],
                "put the channels into a downloaded image (no radio needed)")
    build.add_argument("-i", "--image", required=True)
    build.add_argument("-o", "--out", required=True)
    add("upload", lambda a: upload_image(a.radio, a.port, a.image, a.yes), [radio, port, yes],
        "write an image to the radio").add_argument("-i", "--image", required=True)
    add("program", program, [radio, port, channels, yes], "back up, build and upload in one step")

    args = parser.parse_args()
    return args.run(args) or 0


if __name__ == "__main__":
    sys.exit(main())
