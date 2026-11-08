# Shin Nihon Pro Wrestling - Toukon Retsuden 4 — English Translation

An English translation patch for **Shin Nihon Pro Wrestling - Toukon Retsuden 4**, Tomy's 1999
New Japan Pro-Wrestling game for the Dreamcast, released only in Japan.

Everything the player reads is in English: every menu and mode (Exhibition, IWGP Title Match,
Series Match with the G1 Climax and the other leagues, Challenge the Burning Spirit, Edit Wrestler,
the Wrestler Directory and Options), the rules and result banners, all 42 wrestlers' names and
profiles under their real names, and the 735 different move names in their move sets. 130
pictures with text - menu labels, headings, buttons and the in-match banners - are redrawn in
English. Edit Wrestler takes names of up to 16 letters, and its screens were laid out again for
the English.

**The hidden wrestlers, from the start.** Seven wrestlers - Riki Choshu, Masa Saito, Seiji
Sakaguchi, Antonio Inoki, SASUKE, the referee Tiger Hattori and the ring announcer Hidekazu
Tanaka - are locked until you clear Challenge the Burning Spirit with certain wrestlers. The
**(All Unlocked)** patches make them selectable at once, and add two pieces of music the game
has on the disc but never plays ([details](#notes-for-players)).

**[See screenshots](docs/SCREENSHOTS.md)** of the patched game.

**[Read the player's guide](https://kactusken.github.io/Shin-Nihon-Pro-Wrestling-Toukon-Retsuden-4-English/guide/)**: controls, how a match works, rules, modes, Edit Wrestler, strategy, all 42 wrestler profiles and every move set, and the secrets.

> **Status: v1.0, complete.** Every mode and screen was play-tested in Flycast over twelve
> rounds. Network Match could only be checked as far as dialing: the servers are long gone.
> Loading saves made with the Japanese game hasn't been tested. Please report anything that looks
> wrong ([how to report](#reporting-problems)). [CHANGELOG.md](CHANGELOG.md) lists what's in each
> release.

## Downloads

Get the latest zip from the [Releases](../../releases) page. It contains 3 xdelta patches. Pick one
(the same 3 are also in `Shin.Nihon.Pro.Wrestling.-.Toukon.Retsuden.4.English.Patch.v1.0.UDP-Patches.zip`
as `.dcp` files for [Universal Dreamcast Patcher](#how-to-patch)):

| Patch | What you get |
|---|---|
| **Shin Nihon Pro Wrestling - Toukon Retsuden 4 (English)** | The translation, with the game otherwise unchanged. |
| **Shin Nihon Pro Wrestling - Toukon Retsuden 4 (English) (All Unlocked)** | The translation with the seven hidden wrestlers selectable from the start, the Sapporo venue's own music and an eighth Edit entrance theme. |
| **Shin Nihon Pro Wrestling - Toukon Retsuden 4 (Japan) (All Unlocked)** | The original Japanese game with the same extras. |

## How to patch

**[Follow the step-by-step guide](docs/HOW_TO_PATCH.md).** You patch one of the disc's three files
with [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher/releases), then open the disc's
original `.cue`. Nothing needs renaming.

You need your own copy of the original Japanese disc. Disc images are not provided here.

- Game: *Shin Nihon Pro Wrestling - Toukon Retsuden 4* (Japan), serial T-28202M, a 3-track BIN/CUE dump (Redump).
- The main track must match: `Shin Nihon Pro Wrestling - Toukon Retsuden 4 (Japan) (Track 3).bin`, 1185760800 bytes, CRC32 `bdf46c1d`,
  SHA-1 `0229390c08f9003433de20d5335dde21cc2cb7c6`.

**Alternative:** the release also has a zip of all 3 patches as `.dcp` files for
[Universal Dreamcast Patcher](https://github.com/DerekPascarella/UniversalDreamcastPatcher/releases),
which patches a GDI, CUE/BIN or CHD in one step. See
[the guide](docs/HOW_TO_PATCH.md#alternative-universal-dreamcast-patcher).

Other xdelta tools work too, such as [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/)
in a web browser or `xdelta3` on the command line, but the patched file must end up with the
original file name. To keep several versions in one folder, use the patch's `.cue` and name the
patched files as it does.

Tested in [Flycast](https://github.com/flyinghead/flycast).

## Notes for players

- **Names.** The wrestlers use their real names as they are known in English, given name first
  (Keiji Muto, Hiroyoshi Tenzan, Jushin T. Liger). Where a field is tight, the surname or ring name.
- **What's still in Japanese.** The title logo, the movies, the staff credits, and the arena
  signs and ring gear drawn on the wrestlers and venues.
- **Saves.** The patches use the same save files as the Japanese game, so saves should carry
  over, but this hasn't been tested.
- **Network Match.** Its screens are in English, but the servers it dialed closed long ago.
- **(All Unlocked) patches.** The seven hidden wrestlers are selectable from the start; nothing is
  written to the memory card, so taking the patch out locks them again. The Sapporo venue plays
  its own music, which the original has on the disc but never plays (it reuses Yokohama's), and
  Edit Wrestler's entrance themes gain an eighth, from another unused tune.
- **Hidden content.** The title-screen codes, the hidden referees and what was cut are in
  [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md) and the guide's
  [Secrets](https://kactusken.github.io/Shin-Nihon-Pro-Wrestling-Toukon-Retsuden-4-English/guide/#secrets).

## Reporting problems

Open an [issue](../../issues) with:

- a screenshot,
- which patch you used,
- where you were: the mode and menu, or roughly what had just happened.

Text that is cut off, overlaps, or still shows Japanese is especially helpful.

## For ROM hackers and contributors

Everything needed to rebuild the patches from the original disc is in this repository: the
translated text, the patching code (Python 3, no dependencies for the build) and documentation of
the game's formats.

| Document | What's in it |
|---|---|
| [docs/HOW_TO_PATCH.md](docs/HOW_TO_PATCH.md) | The simplest way to patch your game, with no renaming |
| [docs/BUILDING.md](docs/BUILDING.md) | Setting up, building, making patches, and the checking tools |
| [docs/TRANSLATION.md](docs/TRANSLATION.md) | Text file formats, scope, style guide, glossary, and naming decisions |
| [docs/EDITING.md](docs/EDITING.md) | Editing the in-game text graphics |
| [docs/PATCHES.md](docs/PATCHES.md) | How each code patch works |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | The game's disc layout, archives, compression, data formats, and memory map |
| [docs/PLATFORM.md](docs/PLATFORM.md) | DREAMCAST pitfalls for this kind of work |
| [docs/guide/](https://kactusken.github.io/Shin-Nihon-Pro-Wrestling-Toukon-Retsuden-4-English/guide/) | The player's guide (one page; its wrestler and move tables come from `tools/guidedata.py`) |
| [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md) | Unlockables, debug features, and unused and cut content |
| [tools/README.md](tools/README.md) | Every tool, what it's for and how to run it |

Quick start:

```sh
python3 tools/extract.py                 # unpack the disc in rom/ into extracted/
python3 build.py                         # -> build/Shin Nihon Pro Wrestling - Toukon Retsuden 4 (English).bin
python3 make_patches.py --version v1.0   # -> release/*.xdelta and a zip (needs xdelta3)
```

## AI disclosure

AI assisted with the translation.

## Legal

This is a non-commercial fan translation, not affiliated with or endorsed by the game's developers
or publishers. It contains no copyrighted game data that would let
anyone play without owning the game. The patches only work on your own copy of the disc.
Shin Nihon Pro Wrestling - Toukon Retsuden 4 and its contents belong to their respective owners. The Japanese text in this
repository is included for translation and reference.

The code in this repository is released under the [MIT License](LICENSE).
