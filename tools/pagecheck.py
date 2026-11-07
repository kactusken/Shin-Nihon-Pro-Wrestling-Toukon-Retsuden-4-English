#!/usr/bin/env python3
"""Read a guide page the way a player does: python3 tools/pagecheck.py [--allow-markers] [--warnings] [page...]

Pages: docs/**/index.html (default). Errors (check.py fails on these):
  placeholder   [bracketed template text] left from the starter, TODO / FIXME / TBD / "coming soon"
  hedging       "not tested", "not covered yet", "unverified", "to be confirmed" and the like - the page
                states what is true or leaves the point out (owner.json "guide": fact_markers false)
  marker        "verified in game", "from the code", "from the data" labels (skip with --allow-markers,
                or {"fact_markers": true} in private/guide.json, for an owner who wants them)
  author note   text written for the author, not the reader ("the lead", "belongs outside", "the original
                does the same", notes about how the patch or the original's code works)
  empty         () [] or quotes with nothing inside - a label was stripped and its brackets stayed
  alt           an <img> without alt, or alt text with a double space (a chip stripped from the caption)
  doubled       a heading directly followed by the same heading text (a generated table's own title)
Warnings (--warnings; never fail): code addresses ($03:A953, 0x3eaa2) in the text - they belong in
docs/TECHNICAL.md; a space before , . ; : ! ?.

A line that must stay as written (a quoted game message): put `data-pagecheck="skip"` on its element.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

RULES = [
    ('placeholder', r'(?<![\w\]])\[[A-Za-z][^\]\n,]{2,}\]|\b(TODO|FIXME|TBD|XXX)\b|coming soon|lorem ipsum'),
    ('hedging', r'not (yet )?(been )?(tested|verified|confirmed|checked|covered)|untested|unverified|'
                r'to be confirmed|not (fully )?(known|understood)|haven.t (been )?(tested|checked)|'
                r'(is|are) (still )?unknown|needs? (testing|checking|verifying)|not covered yet|'
                r'(i|we) (am|are)n.t sure|may or may not'),
    ('marker', r'verified in game|verified in-game|from the code|from the data|from a guide|'
               r'seen headless|(?<![\w-])\(unverified\)'),
    ('author note', r'\b(the lead|belongs outside|note to (self|author)|'
                    r'the patch (code|hook)|our hook|the original does the same|private/work|'
                    r'docs/TECHNICAL|tools/\w+\.py)\b|\bclipped at the bottom\b|\bcut off at the bottom\b'),
    ('empty', r'\(\s*\)|\[\s*\]|“\s*”|"\s*"'),
]
WARN = [
    ('address', r'\$[0-9A-Fa-f]{2}:[0-9A-Fa-f]{4}\b|\b0x[0-9A-Fa-f]{5,}\b'),
    ('about the project, not the game (credits only?)', r'the translation project|the patch.s (code|build tools)'),
    ('space before punctuation', r'\w [,.;:!?](?=\s|$)'),
]
SKIP_TAGS = {'script', 'style', 'noscript', 'svg', 'template'}
HEADS = {'h1', 'h2', 'h3', 'h4'}
BLOCKS = HEADS | {'p', 'li', 'td', 'th', 'tr', 'div', 'br', 'section', 'figure', 'figcaption', 'details',
                  'summary', 'ul', 'ol', 'table', 'dt', 'dd', 'button', 'label', 'header', 'footer', 'nav', 'main'}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.alts, self.heads = [], [], []   # text: (line, str)
        self.skip = 0           # inside a script / style / svg
        self.pc_skip = []       # open tags below a data-pagecheck="skip" element
        self.head = None
        self.noalt = []

    def _break(self, tag):
        if tag in BLOCKS and not self.skip and not self.pc_skip:
            self.text.append((self.getpos()[0], ' '))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._break(tag)
        if self.pc_skip:
            self.pc_skip.append(tag)
        elif a.get('data-pagecheck') == 'skip':
            self.pc_skip = [tag]
        if tag in SKIP_TAGS:
            self.skip += 1
        if tag == 'img':
            if 'alt' not in a:
                self.noalt.append(self.getpos()[0])
            elif not self.pc_skip:
                self.alts.append((self.getpos()[0], a['alt']))
        if tag in HEADS:
            self.head = [tag, self.getpos()[0], '']

    def handle_endtag(self, tag):
        self._break(tag)
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        if self.pc_skip:
            if tag == self.pc_skip[-1]:
                self.pc_skip.pop()
        if self.head and tag == self.head[0]:
            self.heads.append((self.head[1], re.sub(r'\s+', ' ', self.head[2]).strip().lower()))
            self.head = None

    def handle_data(self, data):
        if self.skip or self.pc_skip or not data:
            return
        self.text.append((self.getpos()[0], data))
        if self.head:
            self.head[2] += data


def pages(args):
    if args:
        return [Path(a) for a in args]
    return sorted(Path(paths.DOCS).glob('**/index.html'))


def check(path, markers_ok):
    p = Page()
    p.feed(path.read_text(encoding='utf-8'))
    errors, warns = [], []
    # join the text so a phrase split by <b> or a line break is still found, but report the line it starts on
    joined, offsets = '', []
    for line, t in p.text:
        offsets.append((len(joined), line))
        joined += re.sub(r'\s+', ' ', t)

    def line_at(pos):
        ln = 0
        for off, line in offsets:
            if off > pos:
                break
            ln = line
        return ln

    for name, rx in RULES:
        if name == 'marker' and markers_ok:
            continue
        for m in re.finditer(rx, joined, re.I if name != 'placeholder' else 0):
            if name == 'placeholder' and m.group(0).isupper() and len(m.group(0)) < 12 and m.group(0).startswith('['):
                continue    # [SELECT], [A]: a button label, not a template slot
            ctx = joined[max(0, m.start() - 40):m.end() + 40].strip()
            errors.append((line_at(m.start()), name, f'"{m.group(0)}" ... {ctx}'))
    for name, rx in WARN:
        for m in re.finditer(rx, joined):
            warns.append((line_at(m.start()), name, joined[max(0, m.start() - 30):m.end() + 30].strip()))
    for line in p.noalt:
        errors.append((line, 'alt', '<img> without alt'))
    for line, alt in p.alts:
        if '  ' in alt or alt != alt.strip():
            errors.append((line, 'alt', f'double or edge space in alt="{alt[:60]}"'))
    for (l1, h1), (l2, h2) in zip(p.heads, p.heads[1:]):
        if h1 and h1 == h2:
            errors.append((l2, 'doubled', f'heading "{h2}" repeated directly'))
    return sorted(errors), sorted(warns)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('pages', nargs='*')
    ap.add_argument('--allow-markers', action='store_true')
    ap.add_argument('--warnings', action='store_true')
    args = ap.parse_args()
    markers_ok = args.allow_markers
    cfg = Path(paths.PROJECT) / 'private' / 'guide.json'
    if cfg.exists():
        try:
            markers_ok = markers_ok or bool(json.loads(cfg.read_text()).get('fact_markers'))
        except ValueError:
            pass
    files = pages(args.pages)
    bad = 0
    for f in files:
        errors, warns = check(f, markers_ok)
        for line, name, what in errors:
            print(f'  {f}:{line}: {name}: {what}')
        if args.warnings:
            for line, name, what in warns:
                print(f'  {f}:{line}: (warning) {name}: {what}')
        bad += len(errors)
    print(f'{len(files)} page(s), {bad} error(s)' + ('' if args.warnings else ' (--warnings for the rest)'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
