# Patches

What the build changes besides text and images, one section per patch: what the original code
does, what changed, why it works, the tool that makes it, limits to respect, and whether it was
*verified in game*.

## unlock-wrestlers - every wrestler selectable
*Verified in game* (owner, 2026-11-07, test8: the hidden wrestlers on character select and in a match). Headless first:
Choshu, Saito, Sakaguchi, Tanaka and Hattori at the end of the New Japan group.

- **Original:** the lock test at `0x8C06C9D2` (wrestler id in r5) walks the list `0x8C0DEC91` (ids 15-19, 31, 41)
  and returns 1 - locked - when the id is in it and its bit in the system save's unlock word (`*0x8C1E1584 + 0x5C`)
  is clear. Character select, the modes' rosters and the Edit name link all ask it (10 callers).
- **Change:** its first two instructions become `rts; mov #0,r0` (`2DD7 00E6` -> `0B00 00E0`): nobody is locked.
- **Why this way:** nothing is written to the memory card, so taking the patch away brings the locks back, and a
  save from the original keeps working. The normal unlocks and the title codes still set their bits.
- **Limits:** none known; the hidden wrestlers have full model, voice and move data (they are the same as after a
  normal unlock).

## sapporo-music - the Sapporo venue's own music
*Seen headless* (2026-11-07, original image with the same bytes poked: in a match at Sapporo the sound buffer holds
SAPPOROL.P04 instead of YOKOHAMAL.P04); *verified in game* (owner, 2026-11-07, test8).

- **Original:** at match start (0x8C011444) the game plays BGM entry 62 + an arena index from 0x8C06C818 (the
  Options BGM setting: 0 = the venue's own, 1-8 a fixed venue, 9 random). Venue 7, Sapporo, plays entry 69, whose
  files are `yokohamal/r.p04`; no venue plays `SOUND/SAPPOROL/R.P04`, a 142-second track of its own.
- **Change:** entry 69's file names (strings at 0x8C0CDE18 / 0x8C0CDE28, used by no other entry) become
  `sapporol.p04` / `sapporor.p04`, and its length field (0x8C0DB248, in samples = 2 x one file's bytes, like the other
  arena entries) 6572672 -> 6266304. Volume and loop flags stay.
- **Limits:** the Yokohama-named track then plays nowhere (only Sapporo used it; the Yokohama venue plays
  `tokyoA_`). The Options BGM "Sapporo" choice and Random also get the new track.

## edit-theme8 - an eighth Edit entrance theme
*Seen headless* in the build (2026-11-07, `build.py --unlocks edit-theme8`: Edit Settings > Theme lists "Edit Theme 8"
after Edit Theme 7, choosing it stores 49 and the row shows its name; with the code poked into the original, X on
it streamed EDIT7NL/R.P04); *verified in game* (owner, 2026-11-07, test8: list, preview and entrance).

- **Original:** the entrance-theme list (stored as a u16 at edit record +0x474) offers the unlocked wrestlers'
  themes plus 7 edit themes (count 0x8C08B894 `add #7,r7`); list items map to theme numbers 0-51, skipping locked
  wrestlers' themes (0x8C06C312), and theme t is BGM entry t, labelled MENU STRINGS 469 + t. BGM entries 49-52 name
  `edit8n`-`edit11n`, which are not on the disc; `SOUND/SONGS/EDIT7NL/R.P04`, a 53-second tune, is unused.
- **Change:** entry 49's names become `edit7nl/r.p04` (one letter each); the count becomes +8; the list's select and
  label callbacks (0x8C08B92E-0x8C08B965) are repacked to make room for a helper that labels theme 49 with MENU
  STRINGS entry 3141 (unused in the original; the build adds "Edit Theme 8", or エディットのテーマ８ with
  `--no-translation`) and every other theme with 469 + t; the list's vtable (0x8C0EF3E8) and the settings row
  (0x8C08AC02) call it. The entrance and win music read the theme number directly and need no change (*from the code*).
- **Limits:** an edit wrestler saved with Edit Theme 8 and loaded in an unpatched game shows "Type A" as its
  theme and asks for the missing `edit8nl.p04` (not tested). No other patch may touch 0x8C08B92E-0x8C08B965.
