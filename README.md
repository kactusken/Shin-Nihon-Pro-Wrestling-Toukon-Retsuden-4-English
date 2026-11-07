# Shin Nihon Pro Wrestling - Toukon Retsuden 4 — English Translation

An English translation patch for **Shin Nihon Pro Wrestling - Toukon Retsuden 4**, *(year, platform: DREAMCAST, released only in Japan)*.

*(What it covers, with real counts: modes, menus, roster, moves, graphics. One line on the
hardest technical part - a new font, a renderer hook.)*

**[See screenshots](docs/SCREENSHOTS.md)** of the patched game.

*(When `docs/guide/` exists, the line **[Player's guide](https://GITHUB_USER.github.io/REPO/guide/)** - the planned
address `announce.py` prints; write it before the repository exists. Delete this note otherwise.)*

> **Status: work in progress.** *(At release: "first public beta" - what is translated, what
> hasn't been played through yet, please report problems ([how to report](#reporting-problems)).
> [CHANGELOG.md](CHANGELOG.md) lists what's in each release.)*

## Downloads

Get the latest zip from the [Releases](../../releases) page. It contains *(N)* patches. Pick one:

| Patch | What you get |
|---|---|
| **Shin Nihon Pro Wrestling - Toukon Retsuden 4 (English)** | The translation, with the game otherwise unchanged. |

## How to patch

**[Follow the step-by-step guide](docs/HOW_TO_PATCH.md).** You patch the game with
[Delta Patcher](https://github.com/marco-calautti/DeltaPatcher/releases), then open the disc's
original `.cue`. Nothing needs renaming. *(A .bps cartridge ROM: Rom Patcher JS or Flips, no .cue.)*

You need your own copy of the original Japanese disc. Disc images are not provided here.

- Game: *Shin Nihon Pro Wrestling - Toukon Retsuden 4* (Japan), serial *(serial)*. *(Reissues that won't patch.)*
- The image must match: `Shin Nihon Pro Wrestling - Toukon Retsuden 4 (Japan) (Track 3).bin`, 1185760800 bytes, CRC32 `bdf46c1d`,
  SHA-1 `0229390c08f9003433de20d5335dde21cc2cb7c6`.

Other xdelta tools work too, such as [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) in a web browser (CD images;
it may not cope with a multi-GB DVD image) or `xdelta3` on the command line, but the patched files
must end up with the original file names. To keep several versions in one folder, use the patch's
`.cue` and name the patched files as it does.

Tested in *(emulator)*.

## Notes for players

- **Names.** *(real names, spellings)*
- **What's still in Japanese.** *(logos and other art, movies, audio, keyboards, credits, save title)*
- **Saves.** *(do saves from the original work?)*
- **Hidden content.** See [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md).

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
| [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md) | Unlockables, debug features, and unused and cut content |
| [tools/README.md](tools/README.md) | Every tool, what it's for and how to run it |

Quick start:

```sh
python3 tools/extract.py                 # unpack the disc in rom/ into extracted/
python3 build.py                         # -> build/Shin Nihon Pro Wrestling - Toukon Retsuden 4 (English).bin
python3 make_patches.py --version v0.1   # -> release/*.xdelta and a zip (needs xdelta3)
```

## AI disclosure

*(Required - FRAMEWORK.md section 11. A short generic line, e.g. "AI assisted with the
translation." Same wording as `AI_DISCLOSURE` in tools/paths.py.)*

## Legal

This is a non-commercial fan translation, not affiliated with or endorsed by the game's developers
or publishers. It contains no copyrighted game data that would let
anyone play without owning the game. The patches only work on your own copy of the disc.
Shin Nihon Pro Wrestling - Toukon Retsuden 4 and its contents belong to their respective owners. The Japanese text in this
repository is included for translation and reference.

The code in this repository is released under the [MIT License](LICENSE).
