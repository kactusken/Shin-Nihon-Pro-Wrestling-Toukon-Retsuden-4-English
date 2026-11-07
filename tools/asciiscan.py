#!/usr/bin/env python3
"""Find names the game stores as plain ASCII - and spells differently from the glossary:
python3 tools/asciiscan.py IMAGE [IMAGE...] [--min N] [--name WORD ...] [--all]

Games often keep a second copy of a name in ASCII (a HUD table, a debug screen, a save-file name) that the
text extractor never sees. Shin Nippon Chou Senshi had LYGER and CHOSYU in the match HUD while the
translation said Liger and Choshu; the owner found them by playing. Run this on the original after the
glossary exists (to find the tables to patch) and on every build (nothing should be left).

For every run of printable ASCII (letters, digits, space and . ' - & ! ?; at least --min characters, default 4,
and at least 3 letters) it looks for a name from translation/**/*.csv files named like glossary, names,
roster, characters... (their `english` column, each word of 5+ letters; plus --name WORD) that it nearly matches:
  SPELLING   one or two letters off ("LYGER" for "Liger"): fix it in build.py's code patches
  ok         the same word (any case): fine, listed so you know the table exists
--all also lists every run to build/work/asciiscan.txt (a ROM has hundreds; read the part you need).
On a build, text the patch draws with its own tile font can look like near-matches ("RIENTAL"): the useful
run is the original's, and a build should no longer hold the original's SPELLING offsets.
A name written by letter tiles in a font (not ASCII) is not found here: look at the screens (sweep, pairs).
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

RUN = re.compile(rb"[A-Za-z0-9 .'\-&!?]{4,}")


def distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


NAME_FILES = re.compile(r'gloss|name|roster|char|people|wrestler|player|team|fighter', re.I)


def glossary_words(extra):
    """English words of 5+ letters from translation/**/*.csv named like a glossary or name list
    (an `english` column), plus --name words."""
    words = set(extra)
    root = Path(paths.PROJECT) / 'translation'
    for f in sorted(root.glob('**/*.csv')) if root.is_dir() else []:
        if not NAME_FILES.search(f.name):
            continue
        with open(f, encoding='utf-8', newline='') as fh:
            lines = [l for l in fh if not l.startswith('#')]
        for row in csv.DictReader(lines):
            for form in (row.get('english') or '').split('|'):
                words.update(re.findall(r"[A-Za-z][A-Za-z'\-]*", form))
    return {w for w in words if len(w) >= 5}


def scan(data, words, minlen=4):
    """[(offset, run, kind, word)] for the near and exact matches; kind is 'SPELLING' or 'ok'."""
    found = []
    low = {w.lower(): w for w in words}
    for m in RUN.finditer(data):
        run = m.group().decode('ascii')
        if len(run) < minlen or sum(c.isalpha() for c in run) < 3:
            continue
        for tok in re.findall(r"[A-Za-z][A-Za-z'\-]*", run):
            t = tok.lower()
            if len(t) < 5:
                continue
            if t in low:
                found.append((m.start(), run.strip(), 'ok', low[t]))
                continue
            best = min(low, key=lambda w: distance(t, w))
            limit = 1 if len(best) < 8 else 2
            if abs(len(t) - len(best)) <= limit and distance(t, best) <= limit:
                found.append((m.start(), run.strip(), 'SPELLING', low[best]))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('images', nargs='+')
    ap.add_argument('--min', type=int, default=4)
    ap.add_argument('--name', action='append', default=[])
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    words = glossary_words(args.name)
    if not words:
        sys.exit('asciiscan: no glossary names (no glossary- or names-like CSV in translation/ with english words of 5+ letters; use --name)')
    bad = 0
    for img in args.images:
        data = Path(img).read_bytes()
        hits = scan(data, words, args.min)
        print(f'{img}: {len(hits)} name-like ASCII run(s)')
        for off, run, kind, word in hits:
            print(f'  {kind:8} 0x{off:06X}  "{run}"  ~ {word}')
            bad += kind == 'SPELLING'
        if args.all:
            out = Path(paths.PROJECT) / 'build' / 'work' / 'asciiscan.txt'
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'w', encoding='utf-8') as fh:
                for m in RUN.finditer(data):
                    if sum(c.isalpha() for c in m.group().decode()) >= 3:
                        fh.write(f'0x{m.start():06X}  {m.group().decode()}\n')
            print(f'  every run: {out}')
    print(f'{bad} spelling(s) to check' if bad else 'no spelling differs from the glossary')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
