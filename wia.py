#!/usr/bin/env python3
"""Rebuild the repeater group in channels.csv from the WIA Australian Repeater Directory PDF (needs pdftotext)."""
import csv
import pathlib
import re
import subprocess
import sys

CSV = pathlib.Path(__file__).with_name("channels.csv")
AREA = re.compile(r"Brisbane|Ipswi|Gold Coast|Logan|Redcliffe|Sunshine Coast|Maleny|Toowoomba|T'mba|Darling Downs|"
                  r"Bunya|Springfield|Gympie|Warwick|South Burnett")
ROW = re.compile(r"\s*(\d+\.\d+)\s+(\d+\.\d+)\s+(VK4\w+)(.*?)\s([OTPXULW])\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)"
                 r"(?:\s+([\d,]+))?\s*$")
LAST_MEMORY = 80


def repeaters(pdf):
    """South-east Queensland 2 m and 70 cm FM repeaters that the directory marks as on air."""
    lines = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True
                           ).stdout.splitlines()
    found = []
    for heading in ("2 metre FM repeaters", "70cm FM repeaters"):
        start = next(i for i, line in enumerate(lines) if heading in line)
        start = next(i for i in range(start, len(lines)) if lines[i].strip() == "Queensland")
        end = next(i for i in range(start, len(lines)) if lines[i].strip() == "South Australia")
        for line in lines[start + 1:end]:
            if "VK4" not in line:
                continue
            match = ROW.match(line)
            if not match:
                sys.exit(f"cannot read this directory row, so nothing was changed:\n{line}")
            output, uplink, call, where, status, _erp, _hasl, _timeout, _sponsor, tone, _notes = match.groups()
            where = " ".join(where.split())
            if status in "OW" and output != uplink and AREA.search(where):
                found.append((float(output), float(uplink), call, where, None if tone == "-" else float(tone)))
    return sorted(found)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: wia.py REPEATER_DIRECTORY.pdf")
    found = repeaters(sys.argv[1])
    if not 0 < len(found) <= LAST_MEMORY:
        sys.exit(f"found {len(found)} repeaters; expected 1 to {LAST_MEMORY}")
    with open(CSV, newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    template = next(row for row in rows if row["Group"] == "repeater")
    new = []
    for number, (output, uplink, call, where, tone) in enumerate(found, 1):
        shift = round(uplink - output, 4)
        new.append(dict(template, Location=number, Name=f"{call[3:]}{output:.3f}"[:10], Frequency=f"{output:.6f}",
                        Duplex="+" if shift > 0 else "-", Offset=f"{abs(shift):.6f}", Tone="Tone" if tone else "",
                        rToneFreq=f"{tone or 88.5:.1f}", Comment=f"{call} {where}"))
    with open(CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(new + [row for row in rows if row["Group"] != "repeater"])
    print(f"{len(new)} repeaters written, {sum(not r[4] for r in found)} with no tone listed")


if __name__ == "__main__":
    main()
