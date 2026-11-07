#!/usr/bin/env python3
"""Dreamcast PVR textures (GBIX/PVRT): decode to RGBA, encode back, find them in data.

  pvr.py scan <file>...             PVRT chunks in files (raw or SBL LZSS entries): offset, size, format
  pvr.py png <file> <offset> <out>  one texture to PNG (Pillow)

PVRT header (16 bytes): 'PVRT', u32 size of the rest, u8 pixel format (0 ARGB1555, 1 RGB565,
2 ARGB4444, 5 4-bit palette, 6 8-bit palette), u8 data format (1/2 square twiddled [mipmaps],
3/4 VQ [mipmaps], 5/6 4-bit palette twiddled, 7/8 8-bit palette twiddled, 9 rectangle,
0x0B stride, 0x0D rectangle twiddled, 0x10/0x11 small VQ), u16 0, u16 width, u16 height.
Mipmapped data stores the small levels first; the full-size image is the last one.
An optional 'GBIX' chunk (8 + its size bytes) comes before PVRT.

Encoding English back (the texture keeps its size, format and layout; returns the new data):
  Texture(data, off).encode(rows)       twiddled 16-bit (layouts 1, 2: the full-size level), standard
                                        library - a build step can call it
  Texture(data, off).encode_vq(rows)    VQ (layouts 3, 0x10): k-means over the 2x2 blocks, started from
                                        the original codebook, premultiplied alpha. Needs numpy, so it runs
                                        at edit time; freeze its output beside the picture (with the
                                        picture's SHA-1) and let the build copy it in (Fire Pro D:
                                        tools/dptex.py, the network mode's label atlases)
rows: [[(r, g, b, a)] * w] * h, e.g. from tools/pngio.py.
"""
import struct
import sys
from pathlib import Path

PIXEL = {0: 'ARGB1555', 1: 'RGB565', 2: 'ARGB4444', 5: 'PAL4', 6: 'PAL8'}


def twiddle_table(n):
    t = []
    for i in range(n):
        v, b, k = 0, 0, i
        while k:
            v |= (k & 1) << (2 * b)
            k >>= 1
            b += 1
        t.append(v)
    return t


_TW = twiddle_table(1024)


def tw(x, y):
    """Twiddled index of (x, y) in a square texture (x is the slow bit: y | x << 1)."""
    return (_TW[y] | (_TW[x] << 1))


def rgba(px, fmt):
    if fmt == 0:
        a = 255 if px & 0x8000 else 0
        return ((px >> 10) & 31) * 255 // 31, ((px >> 5) & 31) * 255 // 31, (px & 31) * 255 // 31, a
    if fmt == 1:
        return (px >> 11) * 255 // 31, ((px >> 5) & 63) * 255 // 63, (px & 31) * 255 // 31, 255
    if fmt == 2:
        return ((px >> 8) & 15) * 17, ((px >> 4) & 15) * 17, (px & 15) * 17, (px >> 12) * 17
    raise ValueError(f'pixel format {fmt}')


def to_px(c, fmt):
    r, g, b, a = c
    if fmt == 0:
        return (0x8000 if a >= 128 else 0) | (r * 31 // 255) << 10 | (g * 31 // 255) << 5 | (b * 31 // 255)
    if fmt == 1:
        return (r * 31 // 255) << 11 | (g * 63 // 255) << 5 | (b * 31 // 255)
    if fmt == 2:
        return (a * 15 // 255) << 12 | (r * 15 // 255) << 8 | (g * 15 // 255) << 4 | (b * 15 // 255)
    raise ValueError(f'pixel format {fmt}')


class Texture:
    def __init__(self, data, off):
        """The PVRT chunk at `off` of `data` (a GBIX chunk before it is skipped by find())."""
        assert data[off:off + 4] == b'PVRT', 'no PVRT here'
        self.off = off
        self.size = struct.unpack_from('<I', data, off + 4)[0]
        self.pixel, self.layout = data[off + 8], data[off + 9]
        self.w, self.h = struct.unpack_from('<HH', data, off + 12)
        self.body = off + 16
        self.data = data

    @property
    def mip(self):
        return self.layout in (2, 4, 6, 8, 0x11)

    def describe(self):
        return f'{self.w}x{self.h} {PIXEL.get(self.pixel, self.pixel)} layout {self.layout:#x}'

    def level_bytes(self):
        """Bytes of the full-size level's pixel data (VQ: the index bytes)."""
        L, w, h = self.layout, self.w, self.h
        if L in (3, 4, 0x10, 0x11):
            return (w // 2) * (h // 2)
        if L in (5, 6):
            return w * h // 2
        if L in (7, 8):
            return w * h
        return w * h * 2

    def data_start(self):
        """Offset of the full-size level: mipmaps store it last, so count back from the chunk's
        end (no mipmaps: right after the header, or the VQ codebook)."""
        if self.layout in (4, 0x11):          # VQ with mipmaps: codebook, the smaller levels (1x1 first), the full level
            return self.body + self.codebook() * 8 + self.mip_bytes_below()
        if self.mip:
            return self.off + 8 + self.size - self.level_bytes()
        return self.body + (self.codebook() * 8 if self.layout in (3, 0x10) else 0)

    def mip_dims(self):
        """Side lengths of the levels below the full size, smallest first (1, 2, 4, ... w/2)."""
        out, d = [], 1
        while d < self.w:
            out.append(d)
            d *= 2
        return out

    def mip_bytes_below(self):
        """Index bytes of the VQ levels below the full size (a 1x1 level takes one byte, like 2x2)."""
        return sum(max(1, d // 2) ** 2 for d in self.mip_dims())

    def codebook(self):
        """Codebook entries of a VQ texture (small VQ keeps fewer for small sizes)."""
        w = self.w
        if self.layout == 0x10:
            return 16 if w <= 16 else 32 if w == 32 else 128 if w == 64 else 256
        if self.layout == 0x11:
            return 16 if w <= 16 else 64 if w == 32 else 256
        return 256

    def decode(self, palette=None):
        """[(r,g,b,a)] row-major, w*h."""
        d, w, h, L, f = self.data, self.w, self.h, self.layout, self.pixel
        out = [(0, 0, 0, 0)] * (w * h)
        p = self.data_start()
        if L in (1, 2, 0x0D):
            n = min(w, h)
            for y in range(h):
                for x in range(w):
                    # rectangle twiddled: squares of n x n side by side
                    blk = (x // n) + (y // n)
                    i = blk * n * n + tw(x % n, y % n)
                    out[y * w + x] = rgba(struct.unpack_from('<H', d, p + 2 * i)[0], f)
        elif L in (9, 0x0B):
            for y in range(h):
                for x in range(w):
                    out[y * w + x] = rgba(struct.unpack_from('<H', d, p + 2 * (y * w + x))[0], f)
        elif L in (3, 4, 0x10, 0x11):
            book = self.body
            codes = [[rgba(struct.unpack_from('<H', d, book + 8 * k + 2 * j)[0], f) for j in range(4)]
                     for k in range(self.codebook())]
            for y in range(0, h, 2):
                for x in range(0, w, 2):
                    c = codes[d[p + tw(x // 2, y // 2)] % len(codes)]
                    # codebook entry order: (0,0) (0,1) (1,0) (1,1) - x slow
                    out[y * w + x], out[(y + 1) * w + x], out[y * w + x + 1], out[(y + 1) * w + x + 1] = c
        elif L in (5, 6, 7, 8):
            pal = palette or [(k * 17 % 256,) * 3 + (255,) for k in range(256)]
            for y in range(h):
                for x in range(w):
                    i = tw(x, y)
                    if L in (5, 6):
                        v = d[p + i // 2]
                        v = (v >> 4) if i & 1 else (v & 15)
                    else:
                        v = d[p + i]
                    out[y * w + x] = pal[v % len(pal)]
        else:
            raise ValueError(f'layout {L:#x} not handled')
        return out

    def to_image(self, palette=None):
        from PIL import Image
        im = Image.new('RGBA', (self.w, self.h))
        im.putdata(self.decode(palette))
        return im

    def _check_rows(self, rows, layouts):
        if self.layout not in layouts:
            raise ValueError(f'layout {self.layout:#x} can not be encoded here (only {", ".join(map(hex, layouts))})')
        if len(rows) != self.h or any(len(r) != self.w for r in rows):
            raise ValueError(f'image is {len(rows[0])}x{len(rows)}, the texture {self.w}x{self.h}')

    def encode(self, rows):
        """The data with the full-size level of a square twiddled 16-bit texture replaced by `rows`."""
        self._check_rows(rows, (1, 2))
        out = bytearray(self.data)
        p = self.data_start()
        for y in range(self.h):
            for x in range(self.w):
                struct.pack_into('<H', out, p + 2 * tw(x, y), to_px(rows[y][x], self.pixel))
        return bytes(out)

    def encode_vq(self, rows, iterations=12):
        """The data with a VQ texture (no mipmaps) re-encoded from `rows`: a new codebook of the
        same size (k-means from the original's) and new indices. Needs numpy."""
        import numpy as np
        self._check_rows(rows, (3, 4, 0x10, 0x11))
        n, w, h = self.codebook(), self.w, self.h
        a = np.array(rows, dtype=np.float64).reshape(h, w, 4)
        al = a[:, :, 3:4] / 255
        pm = np.concatenate([a[:, :, :3] * al, a[:, :, 3:4]], axis=2)
        # 2x2 blocks in codebook order (0,0) (0,1) (1,0) (1,1) - x slow
        vecs = np.stack([pm[0::2, 0::2], pm[1::2, 0::2], pm[0::2, 1::2], pm[1::2, 1::2]], axis=2).reshape(-1, 16)
        uniq, inverse, counts = np.unique(vecs, axis=0, return_inverse=True, return_counts=True)
        inverse = inverse.reshape(-1)
        d = self.data
        px = lambda k, j: struct.unpack_from('<H', d, self.body + 8 * k + 2 * j)[0]
        book = np.array([[c for j in range(4) for c in _premul(rgba(px(k, j), self.pixel))] for k in range(n)],
                        dtype=np.float64)
        wt = counts.astype(np.float64)
        for _ in range(iterations):
            lab = _nearest(uniq, book)
            for k in range(n):
                m = lab == k
                if m.any():
                    book[k] = (uniq[m] * wt[m, None]).sum(0) / wt[m].sum()
            used = np.bincount(lab, minlength=n)
            if (used == 0).any():       # empty codes take the worst-served blocks
                err = ((uniq - book[lab]) ** 2).sum(1) * wt
                for k, b in zip(np.nonzero(used == 0)[0], np.argsort(-err)):
                    book[k] = uniq[b]
        # quantize the codebook to the pixel format, then the final assignment against it
        codes = [[to_px(_unpremul(book[k, 4 * j:4 * j + 4]), self.pixel) for j in range(4)] for k in range(n)]
        qbook = np.array([[c for v in code for c in _premul(rgba(v, self.pixel))] for code in codes], dtype=np.float64)
        idx = _nearest(uniq, qbook)[inverse].reshape(h // 2, w // 2)
        out = bytearray(d)
        for k, code in enumerate(codes):
            for j, v in enumerate(code):
                struct.pack_into('<H', out, self.body + 8 * k + 2 * j, v)
        p = self.data_start()
        for by in range(h // 2):
            for bx in range(w // 2):
                out[p + tw(bx, by)] = int(idx[by, bx])
        if self.layout in (4, 0x11):              # the smaller levels: the picture averaged down, same codebook
            if w != h:
                raise ValueError('mipmapped VQ is only written for square textures')
            q = self.body + n * 8
            for d in self.mip_dims():
                f = w // d
                small = pm.reshape(d, f, d, f, 4).mean(axis=(1, 3)) if d > 1 else pm.mean(axis=(0, 1)).reshape(1, 1, 4)
                if d == 1:
                    blk = np.tile(small.reshape(1, 4), (4, 1)).reshape(1, 16)
                else:
                    blk = np.stack([small[0::2, 0::2], small[1::2, 0::2], small[0::2, 1::2], small[1::2, 1::2]],
                                   axis=2).reshape(-1, 16)
                li = _nearest(blk, qbook)
                m = max(1, d // 2)
                for by in range(m):
                    for bx in range(m):
                        out[q + tw(bx, by)] = int(li[by * m + bx])
                q += m * m
        return bytes(out)


def _premul(c):
    r, g, b, a = c
    return [r * a / 255, g * a / 255, b * a / 255, a]


def _unpremul(v):
    r, g, b, a = (float(x) for x in v)
    if a <= 0.5:
        return 0, 0, 0, 0
    return tuple(int(max(0, min(255, round(x)))) for x in (r * 255 / a, g * 255 / a, b * 255 / a, a))


def _nearest(vecs, book, chunk=4096):
    import numpy as np
    bb = (book ** 2).sum(1)
    out = np.empty(len(vecs), dtype=np.int64)
    for i in range(0, len(vecs), chunk):
        v = vecs[i:i + chunk]
        out[i:i + chunk] = np.argmin(bb[None, :] - 2 * v @ book.T, axis=1)
    return out


def find(data):
    """Offsets of every PVRT chunk in data."""
    out, i = [], 0
    while True:
        i = data.find(b'PVRT', i)
        if i < 0:
            return out
        if i + 16 <= len(data):
            w, h = struct.unpack_from('<HH', data, i + 12)
            if 8 <= w <= 1024 and 8 <= h <= 1024 and data[i + 9] in (1, 2, 3, 4, 5, 6, 7, 8, 9, 0x0B, 0x0D, 0x10, 0x11):
                out.append(i)
        i += 4


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['scan']:
        for f in argv[1:]:
            data = Path(f).read_bytes()
            for o in find(data):
                print(f'{f} 0x{o:x} {Texture(data, o).describe()}')
    elif len(argv) == 4 and argv[0] == 'png':
        data = Path(argv[1]).read_bytes()
        Texture(data, int(argv[2], 0)).to_image().save(argv[3])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
