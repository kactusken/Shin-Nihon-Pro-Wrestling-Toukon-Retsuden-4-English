#!/usr/bin/env python3
"""The game's text: reading, dumping to translation/text/ and writing English back.

  gametext.py dump menu|edit          MENU/ or EDIT/STRINGS.PAC -> translation/text/strings.txt, edit_strings.txt (keeps English)
  gametext.py roundtrip               prove the STRINGS.PAC writer reproduces the original bytes

STRINGS.PAC (verified in game): a PAC of one section at 8. The section is a table of 3200 u32
offsets (relative to the section start, 8) followed by the string pool; entry i is the Shift-JIS
string at table[i], NUL-terminated; zero offsets mark unused entries (3141..3199); newline 0x0A is
the only control code. The game draws ASCII in its fixed-pitch font at half the width of a
full-width character, so an English string takes one byte and one half-cell per letter: a 20-glyph
Japanese line (40 bytes) is a 40-letter English line. The strings are read by index, so the pool
can be rebuilt freely (shorter or longer).
"""
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
import paths  # noqa: E402

def jp_cols(text):
    """Half-width cells of a Japanese line: full-width characters take 2, ASCII and half-width kana 1."""
    return sum(1 if ord(c) < 0x100 or 0xff61 <= ord(c) <= 0xff9f else 2 for c in text)


# ---- STRINGS.PAC (two tables: MENU/ and EDIT/) -------------------------------------------------

class Table:
    """One STRINGS.PAC: disc path, text file, table size and how it spells a line break."""

    def __init__(self, disc_path, extracted_rel, textfile, size, newline, what):
        self.disc_path, self.rel, self.textfile, self.size, self.newline, self.what = \
            disc_path, extracted_rel, textfile, size, newline, what


TABLES = {
    'menu': Table('/MENU/STRINGS.PAC', 'MENU/STRINGS.PAC', 'strings.txt', 3200, b'\n',
                  'menus, option names and descriptions, titles, wrestler profiles, move names'),
    'edit': Table('/EDIT/STRINGS.PAC', 'EDIT/STRINGS.PAC', 'edit_strings.txt', 2700, b'\\n',
                  'the same menus as loaded in Edit mode, plus move and entrance names'),
}


def read_strings(d, size=3200):
    """-> list of `size` entries: bytes (without the NUL), or None for an unused entry."""
    assert struct.unpack_from('<II', d, 0) == (1, 8), 'STRINGS.PAC header changed'
    assert struct.unpack_from('<I', d, 8)[0] == size * 4, 'STRINGS.PAC table size changed'
    out = []
    for x in struct.unpack_from(f'<{size}I', d, 8):
        if not x:
            out.append(None)
            continue
        s = 8 + x
        out.append(bytes(d[s:d.index(b'\0', s)]))
    return out


def build_strings(entries):
    pool = bytearray()
    table = []
    base = len(entries) * 4
    for e in entries:
        if e is None:
            table.append(0)
            continue
        table.append(base + len(pool))
        pool += e + b'\0'
    return struct.pack('<II', 1, 8) + struct.pack(f'<{len(entries)}I', *table) + bytes(pool)


def entry_lines(raw, newline):
    """The lines of an entry (bytes): split at the table's line break (a real 0x0A or a literal backslash-n)."""
    return raw.decode('cp932').split(newline.decode('ascii'))


# ---- dump -----------------------------------------------------------------------------------------

HEADER_STRINGS = [
    '# {path}: {what}.',
    '# One block per table entry (id = entry number). JP lines are the original text, one per line of',
    '# the entry (a new line only where the Japanese has one). EN lines: plain ASCII, one per line.',
    '# The game draws a letter in half a Japanese character cell, so a 20-glyph Japanese line holds 40 letters.',
    '# Each block says its limit: `# fit W letters x N line(s)` - checked by lint.',
    '# Control codes: none. Do not write full-width characters.',
    '# `# field N` (added by hand): a fixed-width label - the build pads the English to N letters, so the',
    '# values, brackets and cursor drawn after it stay where the Japanese has them.',
]


FIELD = re.compile(r'#\s*field\s+(\d+)')


def field_width(block):
    """N of a block's `# field N` comment (a fixed-width label), or None."""
    for k, t in block.lines:
        m = FIELD.match(t) if k == '#' else None
        if m:
            return int(m.group(1))
    return None


def fit_for(i, lines):
    """(letters per line, lines) the English may use, from the Japanese and where the entry is drawn.
    Sentences (a long or multi-line text) get the 40-cell description box; short names keep the
    Japanese width (min 16). PROVISIONAL until measured in the game (rooms)."""
    n = max(jp_cols(l) for l in lines)
    if len(lines) > 1 or n >= 15:
        return max(40, n), max(2, len(lines))
    return max(16, n), 1


def dump_strings(which, extracted=None):
    t = TABLES[which]
    extracted = Path(extracted or paths.EXTRACTED)
    raw = read_strings((extracted / t.rel).read_bytes(), t.size)
    items = []
    for i, e in enumerate(raw):
        if not e:
            continue
        lines = entry_lines(e, t.newline)
        w, n = fit_for(i, lines)
        items.append((f'{i:04d}', '', lines, [f'# fit {w} letters x {n} line(s)']))
    path = paths.TEXT / t.textfile
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [h.format(path=t.rel, what=t.what) for h in HEADER_STRINGS]
    st = blocks.merge(path, header, items, generated=re.compile(r'# fit '))
    print(f'{path}: {len(items)} blocks ({st["kept"]} with English kept)')


# ---- build steps ----------------------------------------------------------------------------------

def encode(text, ident, where):
    try:
        return text.encode('ascii')
    except UnicodeEncodeError as e:
        bad = text[e.start]
        raise SystemExit(f'{where} block {ident}: {bad!r} can not be drawn - plain ASCII only')


def strings_step_for(which):
    t = TABLES[which]

    def step(path, files):
        """Write the English of translation/text/<file> into the STRINGS.PAC."""
        bf = blocks.BlockFile(path)
        entries = read_strings(files.get(t.disc_path), t.size)
        n = 0
        for b in bf.blocks:
            if not b.english:
                continue
            i = int(b.id)
            if entries[i] is None:
                raise SystemExit(f'{t.textfile} block {b.id}: unused entry in the original')
            en = t.newline.decode('ascii').join(b.english)
            w = field_width(b)
            if w is not None:
                if len(en) > w:
                    raise SystemExit(f'{t.textfile} block {b.id}: {len(en)} letters, the field holds {w}: shorten it')
                en = en.ljust(w)
            entries[i] = encode(en, b.id, t.textfile)
            n += 1
        if n:
            files.put(t.disc_path, build_strings(entries))
        print(f'text: {t.textfile}: {n} entries')
    return step


# ---- 1ST_READ.BIN strings -------------------------------------------------------------------------

EXE = '/1ST_READ.BIN'
EXE_BASE = 0x8C010000
EXE_REGION = (0xB9700, 0xCF000)       # the read-only text: error messages, move names, rosters, labels
# 0xCDC34-0xCEA2F inside it: the champion and tournament histories, fixed records without pointers -
# translation/text/champions.csv (tools/records.py TABLES), not exe.txt
JP = re.compile(r'[ぁ-んァ-ヶー一-龥Ａ-Ｚａ-ｚ０-９ｦ-ﾟ]')
# rows whose Japanese is a character grid or a key of the name-entry keyboards: they stay as they are
KEEP_KEYBOARD = re.compile(r'^[　ぁ-んァ-ヶー、。ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａ-ｚ特]*$')


KEYBOARD_TABLES = [(0xD6940, 0xD69C0), (0xD73F0, 0xD7430)]   # pointer arrays of the name-entry keyboard rows


def is_keyboard(off, ptrs):
    """A row of the name-entry keyboards (pointed to from the keyboard tables): the keys stay."""
    return any(lo <= p < hi for p in ptrs.get(EXE_BASE + off, []) for lo, hi in KEYBOARD_TABLES)


def exe_pointer_index(d):
    """{address: [file offsets of aligned words holding it]} for addresses inside the executable."""
    idx = {}
    for i in range(0, len(d) - 3, 4):
        w = struct.unpack_from('<I', d, i)[0]
        if EXE_BASE <= w < EXE_BASE + len(d):
            idx.setdefault(w, []).append(i)
    return idx


def exe_strings(d, ptrs=None):
    """[(offset, bytes, refs, slot)] for the Japanese strings of the executable's text region."""
    ptrs = ptrs if ptrs is not None else exe_pointer_index(d)
    out = []
    i = EXE_REGION[0]
    while i < EXE_REGION[1]:
        if d[i] == 0:
            i += 1
            continue
        e = d.index(b'\0', i)
        raw = bytes(d[i:e])
        i0, i = i, e + 1
        try:
            t = raw.decode('cp932')
        except UnicodeDecodeError:
            continue
        if any(ord(c) < 0x20 and c != '\n' for c in t) or not JP.search(t):
            continue
        refs = len(ptrs.get(EXE_BASE + i0, []))
        if refs == 0:                 # not pointed to: record data (champions.csv) or not text
            continue
        k = e
        while k < len(d) and d[k] == 0:
            k += 1
        slot = k - i0                  # bytes up to the next non-zero byte (the string, its NUL and the padding)
        out.append((i0, raw, refs, slot))
    return out


def exe_dump(extracted=None):
    extracted = Path(extracted or paths.EXTRACTED)
    d = (extracted / '1ST_READ.BIN').read_bytes()
    items = []
    ptrs = exe_pointer_index(d)
    for off, raw, refs, slot in exe_strings(d, ptrs):
        t = raw.decode('cp932')
        if refs and is_keyboard(off, ptrs):
            continue
        lines = t.split('\n')
        w, n = exe_fit(refs, slot, lines)
        items.append((f'{off:06X}', f'refs={refs} slot={slot}', lines, [f'# fit {w} letters x {n} line(s)']))
    path = paths.TEXT / 'exe.txt'
    header = ['# 1ST_READ.BIN strings: error and network messages, move names, wrestler names, labels.',
              '# One block per string (id = file offset). `refs` = pointers to it (0: a fixed field in a record), `slot` = bytes it may use in place.',
              '# JP lines: the original; EN lines: plain ASCII, one per line (a new line only where the Japanese has one).',
              '# Each block says its limit: `# fit W letters x N line(s)`. A JP text ending in spaces is a padded label: its',
              '# English is padded to the same length by the build. `%s` `%d` `%-16s`...: printf codes - keep them, in the same order.',
              '# A string longer than its slot is moved if it has pointers (refs > 0), else it must fit.']
    st = blocks.merge(path, header, items, generated=re.compile(r'# fit '))
    print(f'{path}: {len(items)} blocks ({st["kept"]} with English kept)')


def exe_fit(refs, slot, lines):
    n = max(jp_cols(l) for l in lines)
    if refs == 0:
        return slot - 1, len(lines)
    if len(lines) > 1 or n >= 15:
        return max(40, n), len(lines)
    return max(16, n), 1


def exe_step(path, files):
    """Write the English of translation/text/exe.txt into 1ST_READ.BIN. A string that fits its slot is
    written in place. Where strings with pointers overflow, the run of neighbouring translated strings
    that have pointers is packed one after another over its whole span and its pointers are rewritten
    (the run's span is never longer than the Japanese it replaces, so the room is always there)."""
    bf = blocks.BlockFile(path)
    d = files.get(EXE)
    ptrs = exe_pointer_index(d)
    cands = {off: (refs, slot) for off, raw, refs, slot in exe_strings(d, ptrs)}
    rows = {}
    for b in bf.blocks:
        if not b.english:
            continue
        off = int(b.id, 16)
        meta = dict(kv.split('=') for kv in b.meta.split())
        jp = '\n'.join(bf.source(b))
        en = '\n'.join(b.english)
        if jp != jp.rstrip(' '):                   # a padded label keeps its width
            en = en.ljust(len(jp.encode('cp932')))
        raw = encode(en, b.id, 'exe.txt') + b'\0'
        refs, slot = int(meta['refs']), int(meta['slot'])
        if cands.get(off) != (refs, slot):
            raise SystemExit(f'exe.txt block {b.id}: the string changed in the original (meta {refs}/{slot}) - dump again')
        rows[off] = (raw, refs, slot)
    for off, (raw, refs, slot) in rows.items():
        if refs == 0 and len(raw) > slot:
            raise SystemExit(f'exe.txt block {off:06X}: {len(raw) - 1} bytes, the fixed slot holds {slot - 1}: shorten it')
    # every pointed-to string takes part in repacking, translated or not (untranslated ones keep their text)
    allrows = dict(rows)
    for off, (refs, slot) in cands.items():
        if off not in allrows and refs:
            e = d.index(b'\0', off)
            allrows[off] = (bytes(d[off:e + 1]), refs, slot)
    runs, cur = [], []
    for off in sorted(allrows):
        raw, refs, slot = allrows[off]
        if refs and cur and cur[-1] + allrows[cur[-1]][2] == off:
            cur.append(off)
        else:
            if cur:
                runs.append(cur)
            cur = [off] if refs else []
    if cur:
        runs.append(cur)
    packed, out = 0, []
    done = set()
    free = []                                   # [start, end) ranges of free bytes
    for run in runs:
        if all(len(allrows[o][0]) <= allrows[o][2] for o in run):
            continue
        start = run[0]
        span = allrows[run[-1]][2] + run[-1] - start
        keep = list(run)
        total = sum(len(allrows[o][0]) for o in keep)
        while total > span:                     # move the longest translated string out of the run
            cand = [o for o in keep if o in rows]
            o = max(cand, key=lambda o: len(allrows[o][0]))
            keep.remove(o)
            out.append(o)
            total -= len(allrows[o][0])
        pos = start
        d[start:start + span] = bytes(span)
        for o in keep:
            raw = allrows[o][0]
            d[pos:pos + len(raw)] = raw
            for p in ptrs.get(EXE_BASE + o, []):
                struct.pack_into('<I', d, p, EXE_BASE + pos)
            done.add(o)
            pos += len(raw)
        free.append([pos, start + span])
        packed += len(keep)
    for off, (raw, refs, slot) in rows.items():
        if off not in done and off not in out:
            d[off:off + slot] = raw + bytes(slot - len(raw))
            if slot - len(raw) >= 4 and off not in {o for r in runs for o in r if o in done}:
                free.append([off + len(raw), off + slot])
    short = []
    for o in sorted(out, key=lambda o: -len(allrows[o][0])):
        raw = allrows[o][0]
        for f in free:
            if f[1] - f[0] >= len(raw):
                new = f[0]
                d[new:new + len(raw)] = raw
                f[0] += len(raw)
                break
        else:
            short.append(f'{o:06X} ({len(raw) - 1} bytes)')
            continue
        for p in ptrs.get(EXE_BASE + o, []):
            struct.pack_into('<I', d, p, EXE_BASE + new)
    if short:
        raise SystemExit('exe.txt: no room for these (shorten them or other strings near them): ' + ', '.join(short))
    files.put(EXE, d)
    print(f'text: exe.txt: {len(rows)} strings ({packed} repacked, {len(out)} moved)')


def roundtrip():
    ok = True
    for name, t in TABLES.items():
        d = (Path(paths.EXTRACTED) / t.rel).read_bytes()
        same = build_strings(read_strings(d, t.size)) == d
        print(f'{t.rel} round trip:', 'identical' if same else 'DIFFERENT')
        ok &= same
    return ok


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['dump'] and len(argv) == 2 and argv[1] in TABLES:
        dump_strings(argv[1])
    elif argv[:2] == ['dump', 'exe']:
        exe_dump()
    elif argv[:1] == ['roundtrip']:
        sys.exit(0 if roundtrip() else 1)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
