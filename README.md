# CHIRP setup for generic VHF/UHF handhelds

One analog channel list (`channels.csv`) for:

| Radio | Choose in CHIRP | Memories | Name length |
|---|---|---|---|
| Quansheng UV-K5 (stock firmware) | Quansheng, UV-K5 | 200 | 10 |
| Baofeng UV-5R Mini | Baofeng, UV-5R Mini | 999 | 12 |
| Baofeng UV-25 | Baofeng, UV-25 | 1000 | 12 |

The list stays within 200 memories, the UV-K5's limit. Names are 10 characters or fewer, except some of your own,
which a UV-K5 shortens.

**Downloading works on a real UV-5R Mini. Uploading has not been tried on any radio.**

## What's in the list

| Memories | Channels |
|---|---|
| 1-18 | Your own channels (`mine`), as read from the UV-5R Mini on 28 Nov 2026; 14 (ISS) is receive only |
| 19-90 | Other south-east Queensland FM repeaters from the WIA directory (see below) |
| 91-100 | Marine VHF, receive only |
| 101-180 | UHF CB 1-80 (memory = 100 + channel), receive only |
| 181-188 | Central Highland Link Repeater System (off unless asked for) |

## Install CHIRP

**Ubuntu**

```bash
sudo apt install chirp
sudo usermod -aG dialout "$USER"   # then log out and in
```

Version 20251108 has drivers for all three radios. If `chirp` fails with `No module named 'chirp'`, an old per-user
launcher is shadowing the package: run `/usr/bin/chirp`, or delete `~/.local/bin/chirp` and `~/.local/bin/chirpc`.

**Windows:** install CHIRP-next from https://chirpmyradio.com, plus the driver for your cable (CH340 or Prolific).

## Program a radio from the command line

`radio.py` uses CHIRP's drivers; the CHIRP application is never opened. Radio names: `k5`, `mini`, `uv25`, or any CHIRP
radio id (for example `Quansheng_UV-K5_egzumer`).

Use a two-pin (K-plug) programming cable. Radio off, push the plug fully in, then turn it on.

```bash
./radio.py ports                                  # find the cable
./radio.py list --cb off                          # preview the channels
./radio.py program -r mini -p /dev/ttyUSB0        # back up, build, ask, upload
```

`program` saves the radio's current contents to `backups/` first, and prints the command that puts it back.

| Command | Does |
|---|---|
| `download -r R -p PORT -o file.img` | Read the radio |
| `build -r R -i file.img -o new.img` | Put the channels into a copy of a download (no radio needed) |
| `upload -r R -p PORT -i file.img` | Write an image to the radio |
| `check` | Check the channels against all three radios |

### Marine and UHF CB

`--marine on|off` and `--cb on|off` (both default on) work with `list`, `build` and `program`. When on, these
channels are **always receive only**, whatever the CSV says: these radios are not approved to transmit on either
service. When off, they are removed from the radio if this list put them there.

### Central Highland Link Repeater System

`--chlrs on` adds the eight link repeaters from the club's page; the default is `off`. Its 439.325 entry is already
memory 55. Tones are the club's, plus the WIA directory's 91.5 Hz for Blackdown. The directory marks Midge Point off
air since June 2024.

### The channel list

`channels.csv` is the single list: CHIRP's CSV columns plus `Group` (`mine`, `repeater`, `marine`, `cb`, `chlrs`). It also
imports into the CHIRP application. `--csv` takes another file or a public `https://` URL.

The script only touches the memory numbers in the list. Other memories and settings stay as they are.

## Updating the repeaters

The repeater group comes from the [WIA Australian Repeater Directory](https://www.wia.org.au/members/repeaters/data/),
currently the 25 September 2025 edition. It takes 2 m and 70 cm FM repeaters marked on air (`O` or `W`) around
Brisbane, Ipswich, the Gold and Sunshine Coasts, Toowoomba and the Downs, Gympie, Warwick and the South Burnett.

```bash
./wia.py "Repeater Directory.pdf" && ./radio.py check     # needs pdftotext (poppler-utils)
```

The Ipswich club's own repeaters come from
[its repeater page](https://ipswichradioclub.org.au/repeaters/) (read 28 Nov 2026), which wins over the directory; they
are the `CLUB` list in `wia.py`.

A channel has a transmit tone only where the directory lists one. Hand edits to repeater rows are overwritten.

## Per-radio notes

- **UV-K5:** CHIRP marks this driver experimental. Always keep the first download; it holds the radio's settings.
  - Custom firmware needs a different choice: for EGZUMER builds pick the `egzumer` variant of the UV-K5.
  - Newer hardware sold as UV-K5(8) or V3 with 7.03 firmware may need **Quansheng UV-K1** instead (not checked).
- **UV-5R Mini:** it is a different radio from the UV-5R. Don't pick "UV-5R".
- **UV-25:** check the label. Similar names (UV-25 Plus and others) may not match this driver.

## Changing channels

Edit `channels.csv`, then run `./radio.py check`. Every command refuses a channel that could transmit outside
144-148 MHz or 430-450 MHz.

## Before you transmit

Amateur channels need an amateur licence. Listen first. Directory entries can be out of date, so
confirm any repeater that doesn't respond.
