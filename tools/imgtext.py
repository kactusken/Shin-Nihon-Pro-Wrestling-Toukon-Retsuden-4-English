#!/usr/bin/env python3
"""Render English into the game's label textures (research/edit tool; needs Pillow: .venv/bin/python).

  imgtext.py render [ID...]     render every graphics.csv row with kind label and English (or the given ids)
  imgtext.py preview ID TEXT    render one label to build/work/img/ID.png (look at it, change nothing)

Menu labels (verified in game 2026-11-06): 128x128 textures drawn on a quad about 4 times wider than
tall, so the original text is tall and narrow in the texture. The English is drawn on a canvas of that
shape (CANVAS_ASPECT) in a bold italic condensed face with a dark outline, then squeezed into the
texture, which gives the original look again. Output: translation/images-rendered/<id>.png (RGBA, the
texture's size). `tools/gfx.py` imports the final set; VQ textures are frozen with `gfx.py freeze`.
"""
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

FONT = Path(__file__).resolve().parent / 'fonts' / 'BarlowCondensed-BlackItalic.ttf'
CANVAS_ASPECT = 4.0          # displayed width : height of a label quad
FILL = (255, 255, 255, 255)
OUTLINE = (24, 24, 32, 255)


def render_label(text, size=(128, 128), aspect=CANVAS_ASPECT, color=FILL, outline=OUTLINE, stroke=6):
    w, h = size
    cw = 1024
    ch = int(cw / aspect)
    pad = 10
    lines = text.split(' / ')
    best = None
    for fs in range(int(ch / len(lines)) + 40, 8, -2):
        font = ImageFont.truetype(str(FONT), fs)
        boxes = [font.getbbox(l, stroke_width=stroke) for l in lines]
        tw = max(b[2] - b[0] for b in boxes)
        th = sum(b[3] - b[1] for b in boxes) + 4 * (len(lines) - 1)
        if tw <= cw - 2 * pad and th <= ch - 2 * pad:
            best = (font, boxes, th)
            break
    if best is None:
        raise SystemExit(f'label {text!r} does not fit')
    font, boxes, th = best
    im = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = (ch - th) // 2
    for l, b in zip(lines, boxes):
        x = (cw - (b[2] - b[0])) // 2 - b[0]
        d.text((x, y - b[1]), l, font=font, fill=color, stroke_width=stroke, stroke_fill=outline)
        y += (b[3] - b[1]) + 4
    return im.resize((w, h), Image.LANCZOS)


GOLD = (255, 170, 20, 255)
BLACK = (10, 10, 10, 255)


def _lum(px):
    return (px[0] * 299 + px[1] * 587 + px[2] * 114) // 1000


def clear_text(img, box, fg):
    """Paint the original text of `box` (an RGBA texture region) out: its pixels take the plate colour
    (the median of the opaque pixels that are not text), or become transparent on an empty plate."""
    x0, y0, x1, y1 = box
    px = img.load()
    opaque = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if px[x, y][3] > 40]
    if not opaque:
        return
    if fg == 'black':
        is_text = lambda p: _lum(p) < 70
    elif fg in ('gold', 'yellow'):
        is_text = lambda p: (p[0] > 150 and p[1] > 150 and p[2] < 120) if fg == 'yellow' else True            # gold headings sit on transparency: everything goes
    else:
        is_text = lambda p: _lum(p) > 200
    rest = [px[x, y] for x, y in opaque if not is_text(px[x, y])]
    if fg == 'gold' or len(rest) < len(opaque) // 8:
        for x, y in opaque:
            px[x, y] = (0, 0, 0, 0)
        return
    rs = sorted(c[0] for c in rest)
    gs = sorted(c[1] for c in rest)
    bs = sorted(c[2] for c in rest)
    med = (rs[len(rs) // 2], gs[len(gs) // 2], bs[len(bs) // 2], 255)
    mask = {(x, y) for x, y in opaque if is_text(px[x, y])}
    grown = set()
    for x, y in mask:
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if (x + dx, y + dy) in set(opaque):
                    grown.add((x + dx, y + dy))
    for x, y in grown:
        px[x, y] = med


def text_bbox(img, fg):
    """Bounding box (x0, y0, x1, y1) of the text pixels of a plate texture, or None."""
    px = img.load()
    if fg == 'yellow':
        test = lambda p: p[3] > 40 and p[0] > 150 and p[1] > 150 and p[2] < 120
    elif fg == 'black':
        test = lambda p: p[3] > 40 and _lum(p) < 70
    else:
        test = lambda p: p[3] > 40 and _lum(p) > 200
    pts = [(x, y) for y in range(img.height) for x in range(img.width) if test(px[x, y])]
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs) - 2, min(ys) - 2, max(xs) + 3, max(ys) + 3


def text_color(notes):
    n = (notes or '').lower()
    if 'black text' in n:
        return 'black'
    if 'yellow' in n and 'black outline' in n:
        return 'yellow'
    if 'orange' in n or 'gold' in n:
        return 'gold'
    return 'white'


def render_row(img, box, text, fg, aspect):
    """Redraw one row of a texture: clear the old text, draw `text` squeezed from a canvas of `aspect`."""
    x0, y0, x1, y1 = box
    clear_text(img, box, fg)
    color = {'black': BLACK, 'gold': GOLD, 'yellow': (255, 235, 40, 255)}.get(fg, FILL)
    t = render_label(text, (x1 - x0, y1 - y0), aspect, color,
                     outline={'black': (230, 230, 230, 0), 'gold': (20, 10, 0, 255), 'yellow': (0, 0, 0, 255)}.get(fg, OUTLINE),
                     stroke={'black': 0}.get(fg, 6))
    img.alpha_composite(t, (x0, y0))


def gradient_fill(w, h, stops):
    """An RGBA image w x h with a vertical gradient through `stops` [(pos 0..1, (r, g, b))]."""
    im = Image.new('RGBA', (w, h))
    px = im.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                f = (t - p0) / max(1e-6, p1 - p0)
                c = tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(3)) + (255,)
                break
        else:
            c = stops[-1][1] + (255,)
        for x in range(w):
            px[x, y] = c
    return im


TELOP_STYLES = {
    'big': dict(stops=[(0, (255, 236, 200)), (0.45, (255, 160, 50)), (1, (190, 45, 10))], outline=(90, 15, 0, 255), stroke=7),
    'small': dict(stops=[(0, (255, 255, 255)), (1, (225, 225, 255))], outline=(10, 10, 210, 255), stroke=5),
}


def render_box(img, box, text, style):
    """Clear `box` of the atlas and draw `text` in a telop style (gradient fill, coloured outline) fitted to it."""
    x0, y0, w, h = box
    px = img.load()
    for y in range(y0, min(img.height, y0 + h + 2)):
        for x in range(x0, min(img.width, x0 + w + 2)):
            px[x, y] = (0, 0, 0, 0)
    st = TELOP_STYLES[style]
    cw, ch = w * 8, h * 8
    lines = text.split(' / ')
    for fs in range(ch, 8, -2):
        font = ImageFont.truetype(str(FONT), fs)
        bb = [font.getbbox(l, stroke_width=st['stroke'] * 2) for l in lines]
        tw = max(b[2] - b[0] for b in bb)
        th = sum(b[3] - b[1] for b in bb) + 8 * (len(lines) - 1)
        if tw <= cw - 8 and th <= ch - 8:
            break
    mask = Image.new('L', (cw, ch), 0)
    d = ImageDraw.Draw(mask)
    outl = Image.new('L', (cw, ch), 0)
    do = ImageDraw.Draw(outl)
    y = (ch - th) // 2
    for l, b in zip(lines, bb):
        x = (cw - (b[2] - b[0])) // 2 - b[0]
        d.text((x, y - b[1]), l, font=font, fill=255)
        do.text((x, y - b[1]), l, font=font, fill=255, stroke_width=st['stroke'] * 2)
        y += (b[3] - b[1]) + 8
    fill = gradient_fill(cw, ch, st['stroke'] and st['stops'])
    layer = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    layer.paste(Image.new('RGBA', (cw, ch), st['outline']), (0, 0), outl)
    layer.paste(fill, (0, 0), mask)
    img.alpha_composite(layer.resize((w, h), Image.LANCZOS), (x0, y0))


def rows():
    p = paths.GRAPHICS_CSV
    if not p.exists():
        return []
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['preview'] and len(argv) == 3:
        out = paths.BUILD / 'work' / 'img'
        out.mkdir(parents=True, exist_ok=True)
        render_label(argv[2]).save(out / f'{argv[1]}.png')
        print(out / f'{argv[1]}.png')
    elif argv[:1] == ['render']:
        import catalog
        only = set(argv[1:])
        n = 0
        version, done = catalog.renderer_version(), catalog.load_renders()
        for r in rows():
            if not (r.get('english') or '').strip() or r.get('status') == 'keep':
                continue
            if only and r['image'] not in only:
                continue
            orig = Image.open(paths.ORIGINAL_IMAGES / f'{r["image"]}.png').convert('RGBA')
            w, h = orig.size
            fg = text_color(r.get('notes'))
            parts = [p.strip() for p in r['english'].split(' | ')]
            img = orig.copy()
            if r.get('boxes'):
                bxs = [tuple(int(v) for v in b.split(',')) for b in r['boxes'].split(';')]
                if len(bxs) != len(parts):
                    raise SystemExit(f'{r["image"]}: {len(bxs)} boxes, {len(parts)} English items')
                styles = r['font'].split(',')
                for k, (b, t) in enumerate(zip(bxs, parts)):
                    st = styles[k] if k < len(styles) else styles[-1]
                    if st == 'row':
                        render_row(img, (b[0], b[1], b[0] + b[2], b[1] + b[3]), t, 'white', b[2] / b[3])
                    else:
                        render_box(img, b, t, st)
            elif r['category'] == 'multi' or len(parts) > 1:
                rh = h // len(parts)
                for k, t in enumerate(parts):
                    render_row(img, (0, k * rh, w, (k + 1) * rh), t, fg, w / rh if fg != 'white' or w > 128 else CANVAS_ASPECT)
            else:
                if fg == 'white' and w <= 128 and not any(k in (r.get('notes') or '') for k in ('beveled', 'plate', 'tile', 'bar', 'button')):
                    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                    img = render_label(parts[0], (w, h))
                else:
                    bb = text_bbox(img, fg) if any(k in (r.get('notes') or '') for k in ('plate', 'tile', 'bar')) else None
                    if bb:
                        bb = (max(0, bb[0]), max(0, bb[1]), min(w, bb[2]), min(h, bb[3]))
                        render_row(img, bb, parts[0], fg, (bb[2] - bb[0]) / (bb[3] - bb[1]))
                    else:
                        render_row(img, (0, 0, w, h), parts[0], fg, w / h if (w != h or 'beveled' in (r.get('notes') or '')) else CANVAS_ASPECT)
            out = paths.RENDERED / f'{r["image"]}.png'
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out)
            done[r['image']] = {'fp': catalog.fingerprint(r, version)}
            n += 1
        catalog.save_renders(done)
        print(n, 'images rendered')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
