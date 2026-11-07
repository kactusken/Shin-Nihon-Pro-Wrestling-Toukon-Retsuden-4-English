#!/usr/bin/env python3
"""Name entry: up to 16 letters, stored as normal (half-width) ASCII - code patches for build.py.

    nameentry.py            assemble the patch and list the regions it replaces
    nameentry.py --check    also check the original code there in extracted/1ST_READ.BIN
    nameentry.py --sha      print the SHA-1 of each original region (for ORIGINAL_SHA1)

The game's name editor (constructor 0x8C095CC0, docs/TECHNICAL.md "Name entry") works in
full-width cells: its ABC/123 page types Ａ, ２ ... (two bytes each), and both screens that use it
in Edit mode ask for 8 cells - 16 bytes, the size of the name fields they fill. English letters
therefore take double room and only 8 fit. The patches:

- both callers ask for 16 cells (the editor accepts 1..20) and allocate their parent object
  44 bytes instead of 28, so its copy of the name (+8) holds 16 cells and the end byte;
- LOAD (parent setup): copies the stored name into that buffer, turning ASCII back into full-width
  cells so the editor can edit it, padded with full-width spaces to 16 cells;
- STORE (parent update, after OK): full-width letters, digits and the symbols in TABLE become ASCII,
  everything is packed into the 16-byte field (an ASCII character costs 1 byte, kana and kanji 2;
  what doesn't fit is dropped) and ends with a 0 byte, as the original copy did.

The two screens: Edit wrestler name (record 0x8C28236C + 0x47A) and the Edit "Thinking" names
(17-byte slots at 0x8C282840). The new code lives in the space of the code it replaces (the
original padding loops, an unrolled copy and a redundant label update); nothing else moves.
"""
import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sh4  # noqa: E402

FILE = '/1ST_READ.BIN'
BASE = 0x8C010000
GROUP = 'name-entry'

# Full-width symbols (Shift-JIS 0x81xx) that become ASCII: (second byte, ASCII). The space must
# stay first (LOAD turns unknown ASCII into it). Pairs end with a 0 byte.
SYMBOLS = [(0x40, ' '), (0x49, '!'), (0x48, '?'), (0x95, '&'), (0x44, '.'), (0x7C, '-'),
           (0x66, "'"), (0x5E, '/'), (0x7B, '+'), (0x69, '('), (0x6A, ')'), (0x94, '#'),
           (0x97, '@'), (0x93, '%'), (0x81, '='), (0x83, '<'), (0x84, '>'), (0x47, ';')]

# Pool words of the original code that these regions read (their values may be changed by the
# text steps when strings move, so the code loads them from there):
SYMS = {
    'W47A': 0x8C096F3A,      # .word 0x047A: name offset in the Edit record
    'L_BLANK': 0x8C096F54,   # -> the blank name (8 full-width spaces)
    'L_DEF': 0x8C097088,     # -> the default name ("Young Lion")
    'L_REC': 0x8C09708C,     # -> 0x8C2827E6, the Edit wrestler name
    'L_IDX': 0x8C09718C,     # -> current Thinking slot number
    'L_TNAMES': 0x8C097190,  # -> 0x8C282840, Thinking names (17 bytes each)
    'L_TIDX': 0x8C0972C8,    # -> current Thinking slot number (update's pool)
    'L_TDEF': 0x8C0972D4,    # -> table of default Thinking names
    'L_TNAMES2': 0x8C0972D8,  # -> 0x8C282840 (update's pool)
    'P1_DONE': 0x8C096EE8,   # parent 1 setup: setText(editor, parent+8) follows
    'P2_DONE': 0x8C097108,   # parent 2 setup: the same
    'P2_RET1': 0x8C09720C,   # parent 2 update: return 1
}

# (start, end exclusive, None, source): new code for a region, padded with nops. Sources may use
# each other's labels; the original bytes are checked against ORIGINAL_SHA1.
REGIONS = [
    # Parent 1 (Edit wrestler) setup, after strcmp(record name, default): r0 = 0 when it is the
    # default, then the editor starts blank. Replaces the label update, padding and strcpy.
    (0x8C096E8E, 0x8C096EE8, None, '''
        mov.w W47A,r5
        tst r0,r0
        bf/s p1go
        add r13,r5              ; r5 = the record's name
        mov.l L_BLANK,r5
    p1go:
        mov r14,r4
        bsr LOAD
        add #8,r4
        bra P1_DONE
        nop
    TABLE:
    ''' + '\n'.join(f'        .byte {t:#x},{ord(c)}' for t, c in SYMBOLS) + '''
        .byte 0
        .align 1
    LOAD2:                      ; ASCII (r0) that is no symbol: digits, letters, else a space
        mov #-126,r1            ; lead 0x82
        mov r0,r2
        add #-48,r2
        mov #43,r3
        cmp/hs r3,r2            ; '0'..'Z' -> second byte c+0x1F
        bf/s l2go
        add #31,r0
        add #-49,r2             ; = c - 'a'
        mov #26,r3
        cmp/hs r3,r2            ; 'a'..'z' -> c+0x20
        bf/s l2go
        add #1,r0
        mov #-127,r1            ; anything else: a full-width space
        mov #64,r0
    l2go:
        bra lput
        nop
    '''),
    # Parent 1 update after OK, from the strcmp(parent+8, "") result on: T = 1 when empty.
    (0x8C096FC6, 0x8C09703A, None, '''
        mov r14,r5
        bf/s p1st
        add #8,r5
        mov.l L_DEF,r5          ; empty: the default name
    p1st:
        mov.l L_REC,r4
        bsr STORE
        nop
        lds.l @r15+,pr
        mov #1,r0
        rts
        mov.l @r15+,r14
    STORE:                      ; r4 = field (16 bytes + end), r5 = full-width name
        mov.l T_ADDR1,r7
        mov #16,r6
    snext:
        mov.b @r5+,r0
        tst r0,r0
        bt send
        cmp/pz r0
        bt/s s1                 ; already ASCII: as it is
        mov r0,r2
        mov.b @r5+,r1           ; second byte
        cmp/eq #-127,r0
        bt s81
        cmp/eq #-126,r0
        bf s2
        mov r1,r2               ; 0x82: 0x4F..0x79 digits and A-Z, 0x81..0x9A a-z
        extu.b r2,r2
        add #-79,r2
        mov #43,r3
        cmp/hs r3,r2
        bf/s s1
        add #48,r2
        add #-98,r2             ; = second byte - 0x81
        mov #26,r3
        cmp/hs r3,r2
        bf/s s1
        add #97,r2
    s2:                         ; two bytes r0, r1 if both fit
        mov #2,r2
        cmp/hs r2,r6
        bf send
        mov.b r0,@r4
        add #1,r4
        add #-1,r6
        mov r1,r2
    s1:                         ; one byte r2 if it fits
        tst r6,r6
        bt send
        mov.b r2,@r4
        add #1,r4
        bra snext
        add #-1,r6
    s81:
        bra SLOOK
        mov r7,r3
    send:
        mov #0,r0
        rts
        mov.b r0,@r4
        .align 2
    T_ADDR1:
        .long TABLE
    '''),
    # Parent 2 (Thinking names) setup, after the editor was made: keeps "store it in +4",
    # replaces the label update, padding and strcpy.
    (0x8C0970A2, 0x8C097108, None, '''
        mov.l L_IDX,r2
        mov.l L_TNAMES,r1
        mov.l @r2,r5
        mov r5,r3
        shll2 r5
        shll2 r5
        add r3,r5
        add r1,r5               ; r5 = names + slot * 17
        mov r14,r4
        bsr LOAD
        add #8,r4
        bra P2_DONE
        nop
    LOAD:                       ; r4 = buffer (33 bytes), r5 = stored name
        mov.l T_ADDR2,r7
        mov #16,r6
    lnext:
        mov.b @r5+,r0
        tst r0,r0
        bt lpad
        cmp/pz r0
        bt la
        mov r0,r1               ; a two-byte character: as it is
        mov.b @r5+,r0
    lput:                       ; r1, r0 = the cell
        mov.b r1,@r4
        add #1,r4
        mov.b r0,@r4
        dt r6
        bf/s lnext
        add #1,r4
        mov #0,r0
        rts
        mov.b r0,@r4
    lpad:
        add #-1,r5              ; stay on the end byte: the rest is spaces
    lunk:
        mov #-127,r1
        bra lput
        mov #64,r0
    la:
        mov r7,r3
    llk:
        mov.b @r3+,r2
        tst r2,r2
        bt lsym
        mov.b @r3+,r1
        cmp/eq r1,r0
        bf llk
        mov #-127,r1
        bra lput
        mov r2,r0
    lsym:
        bra LOAD2
        nop
        .align 2
    T_ADDR2:
        .long TABLE
    '''),
    # Parent 2 update after OK, from the strcmp(parent+8, "") result on: T = 1 when empty.
    (0x8C0971D4, 0x8C09720C, None, '''
        mov.l @r13,r1           ; slot
        mov r14,r5
        bf/s p2st
        add #8,r5
        mov r1,r0               ; empty: that slot's default name
        shll2 r0
        mov.l L_TDEF,r2
        mov.l @(r0,r2),r5
    p2st:
        mov r1,r4
        shll2 r4
        shll2 r4
        add r1,r4
        mov.l L_TNAMES2,r2
        bsr STORE
        add r2,r4
        bra P2_RET1
        nop
    SLOOK:                      ; STORE: 0x81 symbols; r1 = second byte, r3 = TABLE
        mov.b @r3+,r2
        tst r2,r2
        bt sl2
        cmp/eq r1,r2
        bf/s SLOOK
        mov.b @r3+,r2
        bra s1
        nop
    sl2:
        bra s2
        nop
    '''),
]

# One-instruction changes: (address, original, new, what)
SMALL = [
    (0x8C0794D4, sh4.assemble('mov #28,r4', 0)[0], sh4.assemble('mov #44,r4', 0)[0], 'parent 1 size 28 -> 44'),
    (0x8C0794F0, sh4.assemble('mov #28,r4', 0)[0], sh4.assemble('mov #44,r4', 0)[0], 'parent 2 size 28 -> 44'),
    (0x8C096E70, sh4.assemble('mov #8,r5', 0)[0], sh4.assemble('mov #16,r5', 0)[0], 'wrestler name: 16 cells'),
    (0x8C097064, sh4.assemble('mov #8,r5', 0)[0], sh4.assemble('mov #16,r5', 0)[0], 'Thinking name: 16 cells'),
]

# SHA-1 of each region's original bytes (the original code is not kept in the repository).
ORIGINAL_SHA1 = {
    0x8C096E8E: '84f631e4ce6ca9c1062a916e7049fd8b05d4b652',
    0x8C096FC6: '67aabbd7d5a4661e3d2e9b2849783111ba8d805e',
    0x8C0970A2: '4be22c3878b4d72856c9120d19de75535c8734ff',
    0x8C0971D4: '36892cc7658881afb68e1607678213a366f1fb44',
}


def assemble_all():
    """-> [(start, end, code)] with the code padded to the region with nops."""
    symbols = dict(SYMS)
    for name in ('LOAD', 'LOAD2', 'STORE', 'SLOOK', 'TABLE', 'lput', 'lunk', 's1', 's2'):
        symbols.setdefault(name, 0x8C097000)
    out = []
    for _ in range(3):  # labels of later regions settle on the second pass
        out = []
        for start, end, _sha, src in REGIONS:
            code, syms = sh4.assemble(src, start, symbols)
            if len(code) > end - start:
                raise SystemExit(f'nameentry: region {start:#x} needs {len(code)} bytes, has {end - start}')
            symbols.update({k: v for k, v in syms.items() if not k.startswith('__')})
            out.append((start, end, code + b'\x09\x00' * ((end - start - len(code)) // 2)))
    return out


def patches(original):
    """CODE_PATCHES rows for build.py. `original(addr, n)` returns the file's bytes there (the
    build checks them again before writing)."""
    rows = []
    for addr, old, new, what in SMALL:
        rows.append((GROUP, FILE, addr, old, new, what))
    for start, end, code in assemble_all():
        old = original(start, end - start)
        want = ORIGINAL_SHA1[start]
        if hashlib.sha1(old).hexdigest() != want:
            raise SystemExit(f'nameentry: unexpected original code at {start:#x} - not the original '
                             f'1ST_READ.BIN, or a text step changed it')
        rows.append((GROUP, FILE, start, old, code, None))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='compare with extracted/1ST_READ.BIN')
    ap.add_argument('--sha', action='store_true', help='print the SHA-1 of each original region')
    import paths
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    for start, end, code in assemble_all():
        print(f'{start:#x}-{end:#x}: {end - start} bytes')
    if args.check or args.sha:
        data = (paths.EXTRACTED / '1ST_READ.BIN').read_bytes()
        for start, end, _code in assemble_all():
            h = hashlib.sha1(data[start - BASE:end - BASE]).hexdigest()
            ok = h == ORIGINAL_SHA1[start]
            print(f'{start:#x}: {h}' + ('' if args.sha else ('  ok' if ok else '  DIFFERENT')))
        for addr, old, _new, what in SMALL:
            ok = data[addr - BASE:addr - BASE + len(old)] == old
            print(f'{addr:#x}: {what}: {"ok" if ok else "DIFFERENT"}')


if __name__ == '__main__':
    main()
