#!/usr/bin/env python3
"""Build the translated image from the original. Standard library only.

  python3 build.py [--name NAME] [--unlocks all|none|GROUP,...] [--clean]
      -> build/NAME.<ext> (default NAME: "<game> (English)")

Steps (default folders shown; move any of them with the folder options - see --help):
  1. verify the original in rom/ (size + SHA-1; --skip-verify skips the hash)
  2. prepare build/NAME: a fresh copy of the original, or - much faster for big images - the last
     build with every range it wrote restored from the original (tools/image.py; --clean copies)
  3. text: translation/script/ and translation/text/ into the game's files (TEXT_STEPS)
  4. code patches picked by --unlocks (CODE_PATCHES, tools/codepatch.py; debug-* groups only when named)
  5. images: for every catalogued image the English file the catalogue picks (hand-made >
     approved > rendered), imported by tools/gfx.py; the final set is copied to review/images-english/
  6. write every changed file back into the image (files that fit in place first)

Two name sets (e.g. real wrestlers' names and the game's parody names, two releases): fill
NAME_SETS; --names picks one (default the first) and text steps read NAMES. Names are written as
tokens in translation/ (`<Name>`) that the project's names tool resolves per set (Fire Pro
Wrestling S tools/names.py, D tools/fpdtext.py); lint's NAME_TOKEN checks them.

Test builds: --boot PART starts the game straight in PART (BOOT_PATCHES, once known);
--no-translation skips text and images, and gameplay patches unless --unlocks is given - on its
own the result is byte-identical to the original (tools/check.py --control proves it).
Developer flags (never for releases): --no-text FILE skips one text file.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
import catalog  # noqa: E402
import codepatch  # noqa: E402
import disc  # noqa: E402
import gfx  # noqa: E402
import image  # noqa: E402
import nameentry  # noqa: E402
import paths  # noqa: E402

# Gameplay patches: (group, file, address, original, new, description) - see tools/codepatch.py.
# Groups named debug-* are developer extras (debug menus, cheat windows): never in "all" or the
# default, only when named, never in a release variant. An extra the owner wants to release (say a
# restored debug menu as its own patch) gets another group name, e.g. dev-menu, and a make_patches
# VARIANT, with DEFAULT_GROUPS = set() to keep it out of the main patch.
CODE_PATCHES = [
    # Edit > Parameter rows: the Japanese values are full-width digits ([３] = 4 cells), the English
    # ones half-width - one space inside the brackets keeps both columns under their headings and the cursor
    ('layout', '/1ST_READ.BIN', 0x8C0CFA48, b'%s   [%s]   [%s]\0\0\0\0', b'%s   [ %s]   [ %s]\0\0',
     'Edit parameter rows: values under Attack/Defense'),
    # The lock test 0x8C06C9D2 (wrestler id in r5) returns 1 for the seven hidden wrestlers (ids 15-19,
    # 31, 41) while their bit in the system save's unlock word is clear: return 0 at once. The save
    # is not written (docs/HIDDEN_CONTENT.md, docs/PATCHES.md)
    ('unlock-wrestlers', '/1ST_READ.BIN', 0x8C06C9D2, bytes.fromhex('2dd700e6'), bytes.fromhex('0b0000e0'),
     'Hidden wrestlers: every wrestler selectable (rts; mov #0,r0)'),
    # The Sapporo venue (arena BGM index 7) plays BGM entry 69, whose files are yokohamal/r.p04 (played nowhere
    # else); the disc's own SAPPOROL/R.P04 are unused. Point entry 69's names at them and set its length field
    # (samples = 2 x one file's bytes, as the other arena entries)
    ('sapporo-music', '/1ST_READ.BIN', 0x8C0CDE18, b'yokohamal.p04\0\0\0', b'sapporol.p04\0\0\0\0',
     'Sapporo venue music: BGM entry 69 left file'),
    ('sapporo-music', '/1ST_READ.BIN', 0x8C0CDE28, b'yokohamar.p04\0\0\0', b'sapporor.p04\0\0\0\0',
     'Sapporo venue music: BGM entry 69 right file'),
    ('sapporo-music', '/1ST_READ.BIN', 0x8C0DB248, bytes.fromhex('804a6400'), bytes.fromhex('c09d5f00'),
     'Sapporo venue music: length 6266304 samples'),
    # Edit Theme 8: BGM entry 49 (edit8nl/r.p04, not on the disc) plays the unused EDIT7NL/R.P04; the Edit
    # entrance-theme list offers 8 edit themes instead of 7 (0x8C08B894 add #7,r7); the list callbacks at
    # 0x8C08B92E-0x8C08B965 are repacked to make room for theme_label (0x8C08B950: theme 49 -> MENU STRINGS
    # 3141, which EDIT_THEME8_LABEL adds; others 469 + theme), also called by the settings row (0x8C08AC02).
    # Source (tools/sh4.py asm at 0x8C08B92E, pool words of the original):
    #   select:  sts.l pr,@-r15; mov.l @(P_SAVE),r3; mov.l @(P_C312),r2; mov.l @(48,r4),r5; jsr @r2; mov.l @r3,r4
    #            mov.l @(P_THEME),r1; mov.w r0,@r1; lds.l @r15+,pr; rts; mov #0,r0
    #   label:   sts.l pr,@-r15; mov.l @(P_C312),r2; mov.l @(P_SAVE),r3; jsr @r2; mov.l @r3,r4; lds.l @r15+,pr
    #   theme_label: mov.l @(P_GETSTR),r3; mov.w @(P_1D5),r4; cmp/eq #49,r0; bf normal; mov.w @(x8),r4
    #   normal:  jmp @r3; add r0,r4
    #   x8: .word 3092; nop; nop; nop
    #   P_SAVE 0x8C08B994, P_C312 0x8C08B9B4, P_THEME 0x8C08B9B8, P_GETSTR 0x8C08B9BC, P_1D5 0x8C08B990 (= 469)
    ('edit-theme8', '/1ST_READ.BIN', 0x8C0CDB9C, b'8', b'7', 'Edit Theme 8: BGM entry 49 left = edit7nl.p04'),
    ('edit-theme8', '/1ST_READ.BIN', 0x8C0CDBA8, b'8', b'7', 'Edit Theme 8: BGM entry 49 right = edit7nr.p04'),
    ('edit-theme8', '/1ST_READ.BIN', 0x8C08B894, bytes.fromhex('0777'), bytes.fromhex('0877'),
     'Edit Theme 8: theme list count +8 edit themes'),
    ('edit-theme8', '/1ST_READ.BIN', 0x8C08B92E,
     bytes.fromhex('224ffc7f436517d31fd2422f5c550b4232641dd10121047f264f0b0000e0224ffc7f18d210d3522f0b42326419940c34047f16d32b43264f'),
     bytes.fromhex('224f18d320d24c550b4232641fd10121264f0b0000e0224f1bd212d30b423264264f1ad31d943188008b01942b430c34140c090009000900'),
     'Edit Theme 8: theme list callbacks and theme_label'),
    ('edit-theme8', '/1ST_READ.BIN', 0x8C0EF3E8, bytes.fromhex('4cb9088c'), bytes.fromhex('44b9088c'),
     'Edit Theme 8: list vtable label callback'),
    ('edit-theme8', '/1ST_READ.BIN', 0x8C08AC02, bytes.fromhex('5c93ed040b4c3c34'), bytes.fromhex('ed00a4b609000900'),
     'Edit Theme 8: settings row label via theme_label'),
]
EDIT_THEME8_LABEL = (3141, 'Edit Theme 8', 'エディットのテーマ８')  # MENU STRINGS entry (unused in the original), English, Japanese
ALWAYS_GROUPS = {'layout'}              # in every translated build, not a choice (--unlocks ignores them): the English's own fixes
UNLOCK_GROUPS = sorted({p[0] for p in CODE_PATCHES} - ALWAYS_GROUPS)
PLAYER_GROUPS = [g for g in UNLOCK_GROUPS if not g.startswith('debug-')]
DEFAULT_GROUPS = set()  # without --unlocks; the extras are opt-in (owner decides how they ship)

# --boot: (part, file, address, original, new) - patches that start the game in a given part.
BOOT_PATCHES = {
}


def to_offset(name, addr):
    """GAME-SPECIFIC: file offset of a RAM address in file `name` (overlay base, ELF segments, ...)."""
    if name == '/1ST_READ.BIN':
        return addr - 0x8C010000
    raise SystemExit(f'build.py to_offset(): no address mapping for {name} yet')


# Text steps: (text file or folder under translation/, function(path, files)). Each inserts the
# English into the game's files through `files` and stops with a clear message if anything doesn't fit.
# Zero-padding files a grown file may take room from when the disc is full (PS2 disc.py
# take_from_padding: their end is cut off) - e.g. ['/DUMMY.DAT']; check they are all zeros.
PADDING_DONORS = []

# Name sets for the --names option, e.g. ('real', 'parody') - empty: one set, no option.
NAME_SETS = ()
NAMES = NAME_SETS[0] if NAME_SETS else None

import gametext  # noqa: E402
import records  # noqa: E402

TEXT_STEPS = [
    ('text/strings.txt', gametext.strings_step_for('menu')),
    ('text/edit_strings.txt', gametext.strings_step_for('edit')),
    ('text/exe.txt', gametext.exe_step),
    ('text/champions.csv', records.step),         # champion histories in 1ST_READ.BIN (fixed records)
]


class Files:
    """The game's files for this build: read from the image on first use, written back at the end."""

    def __init__(self, d):
        self.d, self.data, self.changed = d, {}, set()

    def get(self, name):
        if name not in self.data:
            self.data[name] = bytearray(self.d.read_file(self.d.find(name)))
        return self.data[name]

    def put(self, name, data):
        self.data[name] = bytearray(data)
        self.changed.add(name)


def unlock_groups(value):
    if value == 'all':
        return set(PLAYER_GROUPS)
    if value == 'none':
        return set()
    groups = {g.strip() for g in value.split(',') if g.strip()}
    if groups - set(UNLOCK_GROUPS):
        raise argparse.ArgumentTypeError(f'expected all, none or some of {",".join(UNLOCK_GROUPS) or "(no groups yet)"}')
    return groups


def images_step(files):
    final = catalog.final_images()
    missing, changed, _ = catalog.stale()
    if missing or changed:
        print(f'note: {len(missing) + len(changed)} automatic renders are out of date - run tools/render.py '
              f'(building with the frozen files there are)')
    n = gfx.import_images({k: p for k, (tag, p) in final.items()}, files)
    if paths.ENGLISH_IMAGES.exists():
        shutil.rmtree(paths.ENGLISH_IMAGES)
    if final:
        paths.ENGLISH_IMAGES.mkdir(parents=True)
        for name, (tag, p) in final.items():
            dst = paths.ENGLISH_IMAGES / f'{name}.png'
            dst.parent.mkdir(parents=True, exist_ok=True)      # ids can be archive paths
            shutil.copyfile(p, dst)
        counts = {}
        for tag, _ in final.values():
            counts[tag] = counts.get(tag, 0) + 1
        print(f'images: {n} imported (' + ', '.join(f'{c} {t}' for t, c in sorted(counts.items())) + ')')


def verify_original(original):
    """SHA-1 of the original image, once: the result is remembered with the file's size and
    modification time (build/original.verified), so later builds only re-hash a changed file
    (a DVD image takes ~20 s to hash)."""
    st = original.stat()
    stamp = f'{original.resolve()} {st.st_size} {st.st_mtime_ns} {paths.ORIGINAL["sha1"]}'
    memo = paths.BUILD / 'original.verified'
    if memo.exists() and memo.read_text() == stamp:
        return
    print('verifying the original...')
    if image.sha1(original) != paths.ORIGINAL['sha1']:
        sys.exit(f'{original.name} does not match the expected SHA-1 {paths.ORIGINAL["sha1"]}')
    paths.BUILD.mkdir(parents=True, exist_ok=True)
    memo.write_text(stamp)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', default=f'{paths.GAME_FILE} (English)')
    ap.add_argument('--skip-verify', action='store_true', help="don't hash the original image")
    ap.add_argument('--clean', action='store_true', help='copy the original instead of restoring the last build')
    ap.add_argument('--no-translation', action='store_true', help='skip text and images (alone: identical to the original)')
    ap.add_argument('--unlocks', type=unlock_groups, metavar='all|none|GROUP,...',
                    help='gameplay patches: all (debug-* groups only when named), none or some groups (default: DEFAULT_GROUPS); '
                         'none with --no-translation')
    if NAME_SETS:
        ap.add_argument('--names', choices=NAME_SETS, default=NAME_SETS[0],
                        help=f'name set: {" or ".join(NAME_SETS)} (default {NAME_SETS[0]})')
    ap.add_argument('--boot', choices=sorted(BOOT_PATCHES), help='TEST BUILD: start the game in this part')
    ap.add_argument('--no-text', action='append', default=[], metavar='FILE',
                    help='developer: leave this text file untranslated (repeatable)')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    global NAMES
    NAMES = getattr(args, 'names', NAMES)
    if args.unlocks is None:
        args.unlocks = set() if args.no_translation else set(DEFAULT_GROUPS)

    original = paths.ROM
    if not original.exists():
        sys.exit(f'put the original image in {paths.show(paths.ROM_DIR)} (or pass --rom): {paths.ORIGINAL_NAME}')
    if original.stat().st_size != paths.ORIGINAL['size']:
        sys.exit(f'{original.name}: {original.stat().st_size} bytes, expected {paths.ORIGINAL["size"]} - not the right image')
    if not args.skip_verify:
        verify_original(original)

    out = paths.BUILD / (args.name + original.suffix)
    with image.prepare(original, out, clean=args.clean) as f:
        d = disc.Disc(f, writable=True)
        files = Files(d)

        if not args.no_translation:
            for rel, step in TEXT_STEPS:
                if rel in args.no_text:
                    print(f'text: skipped {rel} (--no-text)')
                    continue
                step(paths.TRANSLATION / rel, files)

        if not args.no_translation:  # the English's own fix: names of up to 16 letters (tools/nameentry.py)
            exe = files.get(nameentry.FILE)
            codepatch.apply(files, nameentry.patches(lambda a, n: bytes(exe[to_offset(nameentry.FILE, a):][:n])),
                            {nameentry.GROUP}, to_offset)
        codepatch.apply(files, CODE_PATCHES, set(args.unlocks) | (set() if args.no_translation else ALWAYS_GROUPS), to_offset)
        if 'edit-theme8' in args.unlocks:  # its label: a new MENU/STRINGS.PAC entry
            i, en, jp = EDIT_THEME8_LABEL
            t = gametext.TABLES['menu']
            entries = gametext.read_strings(files.get(t.disc_path), t.size)
            if entries[i] is not None:
                sys.exit(f'edit-theme8: MENU/STRINGS.PAC entry {i} is in use - pick a free one (and the x8 word in CODE_PATCHES)')
            entries[i] = jp.encode('cp932') if args.no_translation else en.encode('ascii')
            files.put(t.disc_path, gametext.build_strings(entries))
            print(f'edit-theme8: MENU/STRINGS.PAC entry {i} = {en if not args.no_translation else jp}')

        if not args.no_translation:
            images_step(files)

        if args.boot:
            codepatch.apply(files, [(args.boot, *p, f'TEST BUILD: boots into {args.boot}') for p in BOOT_PATCHES[args.boot]],
                            {args.boot}, to_offset)

        def fits(name):
            return (len(files.data[name]) + disc.SECTOR - 1) // disc.SECTOR <= d.allocated_sectors(d.find(name))
        for name in sorted(files.changed, key=lambda n: (not fits(n), n)):  # fixed order: same disc layout every build
            d.write_file(d.find(name), bytes(files.data[name]), relocate=True,
                         **({'donors': PADDING_DONORS} if PADDING_DONORS else {}))
            print(f'patched {name}')
    disc.companion_files(out, original)
    print(f'done: {paths.show(out)}  ({len(files.changed)} files patched)')
    return out


if __name__ == '__main__':
    main()
