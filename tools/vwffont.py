#!/usr/bin/env python3
"""Bitmap fonts for a variable-width text renderer, as text files you can edit by hand.

  vwffont.py make FONT.ttf OUT.txt [--size 11] [--height 16] [--baseline 12] [--max-width 8]
                                   [--chars TEXT] [--preview PNG]
  vwffont.py show FONT.txt 'some text' PNG        draw a line 3x, to judge the font

`make` needs Pillow and is an editing step: commit OUT.txt and touch it up by hand. The build only
needs load() and wrap(), which use the standard library:
    glyphs = vwffont.load(path)                  # {codepoint: (advance in pixels, [row, ...])}
    vwffont.wrap(text, glyphs, 176)              # word-wrapped lines

Format: a `char 0041 width 7` line (code point, advance in pixels), then one row per line, `#` ink
and `.` blank, up to --max-width columns; `#` lines before the first char are comments. Rows load as
integers with the leftmost pixel in the top bit of a --max-width wide number (8: one byte).

Small sizes of an outline font need a look: try --size 10-12 with --preview, and fix letters in the
text file (Fight da Pon used DejaVu Sans 11). Columns over --max-width are squeezed out, repeated
columns first. The ellipsis is drawn as dots, because a font's own is usually too wide.
"""
import argparse
import re
import sys
from pathlib import Path

ELLIPSIS = '…'
DEFAULT_CHARS = ''.join(chr(c) for c in range(0x20, 0x7f)) + ELLIPSIS


def glyph(font, ch, height, baseline, max_width):
    """(advance, rows) of one character, drawn without smoothing."""
    from PIL import Image, ImageDraw
    if ch == ELLIPSIS:
        return 8, [''.join('#' if y == baseline - 1 and x % 2 == 0 else '.' for x in range(7)) for y in range(height)]
    size = max_width * 2
    im = Image.new('1', (size, height), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((1, baseline), ch, font=font, fill=1, anchor='ls')
    px = im.load()
    xs = [x for x in range(size) for y in range(height) if px[x, y]]
    first, last = (min(xs), max(xs)) if xs else (1, 3)     # a blank glyph is a space
    cols = [[px[x, y] for y in range(height)] for x in range(first, last + 1)]
    while len(cols) > max_width:
        for k in range(1, len(cols)):
            if cols[k] == cols[k - 1]:
                del cols[k]
                break
        else:
            del cols[-1]
    return len(cols) + 1, [''.join('#' if c[y] else '.' for c in cols) for y in range(height)]


def make(font, chars=DEFAULT_CHARS, height=16, baseline=12, max_width=8):
    """The font file's text, from a Pillow font."""
    out = [f'# {height} rows, up to {max_width} columns; "width N" is the advance in pixels. Edit by hand.']
    for ch in chars:
        advance, rows = glyph(font, ch, height, baseline, max_width)
        out += [f'char {ord(ch):04x} width {advance}', *rows]
    return '\n'.join(out) + '\n'


def load(path, columns=8):
    """{codepoint: (advance, [rows as integers])}"""
    glyphs, code = {}, None
    for ln in Path(path).read_text(encoding='utf-8').splitlines():
        m = re.fullmatch(r'char ([0-9a-fA-F]+) width (\d+)', ln)
        if m:
            code = int(m[1], 16)
            glyphs[code] = (int(m[2]), [])
        elif code is not None and ln:
            if not set(ln) <= {'#', '.'} or len(ln) > columns:
                raise SystemExit(f'{path}: bad row for {chr(code)!r}: {ln!r} (# and ., up to {columns} columns)')
            glyphs[code][1].append(int(ln.ljust(columns, '.').replace('#', '1').replace('.', '0'), 2))
    return glyphs


def text_width(text, glyphs):
    """Pixel width of `text`. Replace control codes first (a name code with its longest name)."""
    missing = sorted({c for c in text if ord(c) not in glyphs})
    if missing:
        raise SystemExit(f'no glyph for {missing}: add them to the font')
    return sum(glyphs[ord(c)][0] for c in text)


def wrap(text, glyphs, width, measure=None):
    """`text` split at spaces into lines of at most `width` pixels; a longer word stays on its own
    line. measure(text): the game's own width, when control codes take part."""
    measure = measure or (lambda s: text_width(s, glyphs))
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}' if line else word
        if measure(trial) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


def preview(glyphs, text, path, columns=8, scale=3):
    from PIL import Image
    w = text_width(text, glyphs)
    h = max(len(g[1]) for g in glyphs.values())
    im = Image.new('L', (w + 2, h), 0)
    x = 1
    for c in text:
        advance, rows = glyphs[ord(c)]
        for y, row in enumerate(rows):
            for b in range(columns):
                if row >> (columns - 1 - b) & 1:
                    im.putpixel((min(x + b, w + 1), y), 255)
        x += advance
    im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split('\n', 2)[2])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('make')
    p.add_argument('ttf')
    p.add_argument('out', type=Path)
    p.add_argument('--size', type=int, default=11)
    p.add_argument('--height', type=int, default=16)
    p.add_argument('--baseline', type=int, default=12)
    p.add_argument('--max-width', type=int, default=8)
    p.add_argument('--chars', default=DEFAULT_CHARS)
    p.add_argument('--preview', metavar='PNG')
    p = sub.add_parser('show')
    p.add_argument('font')
    p.add_argument('text')
    p.add_argument('png')
    p.add_argument('--max-width', type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == 'show':
        preview(load(a.font, a.max_width), a.text, a.png, a.max_width)
        return
    try:
        from PIL import ImageFont
    except ImportError:
        sys.exit('needs Pillow: run this with .venv/bin/python')
    font = ImageFont.truetype(a.ttf, a.size)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(make(font, a.chars, a.height, a.baseline, a.max_width), encoding='utf-8', newline='\n')
    print(f'{a.out}: {len(a.chars)} characters')
    if a.preview:
        preview(load(a.out, a.max_width), 'The quick brown fox jumps... (1P) 123', a.preview, a.max_width)
        print(a.preview)


if __name__ == '__main__':
    main()
