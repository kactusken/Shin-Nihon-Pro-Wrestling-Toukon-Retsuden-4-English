#!/usr/bin/env python3
"""The game's .PAC archives: read the nested tables.

  pac.py ls FILE            sections and entries of a PAC (offset, size, first words)

Layout (verified on the disc): u32 n, then n absolute section offsets. Each section is a table of
entries in one of two forms (both offsets are relative to the section start):
  counted:  u32 count, count u32 offsets      (MEIKAN.PAC, WRES.PAC, texture packs)
  plain:    count u32 offsets, count = first offset / 4   (STRINGS.PAC)
An entry runs to the next entry's offset (the last to the section end). An offset of 0 is an
unused slot. Which form a section has is told from its first two words.
"""
import struct
import sys
from pathlib import Path


def section_table(d, start, end):
    """-> (form, [(offset, size)]) of the entries of the section d[start:end]."""
    if end - start < 8:
        return None, []
    w0, w1 = struct.unpack_from('<II', d, start)
    if w1 == 4 * (w0 + 1) and w0 < 100000:
        form, n, tab = 'counted', w0, start + 4
    elif w0 % 4 == 0 and 0 < w0 < end - start:
        form, n, tab = 'plain', w0 // 4, start
    else:
        return None, []
    offs = [x for x in struct.unpack_from(f'<{n}I', d, tab)]
    real = sorted({x for x in offs if x})
    out = []
    for x in offs:
        if not x:
            out.append((0, 0))
            continue
        nxt = next((y for y in real if y > x), end - start)
        out.append((start + x, nxt - x))
    return form, out


def sections(d):
    """-> [(start, end)] of the top-level sections."""
    n = struct.unpack_from('<I', d, 0)[0]
    offs = struct.unpack_from(f'<{n}I', d, 4)
    ends = [o for o in offs[1:]] + [len(d)]
    return list(zip(offs, ends))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != 'ls':
        sys.exit(__doc__)
    d = Path(argv[1]).read_bytes()
    for k, (s, e) in enumerate(sections(d)):
        form, ents = section_table(d, s, e)
        print(f'section {k}: {s:#x}-{e:#x} ({e - s} bytes) {form} {len(ents)} entries')
        shown = 0
        for i, (o, sz) in enumerate(ents):
            if shown >= 6 and i < len(ents) - 1:
                continue
            shown += 1
            head = d[o:o + 16].hex() if o else '-'
            print(f'  [{i}] {o:#x} {sz:#x} {head}')


if __name__ == '__main__':
    main()
