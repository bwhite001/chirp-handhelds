# CHIRP setup for generic VHF/UHF handhelds

One analog channel list (`channels.csv`) for:

| Radio | Choose in CHIRP | Memories | Name length |
|---|---|---|---|
| Quansheng UV-K5 (stock firmware) | Quansheng, UV-K5 | 200 | 10 |
| Baofeng UV-5R Mini | Baofeng, UV-5R Mini | 999 | 12 |
| Baofeng UV-25 | Baofeng, UV-25 | 1000 | 12 |

The list stays within 200 memories and 10-character names, the UV-K5's limits.

**Not yet tried on a real radio.** The list is checked against CHIRP's drivers only.

## What's in the list

| Memories | Channels |
|---|---|
| 1-33 | South-east Queensland FM repeaters, with access tones |
| 34, 35 | 146.500 and 439.000 simplex |
| 51-60 | Marine VHF, receive only |
| 101-180 | UHF CB 1-80 (memory = 100 + channel), receive only |

These radios must not transmit on marine or UHF CB. Those memories have transmit turned off (`Duplex = off`); leave it
that way.

## Install CHIRP

**Ubuntu**

```bash
sudo apt install chirp
sudo usermod -aG dialout "$USER"   # then log out and in
```

Version 20251108 has drivers for all three radios. If `chirp` fails with `No module named 'chirp'`, an old per-user
launcher is shadowing the package: run `/usr/bin/chirp`, or delete `~/.local/bin/chirp` and `~/.local/bin/chirpc`.

**Windows:** install CHIRP-next from https://chirpmyradio.com, plus the driver for your cable (CH340 or Prolific).

## Program a radio

Use a two-pin (Kenwood style, "K-plug") programming cable. The USB socket on a battery or radio may only charge.

1. Radio off, push the cable fully in, then turn it on. A half-seated plug is the usual cause of "no response".
2. In CHIRP: **Radio > Download from radio**. Pick the port (`/dev/ttyUSB0` or `COMx`), vendor and model.
3. **File > Save** the download as `backups/<radio>-<date>.img` before changing anything. This is your way back.
4. With that image open: **File > Import**, choose `channels.csv`.
5. **Radio > Upload to radio**. Don't unplug until it finishes.
6. Turn the radio off, unplug, turn it on and check a few channels.

Backup from the command line:

```bash
/usr/bin/chirpc -r Baofeng_UV-5R_Mini -s /dev/ttyUSB0 --mmap backups/mini.img --download-mmap
```

The radio ids are `Quansheng_UV-K5`, `Baofeng_UV-5R_Mini` and `Baofeng_UV-25`.

## Per-radio notes

- **UV-K5:** CHIRP marks this driver experimental. Always keep the first download; it holds the radio's settings.
  - Custom firmware needs a different choice: for EGZUMER builds pick the `egzumer` variant of the UV-K5.
  - Newer hardware sold as UV-K5(8) or V3 with 7.03 firmware may need **Quansheng UV-K1** instead (not checked).
- **UV-5R Mini:** it is a different radio from the UV-5R. Don't pick "UV-5R".
- **UV-25:** check the label. Similar names (UV-25 Plus and others) may not match this driver.

## Changing channels

Edit `channels.csv` (or open it in CHIRP), then:

```bash
python3 check.py
```

It fails if any channel would be rejected or changed by one of the three drivers, or could transmit outside
144-148 MHz or 430-450 MHz.

## Before you transmit

Amateur channels need an amateur licence. Listen first. The repeater list and tones were copied from a DM-32UV codeplug
on 28 Nov 2026, so confirm any repeater that doesn't respond.
