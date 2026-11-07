# Translation

## Where the text is

| File | Holds | Checked by |
|---|---|---|
| `translation/script/*.txt` | *(story/dialogue)* | `tools/lint.py` |
| `translation/text/*.txt`, `*.csv` | *(menus, names, ...)* | `tools/lint.py` |
| `translation/graphics.csv` | images with text | `tools/check.py` |

## File formats

Message blocks: `@ id`, source lines (`JP `), translation lines (`EN `); no `EN` lines = original
kept. A file's header says what it holds and its limits (`# limit lines=3 chars=28` is checked by
lint). Tables: original columns beside English ones (`japanese`/`english`, or `X`/`en_X`). See
`tools/blocks.py` and `tools/textdb.py`.

Control codes: *(list them here as they're found, e.g. `{name}` = player name)*.

## Style guide

- Name order, romanization: *(decide)*
- Quotes, ellipses, speaker labels, continuation-line indent: *(decide)*
- Voice and register per character type: *(decide)*
- Line and box limits: *(pixels / letters per screen)*

## Glossary

`translation/glossary.csv` (`japanese, english, notes`): lint warns when a source line contains a
term and the English doesn't use its translation (several accepted forms: `A | B`). Prefer
established community names (existing English guides) over new coinages.

## Decisions

| Decision | Who / why |
|---|---|
| | |

## What stays untranslated

*(logos, stylized art, ... and why)*

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
