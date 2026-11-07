#!/usr/bin/env python3
"""Game images: export the textures and import the English ones (Toukon Retsuden 4, Dreamcast).

  gfx.py export [--out DIR] [--only PREFIX]   every texture of the UI archives as DIR/<id>.png (RGBA)
  gfx.py freeze                               encode the final English images of VQ textures (needs numpy:
                                              run with .venv/bin/python) into translation/images-frozen/
  gfx.py list                                 the texture ids with size and format

Textures (verified 2026-11-06): a .PAC section of the *counted* form (tools/pac.py) whose entries are
PVR textures with a 16-byte header instead of the PVRT chunk: u32 id, u8 pixel format, u8 data
format, u16 0, u32 width, u32 height (formats as in tools/pvr.py); the data follows. Ids are
`<folder>_<file>.<section>.<entry>` (e.g. MENU_MENU.0.012).

export_all(extracted, out) -> count          the interface of the kit's image tools
import_images(images, files) -> count        {id: PNG} into the archives. Twiddled textures are encoded
    here (standard library); VQ textures need the numpy k-means, so `freeze` makes their data at edit
    time (translation/images-frozen/<id>.bin + <id>.json with the PNG's SHA-1) and the build copies it.
"""
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pac  # noqa: E402
import paths  # noqa: E402
import pngio  # noqa: E402
import pvr  # noqa: E402

UI_DIRS = ('MENU', 'SPRITE', 'ENTDATA')       # folders whose archives are scanned for textures
FROZEN = 'images-frozen'
PIXELS = (0, 1, 2)                              # 16-bit formats (palette textures are not used here)
DIMS = (8, 16, 32, 64, 128, 256, 512, 1024)
LAYOUTS = (1, 2, 3, 4, 9, 0xb, 0xd, 0x10, 0x11)


def tex_header(d, o, size):
    """(id, pixel, layout, w, h) if the entry at o is a texture, else None."""
    if size < 16 or o + 16 > len(d):
        return None
    gid, pf, df, z, w, h = struct.unpack_from('<IBBHII', d, o)
    if pf in PIXELS and df in LAYOUTS and z == 0 and w in DIMS and h in DIMS:
        return gid, pf, df, w, h
    return None


def walk(extracted, dirs=UI_DIRS):
    """[(image id, disc file path, offset, size)] of every texture in the UI archives."""
    out = []
    for folder in dirs:
        for p in sorted((Path(extracted) / folder).glob('*.PAC')):
            d = p.read_bytes()
            for k, (s, e) in enumerate(pac.sections(d)):
                form, ents = pac.section_table(d, s, e)
                for i, (o, sz) in enumerate(ents):
                    if o and tex_header(d, o, sz):
                        out.append((f'{folder}_{p.stem}.{k}.{i:03d}', f'/{folder}/{p.name}', o, sz))
    return out


def texture(entry):
    """pvr.Texture of an entry (16-byte header + data): a PVRT chunk is put in front."""
    gid, pf, df, w, h = tex_header(entry, 0, len(entry))
    body = bytes(entry[16:])
    chunk = b'PVRT' + struct.pack('<I', len(body) + 8) + bytes([pf, df]) + b'\0\0' + struct.pack('<HH', w, h) + body
    return pvr.Texture(chunk, 0)


def write_rgba_png(path, w, h, pixels):
    raw = b''.join(b'\0' + bytes(c for px in pixels[y * w:(y + 1) * w] for c in px) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def png_rgba(path):
    p = pngio.read(path)
    if p.palette:
        rows = [[tuple(p.palette[v]) + ((p.alpha[v] if p.alpha and v < len(p.alpha) else 255),) for v in r]
                for r in p.rows]
    else:
        rows = [[px if len(px) == 4 else tuple(px) + (255,) for px in r] for r in p.rows]
    return p.width, p.height, rows


def export_all(extracted, out, only=''):
    out = Path(out)
    n = 0
    cache = {}
    for iid, disc_path, o, sz in walk(extracted):
        if only and not iid.startswith(only):
            continue
        d = cache.setdefault(disc_path, (Path(extracted) / disc_path.lstrip('/')).read_bytes())
        t = texture(d[o:o + sz])
        dst = out / f'{iid}.png'
        dst.parent.mkdir(parents=True, exist_ok=True)
        write_rgba_png(dst, t.w, t.h, t.decode())
        dst.with_suffix('.json').write_text(json.dumps({'file': disc_path, 'offset': o, 'size': sz,
                                                        'format': t.describe()}))
        n += 1
    return n


def _sha1(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def encode_entry(entry, rows, iid):
    """The texture entry with its pixels replaced by `rows` (RGBA, the texture's size), twiddled formats only."""
    t = texture(entry)
    if t.layout not in (1, 2, 9, 0xd):
        raise SystemExit(f'{iid}: layout {t.layout:#x} is VQ or other: run `.venv/bin/python tools/gfx.py freeze`')
    if len(rows) != t.h or len(rows[0]) != t.w:
        raise SystemExit(f'{iid}: image is {len(rows[0])}x{len(rows)}, the texture {t.w}x{t.h}')
    if t.layout == 9:                     # rectangle: plain rows of 16-bit pixels
        body = b''.join(struct.pack('<H', pvr.to_px(px, t.pixel)) for row in rows for px in row)
        if len(body) != len(entry) - 16:
            raise SystemExit(f'{iid}: rectangle texture holds {len(entry) - 16} bytes, the picture {len(body)}')
        return bytes(entry[:16]) + body
    chunk = t.encode(rows)
    return bytes(entry[:16]) + chunk[16:]


def import_images(images, files):
    """{id: PNG} -> the archives in `files`. Returns the count."""
    if not images:
        return 0
    frozen_dir = paths.TRANSLATION / FROZEN
    locs = {iid: (fp, o, sz) for iid, fp, o, sz in walk(paths.EXTRACTED)}
    n = 0
    for iid, png in sorted(images.items()):
        if iid not in locs:
            raise SystemExit(f'graphics.csv image {iid!r} is not a texture of the UI archives (tools/gfx.py list)')
        fp, o, sz = locs[iid]
        data = files.get(fp)
        entry = bytes(data[o:o + sz])
        t = texture(entry)
        fz = frozen_dir / (iid.replace('/', '__') + '.bin')
        if t.layout in (3, 4, 0x10, 0x11):
            meta = fz.with_suffix('.json')
            if not fz.exists() or not meta.exists():
                raise SystemExit(f'{iid}: VQ texture without frozen data - run .venv/bin/python tools/gfx.py freeze')
            if json.loads(meta.read_text())['sha1'] != _sha1(png):
                raise SystemExit(f'{iid}: the picture changed since it was frozen - run .venv/bin/python tools/gfx.py freeze')
            new = fz.read_bytes()
            if len(new) != sz:
                raise SystemExit(f'{iid}: frozen data is {len(new)} bytes, the entry {sz}')
        else:
            w, h, rows = png_rgba(png)
            new = encode_entry(entry, rows, iid)
        data[o:o + sz] = new
        files.put(fp, bytes(data))
        n += 1
    return n


def freeze():
    """Encode the VQ textures of the final English images (needs numpy)."""
    import catalog
    final = catalog.final_images()
    locs = {iid: (fp, o, sz) for iid, fp, o, sz in walk(paths.EXTRACTED)}
    frozen_dir = paths.TRANSLATION / FROZEN
    frozen_dir.mkdir(parents=True, exist_ok=True)
    cache, n = {}, 0
    for iid, (tag, png) in sorted(final.items()):
        fp, o, sz = locs[iid]
        d = cache.setdefault(fp, (paths.EXTRACTED / fp.lstrip('/')).read_bytes())
        entry = d[o:o + sz]
        t = texture(entry)
        if t.layout not in (3, 4, 0x10, 0x11):
            continue
        fz = frozen_dir / (iid.replace('/', '__') + '.bin')
        meta = fz.with_suffix('.json')
        if fz.exists() and meta.exists() and json.loads(meta.read_text())['sha1'] == _sha1(png):
            continue
        w, h, rows = png_rgba(png)
        chunk = t.encode_vq(rows)
        new = bytes(entry[:16]) + chunk[16:]
        if len(new) != sz:
            raise SystemExit(f'{iid}: encoded {len(new)} bytes, the entry {sz}')
        fz.write_bytes(new)
        meta.write_text(json.dumps({'sha1': _sha1(png)}))
        n += 1
        print(f'froze {iid}')
    print(f'{n} VQ textures frozen')


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['export']:
        out = paths.ORIGINAL_IMAGES
        only = ''
        if '--out' in argv:
            out = Path(argv[argv.index('--out') + 1])
        if '--only' in argv:
            only = argv[argv.index('--only') + 1]
        print(export_all(paths.EXTRACTED, out, only), 'textures ->', out)
    elif argv[:1] == ['list']:
        for iid, fp, o, sz in walk(paths.EXTRACTED):
            t = texture((paths.EXTRACTED / fp.lstrip('/')).read_bytes()[o:o + sz])
            print(iid, t.describe())
    elif argv[:1] == ['freeze']:
        freeze()
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
