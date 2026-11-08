#!/usr/bin/env python3
"""The guide's data block (docs/guide/index.html): roster, wrestler profiles and every move set.

  python3 tools/guidedata.py [--check] [--json OUT]

Reads the original's tables with the English of translation/text/ (strings.txt, exe.txt), so the
page always shows the patch's names:
  1ST_READ.BIN  group names 0x8C0DF87C (8 pointers) and each group's first id 0x8C0DF89C (8 bytes);
                full names 0x8C0DF8A4 and in-match names 0x8C0DF9F4 (42 pointers each); HP 0x8C0D8CF0
                (5 bytes per wrestler: Main, Head, Torso, Arms, Legs); parameters 0x8C0D8EEF (26 bytes:
                Attack for 13 move types, then Defense); critical combos 0x8C0D8AF8 (3 x u16 start,
                u16 finish); move types 0x8C0E2A28 (a byte per action); in-match move names 0xC2154
                (600 pointers, file offset).
  MOTION/ACTTBL.PAC  "ACT2", u16, u16 600, then a row of 600 u16 actions per wrestler (slot -> action).
  MOTION/NBATTLE.PAC section 1: an action script per action; op 50 shows a name in the match, ops 15
                and 19 hand over to another action (whose names are shown too).
  MENU/STRINGS.PAC (English from strings.txt): Directory profile 1159 + 4*id (name/born/birthplace/
                size; titles + signature moves; two bio parts), theme 0469 + id, parameter names
                0546-0558, HP names 0832-0836, Edit-mode move names 1339 + action.
The move sheet (LAYOUT) puts each per-wrestler slot under a situation, a button and an opponent
state; slot numbers and inputs are in docs/CONTROLS.md. --json also writes the data, readable.
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pagedata  # noqa: E402
import paths  # noqa: E402

B = 0x8C010000
GROUP_NAMES, GROUP_START = 0x8C0DF87C, 0x8C0DF89C
NAMES, SHORT = 0x8C0DF8A4, 0x8C0DF9F4
HP, PARAM, COMBOS, TYPES_AT = 0x8C0D8CF0, 0x8C0D8EEF, 0x8C0D8AF8, 0x8C0E2A28
DISP = 0xC2154
COUNT = 42
TYPE_NAME = [None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]   # action type 1-13 = parameter 0-12

# Hidden wrestlers (docs/HIDDEN_CONTENT.md): Burning Spirit clear that unlocks them, title-screen code.
UNLOCK = {
    15: ('Clear Burning Spirit singles with Kensuke Sasaki', 'L X Y B X Y B R'),
    16: ('Clear Burning Spirit tag with Riki Choshu', 'L X Y A X Y A R'),
    17: ('Clear Burning Spirit tag with Antonio Inoki', 'L X B X X B X R'),
    18: ('Clear Burning Spirit tag with Power Warrior', 'L X Y X X Y X R'),
    19: ('Clear Burning Spirit tag with The Great Muta', 'L X A X X A X R'),
    31: ('Clear Burning Spirit singles with Naoya Ogawa', 'L X Y A B X Y R'),
    41: ('Clear Burning Spirit singles with The Great Sasuke', 'L X A Y B X A R'),
}

STATES = ['N', 'S', 'M', 'L']   # opponent normal, then groggy levels


def _std(sec, bases):
    rows = []
    for btn, base in bases:
        rows.append((sec, btn, [(g, base + 2 * i) for i, g in enumerate(STATES)]))
        rows.append((sec, btn + ' + D-Pad', [(g, base + 2 * i + 1) for i, g in enumerate(STATES)]))
    return rows


def _four(sec, items):
    return [(sec, btn, [(g, s + i) for i, g in enumerate(STATES)]) for btn, s in items]


# (situation, row, [(column, slot)]): the slots a player can choose. Left out: the automatic back
# and kick-catch reversals (234, 235, 448, 449) and the entrance, call and victory performances.
LAYOUT = (
    _std('Grapple, facing', [('A', 240), ('B', 248), ('Y', 256)])
    + _std('Grapple, behind', [('A', 302), ('B', 310), ('Y', 318)])
    + _four('Running, opponent facing you', [('A', 265), ('B', 269), ('Y', 273)])
    + _four('Running, at his back', [('A', 277), ('B', 281), ('Y', 285)])
    + [('Counters', 'A', [('Dash counter', 290), ('Whip counter', 293), ('Rope rebound', 296), ('Corner rebound', 299)]),
       ('Counters', 'B', [('Dash counter', 291), ('Whip counter', 294), ('Rope rebound', 297), ('Corner rebound', 300)]),
       ('Counters', 'Y', [('Dash counter', 292), ('Whip counter', 295), ('Rope rebound', 298), ('Corner rebound', 301)]),
       ('Opponent down, face up', 'A', [('Head', 352), ('Upper body', 353), ('Lower body', 357), ('Legs', 356)]),
       ('Opponent down, face up', 'Y', [('Head', 368), ('Upper body', 369), ('Lower body', 373), ('Legs', 372)]),
       ('Opponent down, face up', 'B (lift)', [('Upper body', 360), ('Lower body', 364)]),
       ('Opponent down, face down', 'A', [('Head', 376), ('Upper body', 377), ('Lower body', 381), ('Legs', 380)]),
       ('Opponent down, face down', 'Y', [('Head', 392), ('Upper body', 393), ('Lower body', 397), ('Legs', 396)]),
       ('Opponent down, face down', 'B (lift)', [('Upper body', 384), ('Lower body', 388)]),
       ('Pins', 'X, face up', [('Head', 469), ('Upper body', 470), ('Lower body', 474), ('Legs', 473)]),
       ('Pins', 'X, face down', [('Head', 477), ('Upper body', 478), ('Lower body', 482), ('Legs', 481)]),
       ('Corner', 'Opponent groggy in the corner', [('A', 433), ('B', 434), ('Y', 435)]),
       ('Corner', 'Corner charge', [('Into the corner', 436), ('Into the barrier', 437)]),
       ('Opponent on the top rope', 'Facing you', [('A, climbing', 400), ('B, climbing', 407), ('B, groggy', 408)]),
       ('Opponent on the top rope', 'Facing away', [('B, climbing', 409), ('B, groggy', 410)]),
       ('Opponent on the top rope', 'Avalanche B, facing you', [('S', 401), ('M', 402), ('L', 403)]),
       ('Opponent on the top rope', 'Avalanche B, facing away', [('S', 404), ('M', 405), ('L', 406)])]
    + _four('From the top rope', [('A, opponent standing', 411)])
    + [('From the top rope', 'B / Y, opponent standing', [('B, M', 417), ('B, L', 418), ('Y, M', 421), ('Y, L', 422)]),
       ('From the top rope', 'A, opponent down', [('Face up, by the ropes', 424), ('Face up, Toukon Rush', 425),
                                                  ('Face up, by the corner', 426), ('Face down, by the ropes', 427),
                                                  ('Face down, by the corner', 428)])]
    + _four('From the top rope', [('A, opponent outside', 429)])
    + _four('Ring and outside', [('A, to opponent outside', 327), ('A, outside, mid range', 331),
                                 ('A, apron to outside', 347)])
    + [('Ring and outside', 'Ring to apron', [('A', 335), ('B', 336), ('Y', 337)]),
       ('Ring and outside', 'On the apron, facing him', [('A', 338), ('B', 339), ('Y', 340)]),
       ('Ring and outside', 'On the apron, facing away', [('A', 341), ('B', 342), ('Y', 343)]),
       ('Ring and outside', 'Apron to ring', [('A', 344), ('B', 345), ('Y', 346)]),
       ('Other', 'Get-up attack', [('A', 438), ('B', 440), ('Y', 442)]),
       ('Other', 'Full nelson, A', [('Close', 444), ('Dash', 445), ('Top rope', 446)]),
       ('Other', 'Save (cut in), A', [('Opponent down', 229), ('Opponent standing', 230)]),
       ('Taunts', 'L / R', [('Normal', 450), ('Normal + D-Pad', 451), ('Opp. groggy or down', 452),
                            ('Groggy/down + D-Pad', 453)]),
       ('Double team', 'A', [('Side by side, front', 515), ('Front and back', 516), ('Corner', 517)]),
       ('Double team', 'B', [('Side by side, front', 518), ('Front and back', 519), ('Side by side, behind', 520),
                             ('Corner 1', 521), ('Corner 2', 560), ('Corner 3', 561)]),
       ('Double team', 'Y', [('Side by side, front', 522), ('Side by side, behind', 523),
                             ('Down, upper body', 524), ('Down, lower body', 525)])]
)


def u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def blocks(path, tag='EN '):
    """id -> list of the lines with this tag (EN, JP) of a translation text file."""
    out = {}
    for blk in re.split(r'\n(?=@ )', path.read_text(encoding='utf-8')):
        m = re.match(r'@ (\S+)', blk)
        if m:
            out[m.group(1)] = [ln[3:] for ln in blk.split('\n') if ln.startswith(tag)]
    return out


def profile(g, w):
    """The Wrestler Directory text of wrestler w: four blocks that flow as one page - name, born,
    birthplace, size; titles; the signature moves (the Japanese line ending 等, "etc."); a bio."""
    pairs = []
    for k in range(4):
        i = '%04d' % (1159 + 4 * w + k)
        en, jp = g.ms.get(i, []), g.ms_jp.get(i, [])
        pairs += list(zip(jp, en)) if len(jp) == len(en) else [('', e) for e in en]
    out = dict(born='', origin='', size='', titles=[], signature='', bio='')
    head = next((n for n, (_, e) in enumerate(pairs) if re.search(r'\d+cm', e)), 0)
    for _, e in pairs[1:head + 1]:   # the name, then born, birthplace and size (some have size only)
        if re.search(r'\d+cm', e):
            out['size'] = e
        elif e.startswith('Born '):
            out['born'] = e[5:]
        else:
            out['origin'] = e
    rest, n = pairs[head + 1:], 0
    # titles: lines starting 第/初代 ("Nth holder"), and their wrapped "...Champion" ends
    start, wrap = re.compile('^(第|初代)'), re.compile(r'チャンピオン(（.*）)?$')
    while n < len(rest) and (start.match(rest[n][0]) or (n and wrap.search(rest[n][0]))):
        j, e = rest[n]
        if start.match(j) and not (out['titles'] and out['titles'][-1].endswith('/')):
            out['titles'].append(e.strip())
        else:
            out['titles'][-1] += ('' if out['titles'][-1].endswith('/') else ' ') + e.strip()
        n += 1
    sig = next((k for k in range(n, len(rest)) if rest[k][0].rstrip().endswith('等')), None)
    if sig is not None:   # the signature moves, sometimes over two lines, end in 等 ("etc.")
        lines = [e.strip().rstrip(',') for _, e in rest[n:sig + 1]]   # a line break separates two moves
        out['signature'] = re.sub(r',? etc\.$', '', ', '.join(lines))
        n = sig + 1
    out['bio'] = ' '.join(e.strip() for _, e in rest[n:])
    return out


class Game:
    def __init__(self):
        ex = paths.EXTRACTED
        for f in ('1ST_READ.BIN', 'MOTION/ACTTBL.PAC', 'MOTION/NBATTLE.PAC'):
            if not (ex / f).exists():
                sys.exit(f'{paths.show(ex / f)} missing: run python3 tools/extract.py first')
        self.x = (ex / '1ST_READ.BIN').read_bytes()
        a = (ex / 'MOTION/ACTTBL.PAC').read_bytes()
        if a[:4] != b'ACT2':
            sys.exit('ACTTBL.PAC: not an ACT2 table - is extracted/ from the original?')
        cols = u16(a, 6)
        self.rows = [struct.unpack_from('<%dH' % cols, a, 8 + 2 * cols * r) for r in range(COUNT)]
        nb = (ex / 'MOTION/NBATTLE.PAC').read_bytes()
        s1 = u32(nb, 8)
        n = u32(nb, s1 + 8)
        offs = struct.unpack_from('<%dI' % n, nb, s1 + 12)
        base = s1 + 12 + 4 * n
        valid = sorted(set(o for o in offs if o != 0xFFFFFFFF))
        nxt = {o: (valid[i + 1] if i + 1 < len(valid) else len(nb) - base) for i, o in enumerate(valid)}
        self.scripts = [None if o == 0xFFFFFFFF else nb[base + o:base + nxt[o]] for o in offs]
        self.ms = blocks(paths.TEXT / 'strings.txt')
        self.ms_jp = blocks(paths.TEXT / 'strings.txt', 'JP ')
        self.exe = blocks(paths.TEXT / 'exe.txt')
        self.types = self.x[TYPES_AT - B:TYPES_AT - B + 1500]
        self.disp = struct.unpack_from('<600I', self.x, DISP)

    def menu(self, i):
        return ' '.join(self.ms.get('%04d' % i, []))

    def exe_at(self, ptr):
        return ' '.join(self.exe.get('%06X' % (ptr - B), []))

    def ptr(self, at, i):
        return u32(self.x, at - B + 4 * i)

    def walk(self, a):
        """Ops of action a's script: (opcode, bytes)."""
        s = self.scripts[a] if a < len(self.scripts) else None
        ops, j = [], 4
        while s and j < len(s) and s[j] < len(OPLEN):
            ops.append((s[j], s[j:j + 4 * OPLEN[s[j]]]))
            j += 4 * OPLEN[s[j]]
        return ops

    def shown(self, a, depth=0, seen=None):
        """Names shown in the match for action a and the actions it hands over to."""
        seen = set() if seen is None else seen
        if a in seen or depth > 2:
            return []
        seen.add(a)
        out = []
        for op, b in self.walk(a):
            if op == 50 and u16(b, 4) < 600:
                out.append(self.exe_at(self.disp[u16(b, 4)]))
            elif op in (15, 19) and 0 < u16(b, 4) < len(self.scripts):
                out += self.shown(u16(b, 4), depth + 1, seen)
        return [s for s in dict.fromkeys(out) if s]


# words per script op (op word included), from the script interpreter's handlers at 0x8C041560
OPLEN = [1, 21, 21, 21, 21, 21, 21, 21, 21, 2, 2, 2, 4, 2, 2, 2, 3, 2, 1, 3, 2, 3, 3, 2, 1, 1, 3, 3, 2, 2, 2,
         2, 1, 2, 1, 2, 2, 1, 3, 1, 4, 2, 2, 2, 1, 1, 1, 2, 2, 1, 2, 1, 1, 1, 1, 2, 2, 3, 4, 2, 2, 2, 2, 1, 1,
         2, 2, 2, 1, 3, 2, 4, 2, 2, 3, 2, 2, 3, 1, 2, 9, 9, 9, 9, 9, 9, 9, 9, 9, 15, 15, 15, 15, 15, 15, 15,
         15, 15]


def build():
    g = Game()
    x = g.x
    gstart = list(x[GROUP_START - B:GROUP_START - B + 8])
    groups = [g.exe_at(g.ptr(GROUP_NAMES, i)) for i in range(5)]
    params = [g.menu(546 + i) for i in range(13)]
    hp_names = [g.menu(832 + i) for i in range(5)]
    moves = {}

    def move(a):
        if not a:
            return 0
        if a not in moves:
            edit = g.menu(1339 + a) if a < 1500 else ''
            t = g.types[a] if a < 1500 else 0
            shown = g.shown(a)
            moves[a] = [' / '.join(shown) or edit, edit, (t - 1) if 1 <= t <= 13 else -1]
        return a

    wrestlers = []
    for w in range(COUNT):
        grp = max(k for k in range(5) if gstart[k] <= w)
        p = x[PARAM - B + 26 * w:PARAM - B + 26 * w + 26]
        row = g.rows[w]
        sheet = []
        for r, (_, _, cols) in enumerate(LAYOUT):
            cells = [move(row[s]) for _, s in cols]
            if any(cells):
                sheet.append([r, cells])
        combos = [[move(a) for a in struct.unpack_from('<2H', x, COMBOS - B + 12 * w + 4 * k)] for k in range(3)]
        unlock = UNLOCK.get(w)
        wrestlers.append(dict(
            id=w, en=g.exe_at(g.ptr(NAMES, w)), jp=x[g.ptr(NAMES, w) - B:x.index(b'\0', g.ptr(NAMES, w) - B)].decode('cp932'),
            short=g.exe_at(g.ptr(SHORT, w)), group=grp, pos=w - gstart[grp],
            **profile(g, w),
            theme=g.menu(469 + w), hp=list(x[HP - B + 5 * w:HP - B + 5 * w + 5]),
            atk=list(p[:13]), dfn=list(p[13:]), combos=combos, sheet=sheet,
            unlock=list(unlock) if unlock else None))
    return dict(groups=groups, params=params, hp=hp_names, states=STATES,
                layout=[[s, r, [c for c, _ in cols]] for s, r, cols in LAYOUT],
                moves={str(k): v for k, v in sorted(moves.items())}, wrestlers=wrestlers)


def main(argv=None):
    argv = paths.configure(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='only report whether the page is up to date')
    ap.add_argument('--json', help='also write the data, indented, to this file')
    args = ap.parse_args(argv)
    data = build()
    if args.json:
        Path(args.json).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    page = paths.DOCS / 'guide' / 'index.html'
    if not page.exists():
        sys.exit(f'{paths.show(page)} missing: the guide page holds the data block')
    ok = pagedata.write(page, data, check=args.check)
    n = sum(1 for w in data['wrestlers'] for _, cells in w['sheet'] for c in cells if c)
    print(f'{len(data["wrestlers"])} wrestlers, {n} moves ({len(data["moves"])} different)'
          + ('' if ok else (' - page out of date' if args.check else ' - page updated')))
    if args.check and not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
