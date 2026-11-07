# How to Patch Shin Nihon Pro Wrestling - Toukon Retsuden 4

*(For players who have never patched a game: keep it this short. This is written for a .bin/.cue
disc: fill in the file counts and names, add a step for each extra patch such as `(Track 03).xdelta`,
then delete this note. No .cue: drop the .cue parts.)*

You patch *(how many)* of the disc's files, then open the disc's original `.cue`. Nothing needs renaming.

## What you need

- **Your own copy of the Japanese disc:** a folder with *(how many)* `.bin` files and one `.cue`
  file. Other formats, such as `.gdi` or `.chd`, won't work with these steps.
- **The patch:** download the zip from the *(releases page link)* and unzip it.
- **Delta Patcher:** download it from
  [its releases page](https://github.com/marco-calautti/DeltaPatcher/releases). It runs on Windows,
  macOS and Linux.

## Steps

These steps use the *(version)* version. For another version, pick the patch file with that
version's name instead. Delta Patcher changes the file you give it, so always work on a copy.

1. Copy your whole disc folder and work in the copy.
2. Open Delta Patcher and make the patch:
   - **Original file:** `Shin Nihon Pro Wrestling - Toukon Retsuden 4 (Japan) (Track 3).bin`
   - **XDelta patch:** `Shin Nihon Pro Wrestling - Toukon Retsuden 4 (English).xdelta`
   - Click **Apply patch** and wait for "Patch successfully applied!"
3. Open the `.cue` from the copied folder in your emulator. It has been tested in *(emulator)*.

The game should now be in English, even though the files still have their original names. Ignore
the `.cue` files in the patch zip: you only need them to keep several versions in one folder.

## If it goes wrong

Most problems come from a mixed-up file or a file that was already patched. The usual fix is to
make a fresh copy of your original folder and start again.

| What you see | Likely cause | Fix |
| --- | --- | --- |
| "The file you are trying to patch is not the right one" | The file is already patched, or your disc is a different dump | Check the file, then start again from a fresh copy |
| The game is still in Japanese | You opened the `.cue` in the original folder | Open the `.cue` in the copied folder |
| The patched file ends in "(patched)" | You used Rom Patcher JS, which adds that to the name | Use Delta Patcher, or rename the file back to its original name |
