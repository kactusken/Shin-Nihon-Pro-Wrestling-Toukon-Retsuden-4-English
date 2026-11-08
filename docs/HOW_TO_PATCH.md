# How to Patch Shin Nihon Pro Wrestling - Toukon Retsuden 4

You patch one of the disc's three files, then open the disc's original `.cue`. Nothing needs renaming.

## What you need

- **Your own copy of the Japanese disc:** a folder with 3 `.bin` files and one `.cue` file. Other
  formats, such as `.gdi` or `.chd`, won't work with these steps (see
  [the alternative](#alternative-universal-dreamcast-patcher) below).
- **The patch:** download the zip from the
  [releases page](https://github.com/kactusken/Shin-Nihon-Pro-Wrestling-Toukon-Retsuden-4-English/releases)
  and unzip it.
- **Delta Patcher:** download it from
  [its releases page](https://github.com/marco-calautti/DeltaPatcher/releases). It runs on Windows,
  macOS and Linux.

## Steps

These steps use the English version. For another version, pick the patch file with that
version's name instead. Delta Patcher changes the file you give it, so always work on a copy.

1. Copy your whole disc folder and work in the copy.
2. Open Delta Patcher and make the patch:
   - **Original file:** `Shin Nihon Pro Wrestling - Toukon Retsuden 4 (Japan) (Track 3).bin`
   - **XDelta patch:** `Shin Nihon Pro Wrestling - Toukon Retsuden 4 (English).xdelta`
   - Click **Apply patch** and wait for "Patch successfully applied!"
3. Open `Shin Nihon Pro Wrestling - Toukon Retsuden 4 (Japan).cue` from the copied folder in your
   emulator. It has been tested in [Flycast](https://github.com/flyinghead/flycast).

The game should now be in English, even though the files still say "Japan". Ignore the `.cue`
files in the patch zip: you only need them to keep several versions in one folder.

## Alternative: Universal Dreamcast Patcher

If you would rather patch in one step, the release also has
**`Shin.Nihon.Pro.Wrestling.-.Toukon.Retsuden.4.English.Patch.v1.0.UDP-Patches.zip`**, with the same 3
patches as `.dcp` files for
[Universal Dreamcast Patcher](https://github.com/DerekPascarella/UniversalDreamcastPatcher/releases)
(UDP). UDP takes a GDI, a CUE/BIN or a CHD of the Japanese disc, so it also works if your disc is
not the 3-file BIN/CUE. Unzip it; the patches are named like the xdelta ones:

- `Shin Nihon Pro Wrestling - Toukon Retsuden 4 - English v1.0.dcp`
- `Shin Nihon Pro Wrestling - Toukon Retsuden 4 - English v1.0 (All Unlocked).dcp`
- `Shin Nihon Pro Wrestling - Toukon Retsuden 4 - Japanese v1.0 (All Unlocked).dcp`, the Japanese game with the extras

1. Open Universal Dreamcast Patcher and go to the patching tab.
2. **Source disc image:** your Japanese disc's `.cue` (or `.gdi`, `.chd`). UDP leaves the original alone.
3. **Patch file:** the `.dcp` you want.
4. **Output folder:** any folder. **Patched disc image format:** the one your emulator wants.
5. Click **Apply Patch**. The patched disc is written to a subfolder named after the patch file.
   Open its `.cue`, `.gdi` or `.chd` in your emulator.

Use only one method per disc: do not apply a `.dcp` to a disc that an xdelta patch has changed.

## If it goes wrong

Most problems come from a mixed-up file or a file that was already patched. The usual fix is to
make a fresh copy of your original folder and start again.

| What you see | Likely cause | Fix |
| --- | --- | --- |
| "The file you are trying to patch is not the right one" | The file is already patched, or your disc is a different dump | Check the file, then start again from a fresh copy |
| The game is still in Japanese | You opened the `.cue` in the original folder | Open the `.cue` in the copied folder |
| The patched file ends in "(patched)" | You used Rom Patcher JS, which adds that to the name | Use Delta Patcher, or rename the file back to its original name |
