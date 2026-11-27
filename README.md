# IADRC channel list for handheld radios

A ready-made analog channel list for members of the Ipswich and District Radio Club (VK4WIP), in
[`channels.csv`](https://raw.githubusercontent.com/bwhite001/chirp-handhelds/main/channels.csv).

| Radio | Choose in CHIRP | Memories | Name length |
|---|---|---|---|
| Quansheng UV-K5 (stock firmware) | Quansheng, UV-K5 | 200 | 10 |
| Baofeng UV-5R Mini | Baofeng, UV-5R Mini | 999 | 12 |
| Baofeng UV-25 | Baofeng, UV-25 | 1000 | 12 |

**How far it has been tested:** on a real UV-5R Mini and a real UV-25, the command line tool has read, written and
read back the list with an exact match. Loading it through the CHIRP application has not been tried, and nor has a UV-K5. Save your radio's contents first (step 2 below) so you can put them back.

## What's in the list

| Memories | Channels |
|---|---|
| 1-18 | Club core channels: local repeaters, simplex calling, SSTV, ISS (receive only), WICEN |
| 19-70 | Other south-east Queensland FM repeaters |
| 81-84 | WICEN simplex: base 438.975, check points 439.250, 439.175, 439.025 |
| 91-100 | Marine VHF, receive only |
| 101-180 | UHF CB 1-80 (memory = 100 + channel), receive only |
| 181-188 | Central Highland Link Repeater System |

**Never turn on transmit for the marine or UHF CB channels.** These radios are not approved for either service.

A UV-K5 shortens the longer names; `WICEN-RPTR2m` and `WICEN-RPTR70` both show as `WICEN-RPTR`.

## Load it with the CHIRP application (Windows, Linux or Mac)

You need a two-pin (Kenwood style, "K-plug") programming cable. The USB socket on a battery or radio may only charge.

These steps are not for F4HWN firmware (see below).

1. Install CHIRP from https://chirpmyradio.com. Windows may also need the driver for your cable (CH340 or Prolific).
2. Radio off, push the plug fully in, turn it on. In CHIRP: **Radio > Download from radio**, choose the port, vendor and
   model. Then **File > Save** and keep that file: it is your way back.
3. With it open, **File > Import** and choose `channels.csv`. This replaces whatever is in memories 1-188 that the list
   uses, including all the groups above.
4. **Radio > Upload to radio**. Don't unplug until it finishes, then turn the radio off and on.

CHIRP may report an unknown `Group` column; the command-line tool below uses it.

## Or use the command line (Linux)

`radio.py` uses CHIRP's drivers without opening the application. It has been run on Ubuntu only.

```bash
sudo apt install chirp
sudo usermod -aG dialout "$USER"       # then log out and in
git clone https://github.com/bwhite001/chirp-handhelds.git && cd chirp-handhelds
./radio.py ports                       # find the cable
./radio.py program -r mini -p /dev/ttyUSB0
```

`program` backs up the radio to `backups/`, builds the new contents, asks before writing, and prints the command that
puts the old contents back. Radio names are `k5`, `mini`, `uv25`, or any CHIRP radio id.

| Command | Does |
|---|---|
| `list` | Show the channels that would be written |
| `download -r R -p PORT -o file.img` | Read the radio |
| `build -r R -i file.img -o new.img` | Put the channels into a copy of a download (no radio needed) |
| `upload -r R -p PORT -i file.img` | Write an image to the radio |
| `check` | Check the list against all three radios |

Options for `list`, `build` and `program`:

| Option | Default | Effect |
|---|---|---|
| `--marine on\|off` | on | Marine channels, always receive only |
| `--cb on\|off` | on | UHF CB channels, always receive only |
| `--chlrs on\|off` | off | Central Highland link repeaters |

Only the memory numbers in the list are touched. Turning a group off removes it from the radio if this list put it
there.

## UV-K5 V3 / UV-K1 with F4HWN firmware

**Do not load `channels.csv` into this radio with the CHIRP application.** F4HWN has no receive-only channel, so marine
and UHF CB come out able to transmit.

Use the command line tool, which blocks transmit properly or saves nothing. It needs F4HWN's own driver module matching
your firmware version. For v5.9.0 that is
[`f4hwn.fusion.chirp.v5.9.0.py`](https://github.com/armel/uv-k1-k5v3-firmware-custom/releases/tag/v5.9.0)
(SHA-256 `09d23891a6dc44478cb3e8fd16e1f00fdf33673b4e2faffae765ad812b3a0ff2`); put it in `modules/`.

```bash
./radio.py --module modules/f4hwn.fusion.chirp.v5.9.0.py program -r module -p /dev/ttyUSB0 --f-lock-ca
```

- `--f-lock-ca` sets the radio's **F Lock to CA HAM (144-148, 430-450)**. The firmware transmits on a channel unless
  both F Lock disallows the frequency and the channel's TX Lock is on. The tool turns TX Lock on for every channel it
  writes. Don't change F Lock or turn TX Lock off afterwards.
- Without it you can only load with `--marine off --cb off`.
- Memory 14 (ISS) is left out: its frequency is inside the 2 m band, so receive only can't be enforced.

## Which radio to pick

- **UV-K5:** CHIRP marks this driver experimental.
  - Custom firmware needs a different choice: for EGZUMER builds pick the `egzumer` variant.
  - Newer hardware sold as UV-K5(8) or V3 with stock 7.03 firmware may need **Quansheng UV-K1** instead (not checked).
  - F4HWN firmware v5 or later: see the section above.
- **UV-5R Mini:** it is a different radio from the UV-5R. Don't pick "UV-5R".
- **UV-25:** check the label. Similar names (UV-25 Plus and others) may not match this driver.

## Where the information comes from

- Club repeaters: the [club's repeater page](https://ipswichradioclub.org.au/repeaters/), read 28 Nov 2026. It wins
  over the directory.
- Other repeaters: the [WIA Australian Repeater Directory](https://www.wia.org.au/members/repeaters/data/), 25 September
  2025 edition: 2 m and 70 cm FM marked on air around Brisbane, Ipswich, the Gold and Sunshine Coasts, Toowoomba and
  the Downs, Gympie, Warwick and the South Burnett.
- Link repeater tones: the club page, plus the directory's 91.5 Hz for Blackdown. The directory marks Midge Point
  (146.800) off air since June 2024.

Details go out of date. If a repeater doesn't respond, check it, and please report the correction as a GitHub issue.

## Maintaining the list

`channels.csv` is CHIRP's CSV format plus the `Group` column (`core`, `repeater`, `wicen`, `marine`, `cb`, `chlrs`). After
editing it, run `./radio.py check`. Every command refuses a channel that could transmit outside 144-148 MHz or
430-450 MHz.

To rebuild the `repeater` group from a newer directory (needs `pdftotext`, from poppler-utils):

```bash
./wia.py "Repeater Directory.pdf" && ./radio.py check
```

This keeps the `core` channels first and overwrites hand edits to `repeater` rows. The club's repeaters are the `CLUB`
list in `wia.py`.

## Before you transmit

You need an amateur licence for the amateur channels. Listen first.
