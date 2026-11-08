# Hidden content

Unlockables, debug features, button codes, cut and unused content. Every find says how sure it
is:

- *verified in game* - seen in an emulator (with the date, and the build or code used to get there)
- *seen headless* - seen running in the headless emulator (tools/emu.py) on the original image, not yet in a play-test
- *from the code* - read in the disassembly, not seen running
- *from the data* - in the game's files or tables, whether or not the code uses it
- *from a guide* / *from fans* - a published source, not yet matched with the code

Addresses: RAM addresses (`1ST_READ.BIN` is loaded at `0x8C010000`: file offset + 0x8C010000), disc paths for
files. Optional patches that switch some of this on are in [PATCHES.md](PATCHES.md).

**Prior art (2026-11-07).** An English GameFAQs FAQ (elbarto, 2001) lists the title-screen codes for the seven
hidden wrestlers and the analog-stick referee choice, without the normal unlock conditions. Japanese pages
(dc-station.com's 裏技 database, kakusi.jp) give the normal conditions, the referees and the CPU-logic trick;
dc-station misprints the SASUKE code as LXAYBYAR. No cheat-device codes (CodeBreaker, Xploder) and no
cut-content pages were found; The Cutting Room Floor could not be checked automatically. Everything below
"Searched in the data" is new.

## Contents
- [Hidden wrestlers](#hidden-wrestlers) · [Title-screen codes](#title-screen-codes) · [Hidden referees](#hidden-referees)
- [CPU-logic control in CPU vs CPU](#cpu-logic-control-in-cpu-vs-cpu) · [Edit names of locked wrestlers](#edit-names-of-locked-wrestlers)
- [Dead debug camera on controller C](#dead-debug-camera-on-controller-c)
- [Cut wrestler: Osamu Nishimura](#cut-wrestler-osamu-nishimura) · [Unused music](#unused-music)
- [The old Edit string table](#the-old-edit-string-table) · [Test move sets and unreached moves](#test-move-sets-and-unreached-moves)
- [Other leftovers](#other-leftovers) · [Searched and not found](#searched-and-not-found) · [How to see it yourself](#how-to-see-it-yourself)

## Hidden wrestlers
*from the code*, matching *from a guide* (dc-station.com, kakusi.jp); the unlock patch *verified in game* (2026-11-07, `build.py --unlocks unlock-wrestlers`)

Seven wrestlers are locked at first: Riki Choshu, Masa Saito, Seiji Sakaguchi, Hidekazu Tanaka (the ring
announcer), Tiger Hattori (the referee), Antonio Inoki and SASUKE (the heel Great Sasuke) - roster ids 15-19,
31 and 41 (list `0x8C0DEC91`). Each is unlocked by winning the last match of **Challenge the Burning Spirit**
(mode 18 singles / 19 tag, match-end routines `0x8C07377A` and `0x8C073B8C`) with a given wrestler; the
number of opponents chosen and the difficulty don't matter:

| Unlocks | Clear | with |
|---|---|---|
| Riki Choshu | Singles | Kensuke Sasaki |
| Antonio Inoki | Singles | Naoya Ogawa |
| SASUKE | Singles | The Great Sasuke |
| Masa Saito | Tag | a team with Riki Choshu |
| Seiji Sakaguchi | Tag | a team with Antonio Inoki |
| Tiger Hattori | Tag | a team with The Great Muta |
| Hidekazu Tanaka | Tag | a team with Power Warrior |

So Saito and Sakaguchi need Choshu and Inoki first. The unlocks are bits 0-6 of the u16 at
`*0x8C1E1584 + 0x5C`, saved at once in the memory card's system file (TOUKON4DCSYS) when one is loaded; the lock
test is `0x8C06C9D2`. The system save has no other unlock bits (no arenas, costumes, referees or modes), and
these two match-end routines are the only places that set them besides the codes below. Once unlocked, Choshu,
Saito, Sakaguchi, Tanaka and Hattori join the end of the New Japan group on character select (*seen headless*).

## Title-screen codes
*verified in game* (2026-11-07, L X Y B X Y B R; all eight *seen headless* on the original image: each code set its bit, a wrong code nothing)

On the "Press Start" title screen, on controller A: press L, then six of X/Y/A/B, then R. The reader is
`0x8C0799D8`; L clears the entry, R compares it with the table `0x8C0DFC58` (8 codes of 6 buttons). These are
all the codes there are.

| Code | Unlocks |
|---|---|
| L X Y B X Y B R | Riki Choshu |
| L X Y A X Y A R | Masa Saito |
| L X B X X B X R | Seiji Sakaguchi |
| L X Y X X Y X R | Hidekazu Tanaka |
| L X A X X A X R | Tiger Hattori |
| L X Y A B X Y R | Antonio Inoki |
| L X A Y B X A R | SASUKE |
| L X A A A A A R | all seven |

The all-seven code sets the whole word to 0xFF; nothing reads bit 7, so there is no eighth wrestler. With a
memory card in, the unlock is saved at once - take the card out to earn them the normal way later.

## Hidden referees
*verified in game* (2026-11-07, both sticks up = Sakaguchi); the table *from the code* (`0x8C026684`, at match load), matching *from a guide*

In a singles match, hold both analog sticks while the match loads (controllers A and B):

| A | B | Referee |
|---|---|---|
| up | up | Seiji Sakaguchi |
| down | up | Tanaka ("Kero") |
| up | down | Sachie Koike (Super J-Girls) |
| right | left | Hiroko Ito (Super J-Girls) |
| left | right | Nozomi Endo (Super J-Girls) |

The three Super J-Girls also have profiles; they are not wrestlers.

## CPU-logic control in CPU vs CPU
*from the code* (`0x8C026762`, `0x8C030462`, `0x8C0591C2`), matching *from a guide*

In a CPU vs CPU single match with an edit wrestler as wrestler 1, hold L on controller A while the match
loads. During the match A/B/X/Y on controller A then force that wrestler's thinking pattern 1-4 (the field
`+0xD3` of its CPU-logic object, which the game otherwise switches by situation at `0x8C04D35C`) - a
developer's way to watch an Edit thinking pattern.

## Edit names of locked wrestlers
*from the code* (`0x8C08AAC4`)

An edit wrestler named exactly like a preset is linked to him (record `+0x490`, used for the ring call). If that
wrestler is still locked, the name is quietly swapped for a look-alike from `0x8C0DF94C` (e.g. "長州  力" with
two spaces) so the link fails. An empty name becomes ヤングライオン (Young Lion). No secret names.

## Dead debug camera on controller C
*from the code*

A free camera at `0x8C01FBC0`-`0x8C020286` reads controller C (`pdGetPeripheral(12)`; everything else in the
game reads A or B) and moves the match camera with the D-pad, A/B/X/Y, L/R and Start. Nothing calls it or points
to it, so it can't be reached; restoring it needs a hook into the match loop and a third controller.

## Cut wrestler: Osamu Nishimura
*from the data*

`SOUND/SONGS/NISIMURAL.P04` / `NISIMURAR.P04` are Osamu Nishimura's entrance theme, which no BGM table entry
plays. Decoded, it is the same recording as `EDIT7L/R` (Edit theme 7) at half the volume - the cut wrestler's
theme was kept as the seventh edit theme. His name is also in the menu strings and the old Edit table has a
"西村コールポーズ" (Nishimura call pose); there is no model, voice or move set for him.

## Unused music
*from the data*, table *from the code* (BGM table `0x8C0DABC0`, 72 entries)

- `SOUND/SONGS/EDIT7NL/R.P04`: a different 53-second tune ("Edit 7 New") that nothing plays; the game plays `edit7`.
- `SOUND/SAPPOROL/R.P04`: a 142-second arena track nothing plays. A match plays BGM entry 62 + the venue
  (0x8C011444); the Sapporo venue gets entry 69, files `yokohama` (the Yokohama venue plays `tokyoA_`).
  Entries 70 (`k_hall`) and 71 (`tuika3`) are never played either (*from the code*). Restored by the
  `sapporo-music` patch (*verified in game*, 2026-11-07).
- `SOUND/SONGS/EDIT7NL/R.P04` can be added to the Edit themes as an eighth theme with the `edit-theme8` patch (*verified in game*, 2026-11-07).
- BGM entries 49-52 name edit themes 8-11 (`edit8n`-`edit11n`) that are not on the disc; the menu offers 1-7.
- Byte-identical copies under old names, unused: `SOUND/OSAKAAL/BL`, `TOKYOAL/BL/CL` (L and R) = `TUIKA1`;
  `NWOROGO` = `NWOLOGO` (misspelt).

## The old Edit string table
*seen headless* (2026-11-07, original image, Edit Settings) and *from the code*

`EDIT/STRINGS.PAC` (2700 entries) is never loaded: the only `strings.pac` name (`0x8C0CF694`) is loaded from
the MENU folder (`0x8C077048`), and in Edit mode RAM holds `MENU/STRINGS.PAC` at `0x8C6EDBA0` and no copy of the
Edit table. It is an older version of the menu table (633 entries are menu entries shifted by 581; 78 are
still `IDSTR_*` placeholders) with a roster from an earlier game - call poses for Norton, Scott and Rick Steiner,
Fujiwara, Nishimura, Wild Pegasus, Battle Liger, Delfin, Jinsei Shinzaki, Tiger Mask, Tiger King, and B-Chono /
B-Muto / Baby Muto - plus "立ちポ－ズ（未使用）" (Standing Pose (unused)), six "ＮＥＷ歩きVer 1.12" (New walk) entries
and ケロちゃん (Kero-chan). The translation covers it anyway, in case a hack restores it.

## Test move sets and unreached moves
*from the data*, readers *from the code* (`MOTION/ACTTBL.PAC`, read at `0x8C035480`)

- The move table has 50 rows of 600 slots but the game reads only rows 0-41 (one per preset). Rows 42-49 are
  copies of rows 0-7 with slots changed: row 42 (a Hashimoto copy, 51 slots) holds the newest moves - Fire
  Attack, Mochitsuki Michinoku Driver II, Mochitsuki Liger Bomb, Modified Exploder, X Suplex, Straddle Slap,
  Triangle Scorpion and more; row 45 (a Koshinaka copy, 104 slots) is a mix of other wrestlers' finishers; the
  rest are small reshuffles. Actions 283, 358, 383, 1169 and 1170 appear only there.
- 52 of the 1474 action scripts are reached from no preset, edit list or script follow-up (the code might still
  start some directly): among them 799 Chair Attack (イス攻撃; no constant for it in the code), 219 an older Green
  Mist, 754 an older Northern Lights Bomb, 984 a body pin on a face-down opponent, 318 Shoulder Tackle
  (rebound). The full list is in the project's research notes.
- Preset-only moves: the Edit move menu offers each slot a fixed list (190 lists at `0x8C0E6414`), and the
  presets break those lists 267 times with 116 different actions. 67 of them are in no Edit list at all - 62
  poses and entrance actions, and five attacks: Don Frye's Combo Punch / Punch / Sleeper (1066), SASUKE's Mounted
  Palm (1167/1168), Frye's and Ogawa's Mounted Punches (1171/1172). The other 49 are offered for some other slot
  but not where the preset uses them - e.g. Liger's Long-Hang Vertical Drop Brainbuster (782), Inoki's Original
  Enzuigiri (252) and Choke Sleeper (622), Kido's Kido Clutch (814), Tenryu's Lariat (1076).
- Slots 234/235 (kick-catch reversal, "catch kick, elbow") vary per wrestler and the Edit strings name the
  category, but the Edit move menu doesn't offer it. Entrance walk and ring-call poses (slots 496-512, 514) also
  vary but aren't editable.

## Other leftovers
*from the data* unless marked

- `EDIT/REGULAR/RE002.H`: a developer C header with the colour-swap tool's path,
  `C:\ﾃﾞｰﾀ\闘魂４\色替えツール\最終データ\regular\re002\re002.mdl` ("data\Toukon 4\colour-swap tool\final data").
- `KAIJO/RING_00.PAC`: a ring with a "ワールドプロレスリング" (World Pro-Wrestling, the TV show) apron, nothing loads
  it; its textures are also in `BVD_00`. Crowd sets `KYAKU00_0D`, `01_0`, `01_04_0`, `02_0D` are never loaded.
- The executable names `acttbldt.pac` and `999.p04`, which aren't on the disc; the one pointer to
  `acttbldt.pac` (`0x8C0D8AF4`) is never read - a dead developer loader (*from the code*).
- `ENTDATA/TELOP.PAC` has ファースト / ファイナル ("First" / "Final") banners that match no mode; whether anything
  draws them is open.
- Network mode: server addresses 210.251.115.12 / .13, protocol verbs (USRNEW, FUPLD, FGTCHT ...), modem and
  PPP state names and "Wellcome!!" - the service is long gone.
- `WRESTLER/DEKU_R/G/B.PAC` (木偶, a dummy figure in three colours) and `KAIJO/DUMMY.PAC` are loaded at boot; their
  use is unknown.

## Searched and not found
- Other button codes: the title-screen reader is the only sequence reader; no codes on character select, mode
  select, options or name entry (name entry has no password compares).
- Other unlocks: the system save's unlock word is the only unlock flag; no arena, costume, referee or mode unlocks.
- Modes: 22 mode objects (exhibition, the 17 saved modes, the Edit test match, network), all reachable; the
  main menu's 8 items are all shown.
- The "special match" byte `0x8C1E158C` is the Edit test match's situation (which move slot to try), not a list
  of hidden match types.
- Debug menus, sound test, test strings: none. The printf formats are UI text or the SDK's.
- Extra wrestlers: exactly 42 model sets and 43 voice banks (42 + edit); 45 profiles (42 + the Super J-Girls).
- Arenas and ring mats: all 8 arenas (with night versions) are selectable. No debug images in MENU, SPRITE or GAMEN.
- Not done: which MENU strings no code reads (ids also come from tables; needs a tracer), which of the 560
  announcer voices and 2166 motions are used, the Edit part numbers the menus can reach.

## How to see it yourself
| Find | How |
|---|---|
| Hidden wrestlers | the codes above, the Burning Spirit clears, or `python3 build.py --unlocks unlock-wrestlers` |
| Hidden referees | hold both analog sticks as a singles match loads |
| CPU-logic control | hold L on controller A as a CPU vs CPU match with an edit wrestler loads, then A/B/X/Y |
| Sapporo music | `python3 build.py --unlocks sapporo-music`, a match at the Sapporo venue |
| Edit Theme 8 | `python3 build.py --unlocks edit-theme8`, Edit > Edit Settings > Theme |
