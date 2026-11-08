# Translation

## Where the text is

| File | Holds | Checked by |
|---|---|---|
| `translation/text/*.txt` | `strings.txt`: MENU/STRINGS.PAC (menus, help lines, profiles, move names); `exe.txt`: strings in 1ST_READ.BIN; `edit_strings.txt`: EDIT/STRINGS.PAC (never loaded by the game) | `tools/lint.py` |
| `translation/text/champions.csv` | names in the champion and tournament histories (tools/records.py) | `tools/lint.py` |
| `translation/text/rooms.csv` | measured room for exe strings whose limit isn't their slot | `tools/lint.py` |
| `translation/graphics.csv` | images with text | `tools/check.py` |

## File formats

Message blocks: `@ id`, source lines (`JP `), translation lines (`EN `); no `EN` lines = original
kept. A file's header says what it holds and its limits (`# limit lines=3 chars=28` is checked by
lint). Tables: original columns beside English ones (`japanese`/`english`, or `X`/`en_X`). See
`tools/blocks.py` and `tools/textdb.py`.

Control codes: none; printf codes (`%d`, `%s`) in the exe strings are kept in order.

## Style guide

- Name order, romanization: given name first, Hepburn without macrons (see Style decisions below).
- The game has no story dialogue: help lines are imperative sentences in sentence case; labels in Title Case.
- Line and box limits: a letter takes half a Japanese character cell, so a 20-character line holds
  40 letters; each block's `# fit` line gives its limit, checked by lint. Move names: 32 letters at most.

## Glossary

`translation/glossary.csv` (`japanese, english, notes`): lint warns when a source line contains a
term and the English doesn't use its translation (several accepted forms: `A | B`). Prefer
established community names (existing English guides) over new coinages.

## Decisions

See *Scope* and *Style decisions* below (owner decisions with their dates).

## What stays untranslated

The title logo (owner's choice), the movies and staff credits (scope), and the arena signs and
wrestler gear textures (owner, play-test round 9).

## Scope (decided 2026-11-06)
- Translated: all text and menus, including text drawn as images.
- Stays Japanese: movies and credits only.
- Names: wrestlers use their real names as known in English (e.g. Keiji Muto, Hiroyoshi Tenzan).

## Style decisions (2026-11-06; owner answered 2026-11-07: title logo stays Japanese; surnames in tight fields, terms, literal abbreviations and Liger's joke birth date approved; name readings with no source and the save message to be judged in game)
- Names: real names, given name first, Hepburn without macrons; short forms (surname / ring name) where a field is tight.
- Move names: the usual English fan names; a wrestler's own version is written "(Surname)".
- Network mode terms: federation (団体), Inter-Federation Match (交流戦), Found Federation (旗揚げ), Join (入門), Transfer (移籍).
- 本部席裁定 = Table Ruling; 前口上 = Entrance Speech (label "Intro" where 6 letters); ぷるぷるぱっく = Jump Pack;
  異種格闘技 = MMA Rules (rule value) / Cross-Style Match (banner).
- Help text: imperative, sentence case, period. Labels: Title Case. ASCII only; printf codes kept in order.
- Owner, round 1 (2026-11-07): Options labels CPU Level, Show Names, Show Moves, Show Stamina; CPU level セメント = Aggressive
  (everywhere); camera 特リン = Ring; BGM values Venue Std, Tokyo A/B/C, Yokohama, Osaka A/B, Fukuoka, Sapporo; menu
  labels Burning Spirit, Edit Wrestler, Elimination, Go Back, banner Exhibition; button 変更 = Edit; HUD / character
  select short name 獣神Ｔ・ライガー = Jushin T. Liger.
- Owner, round 3 (2026-11-07): 結果 button = Skip (the game picks the winner); banners IWGP Heavyweight / IWGP Jr.
  Heavyweight on one line. Approved after play-test: Points/Survival team positions 先鋒..大将 = 1st..5th; team heading A組 = "A"
  (the field holds 4 bytes); league tag suffix 組 left blank (2-letter field); 初代 = "No. 1" like the other reigns; team names use "&".
- Owner (2026-11-07): the hidden wrestlers stay locked in the main patch; a separate "(English) (All Unlocked)" patch
  (`unlock-wrestlers`, docs/PATCHES.md) makes them selectable from the start, with the two music restores
  (`sapporo-music`, `edit-theme8`). Making the preset-only moves pickable in Edit: not done (owner, 2026-11-07).
