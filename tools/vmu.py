#!/usr/bin/env python3
"""Dreamcast memory card (VMU) images: list, extract and add files, standard library only.

  vmu.py list CARD...                 the files on each card
  vmu.py extract CARD OUTDIR          every file -> OUTDIR/<name>
  vmu.py add CARD NAME FILE [OUT]     add FILE as NAME (a data file), to OUT or CARD itself

An image is 128 KB: 256 blocks of 512 bytes, as Flycast keeps them (vmu_save_A1.bin). Start a test
card from a blank one: `emu.py run <cue> --card A1=blank.bin` makes it, formatted (docs/PLATFORM.md).

Root block 255: FAT block (u16 at 0x46), FAT size (0x48), directory block (0x4A), its size (0x4C).
Directory blocks run downwards from there. Each entry is 32 bytes: type (0x33 data, 0xCC game), copy
flag, first block u16, name 12, time 8 (BCD), size in blocks u16, header offset in blocks u16. The
FAT chains the blocks: 0xFFFA ends a file, 0xFFFC is a free block.

A game checks a data file's own VMS header too: after changing one, set_crc(data, length), with
length the bytes the CRC covers (header + payload: the game's save format says how many).

As a library: files(card_bytes) -> [Entry], add_file(card_bytes, name, data) -> new card bytes.
"""
import argparse
import datetime
import struct
import sys
from collections import namedtuple
from pathlib import Path

BLOCK = 512
CARD_SIZE = 256 * BLOCK
USER_BLOCKS = 200           # the blocks a file can use; the rest is the system area
ROOT = 255
DATA, GAME = 0x33, 0xCC
FREE, LAST = 0xFFFC, 0xFFFA

Entry = namedtuple('Entry', 'name kind blocks header data time')


def _layout(card):
    if len(card) != CARD_SIZE:
        sys.exit(f'a VMU image is {CARD_SIZE} bytes, this one {len(card)}: not a card image?')
    return struct.unpack_from('<HHHH', card, ROOT * BLOCK + 0x46)      # FAT block, size, directory block, size


def _fat(card, fat_block):
    return list(struct.unpack_from('<256H', card, fat_block * BLOCK))


def files(card):
    """The files of a card image (bytes)."""
    fat_block, _, dir_block, dir_blocks = _layout(card)
    fat = _fat(card, fat_block)
    out = []
    for k in range(dir_blocks):
        at = (dir_block - k) * BLOCK
        for e in range(at, at + BLOCK, 32):
            kind, first = card[e], struct.unpack_from('<H', card, e + 2)[0]
            if kind not in (DATA, GAME):
                continue
            size, header = struct.unpack_from('<HH', card, e + 0x18)
            data, b = bytearray(), first
            for _ in range(size):
                data += card[b * BLOCK:(b + 1) * BLOCK]
                b = fat[b]
            out.append(Entry(card[e + 4:e + 16].decode('ascii', 'replace').strip(' \0'), kind, size, header,
                             bytes(data), card[e + 16:e + 24].hex()))
    return out


def add_file(card, name, data, when=None):
    """`card` with a new data file, its blocks taken from the top down as the BIOS does."""
    card = bytearray(card)
    fat_block, _, dir_block, dir_blocks = _layout(card)
    if name in [f.name for f in files(card)]:
        sys.exit(f'{name} is already on the card')
    fat = _fat(card, fat_block)
    count = (len(data) + BLOCK - 1) // BLOCK
    free = [b for b in range(USER_BLOCKS - 1, -1, -1) if fat[b] == FREE][:count]
    if len(free) < count:
        sys.exit(f'card full: {name} needs {count} blocks, {len(free)} are free')
    for at in range(dir_blocks):
        block = (dir_block - at) * BLOCK
        entry = next((e for e in range(block, block + BLOCK, 32) if card[e] == 0), None)
        if entry is not None:
            break
    else:
        sys.exit('the card directory is full')
    for i, b in enumerate(free):
        fat[b] = free[i + 1] if i + 1 < count else LAST
        card[b * BLOCK:(b + 1) * BLOCK] = data[i * BLOCK:(i + 1) * BLOCK].ljust(BLOCK, b'\0')
    struct.pack_into('<256H', card, fat_block * BLOCK, *fat)
    t = when or datetime.datetime.now()
    time = bytes.fromhex(t.strftime('%Y%m%d%H%M%S') + f'{t.weekday():02d}')
    card[entry:entry + 32] = struct.pack('<BBH12s8sHH4x', DATA, 0, free[0], name.encode('ascii').ljust(12, b'\0'),
                                         time, count, 0)
    return bytes(card)


def crc16(data):
    """The VMS file CRC (CCITT, initial value 0)."""
    n = 0
    for c in data:
        n ^= c << 8
        for _ in range(8):
            n = ((n << 1) ^ 0x1021 if n & 0x8000 else n << 1) & 0xFFFF
    return n


def set_crc(data, length):
    """`data` with the CRC at 0x46 of its VMS header set, computed over `length` bytes with it zeroed."""
    data = bytearray(data)
    struct.pack_into('<H', data, 0x46, 0)
    struct.pack_into('<H', data, 0x46, crc16(data[:length]))
    return bytes(data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('list')
    p.add_argument('cards', nargs='+', type=Path)
    p = sub.add_parser('extract')
    p.add_argument('card', type=Path)
    p.add_argument('outdir', type=Path)
    p = sub.add_parser('add')
    p.add_argument('card', type=Path)
    p.add_argument('name')
    p.add_argument('file', type=Path)
    p.add_argument('out', nargs='?', type=Path)
    a = ap.parse_args(argv)
    if a.cmd == 'list':
        for card in a.cards:
            for f in files(card.read_bytes()):
                print(f'{card.name:18} {f.name:12} {"data" if f.kind == DATA else "game"} {f.blocks:3} blk  {f.time}')
    elif a.cmd == 'extract':
        a.outdir.mkdir(parents=True, exist_ok=True)
        for f in files(a.card.read_bytes()):
            (a.outdir / f.name).write_bytes(f.data)
            print(f'{a.outdir / f.name}: {len(f.data)} bytes')
    else:
        (a.out or a.card).write_bytes(add_file(a.card.read_bytes(), a.name, a.file.read_bytes()))


if __name__ == '__main__':
    main()
