# Hidden content

Unlockables, debug features, button codes, cut and unused content. Every find says how sure it
is:

- *verified in game* - seen in an emulator (with the date, and the build or code used to get there)
- *from the code* - read in the disassembly, not seen running
- *from the data* - in the game's files or tables, whether or not the code uses it
- *from a guide* / *from fans* - a published source, not yet matched with the code

Addresses: [say how - RAM or file offsets, `$bank:addr` for cartridges, overlay names].
Optional patches that switch some of this on are in [PATCHES.md](PATCHES.md).

**Prior art ([date]).** [What The Cutting Room Floor, Data Crystal, GameFAQs, fan wikis, cheat
code databases and guidebooks say - or that there is nothing. Which finds below were already
known; everything else is new.]

## Contents
- [Find](#find) · [Searched and not found](#searched-and-not-found) · [How to see it yourself](#how-to-see-it-yourself)

## [Find]
*verified in game* ([date], `build.py --unlocks group`) / *from the code*

What it is and what it does, how it's reached in the original (or that it can't be), where it
lives (address, file), and a screenshot in `screenshots/` when there is one. Say when a release
patch can't reach it (needs dev-kit hardware, SRAM edits, a test image).

## Searched and not found
What was checked and came up empty, so nobody searches again: button-code readers, name-entry
passwords, unreached menu entries, unused files, never-set flags.

## How to see it yourself
| Find | How |
|---|---|
| [find] | `python3 build.py --unlocks group` / the "(All Unlocked)" patch / a RAM poke / a cheat code |
