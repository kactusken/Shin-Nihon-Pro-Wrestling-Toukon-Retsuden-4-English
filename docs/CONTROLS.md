# Match controls and moves - Toukon Retsuden 4

How the controls work during a match, read from the game's code (`1ST_READ.BIN`) and data
(`MOTION/ACTTBL.PAC`, `MOTION/NBATTLE.PAC`), with most claims tried in a headless emulator on the
original disc (2026-11-07). It replaces the guesswork in the two community FAQs (CJayC 2000,
elbarto 2001); where they are wrong it says so.

Markings: *seen headless* = driven and observed in the emulator; *from the code* = read in the
disassembly, not run. Addresses are RAM (`0x8C010000` + file offset for the executable).

## Contents
- [Buttons at a glance](#buttons-at-a-glance) · [How a move is chosen](#how-a-move-is-chosen)
- [Every move slot](#every-move-slot) · [Priority](#priority-rock-paper-scissors) · [The X button](#the-x-button)
- [Defence: getting up, kick-outs, escapes](#defence-getting-up-kick-outs-escapes)
- [Taunts, combos, crowd rush](#taunts-critical-combos-crowd-rush) · [Match flow](#match-flow-pause-skip-reset-secret-inputs)
- [FAQ claims checked](#faq-claims-checked) · [Technical reference](#technical-reference) · [Open questions](#open-questions)

## Buttons at a glance

| Input | In a match |
|---|---|
| **A** | Strike. Also: climb the turnbuckle (A + toward the corner, opponent down), dive from the top |
| **B** | Throw (grapple). Lift throws on a downed opponent |
| **Y** | Submission / technical hold |
| **X** | Action: run, Irish whip, pick up, pin (hold), ring/apron/floor moves, weapons, tag |
| **L** | Taunt (appeal) - always |
| **R** | Taunt in a singles match (identical to L); in 3-4 wrestler matches it cycles the target instead |
| **D-pad** | Walk; held with a button it selects the "+ direction" variant of the move |
| **Analog stick** | Only in multi-opponent matches: up / left / right picks an opponent. Not used for walking |
| **Start** | Pause. While paused, **R** skips the match |
| **A+B+X+Y + Start** | Soft reset to the title screen |

- Every direction counts the same: "button + direction" means *any* D-pad direction, read on the
  frame the button is pressed. There are no toward/away/sideways variants for attacks (*seen headless*).
  Directions matter only for X actions (where you run, which rope or barrier).
- Two buttons at once: the game checks B, then A, then Y, then X, then L/R; A+B gives the strike,
  B+Y the throw (*seen headless*).
- The computer opponent uses the same code: the AI writes a virtual pad and goes through the same
  move choice as a human (*seen headless*).

## How a move is chosen

The game never picks a move directly. From the situation and the button it computes a **slot**
(0-599), and the wrestler's move set says which move is in that slot (`0x8C035480`). An empty slot
does nothing. Each built-in wrestler's move set is one row of 600 slots in `MOTION/ACTTBL.PAC`; edit
wrestlers carry the same 600-slot layout in their save record. The Edit mode's Move Setup tree labels
every slot with its input (button, + direction, opponent state), which is where the table below comes
from.

What decides the slot:
- **Where you stand relative to the opponent**: face to face / side, or behind (a 6-sector angle,
  `status+0xC`; "behind" is the 60 degrees at his back for A, the wider back half for B and Y).
- **Distance**: grab range is about 700 units; X whips inside 600 and runs from farther.
- **The opponent's stun (groggy) level**: N normal, S, M, L (`opponent+0x4B`, 0-3). Stun never blocks a
  move: each stun level simply has its own slot. The FAQ "N/S/M/L" columns are this.
- **Whether a direction is held** on the press frame.
- **The situation**: running, opponent running at you, opponent down (face up / down, which part of the
  body you stand at), corner, ropes, apron, floor, top rope, tag partner positions.

Timing: A starts at once. B and Y start a **16-frame lock-up**; the move happens only if the opponent
is still in range and can be grabbed when it ends - otherwise you whiff (*seen headless*).

## Every move slot

Per wrestler, 206 slots take a player input (plus entrance, call and victory poses that play by
themselves). "x4 stun" = one move per opponent stun level N/S/M/L; "+/-dir" = with and without a
direction.

| Situation | Inputs | Moves |
|---|---|---|
| **Close attack** (opponent standing, in front or to the side) | A, B, Y x +/-dir x 4 stun | 24 |
| **Rear attack** (behind the opponent) | A, B, Y x +/-dir x 4 stun | 24 |
| **Dash attack, opponent facing you** (while running) | A, B, Y x 4 stun | 12 |
| **Dash attack, opponent facing away** | A, B, Y x 4 stun | 12 |
| **Dash counter** (opponent runs at you) | A, B, Y | 3 |
| **Whip counter** (opponent coming back off the ropes after your whip) | A, B, Y | 3 |
| **Rope rebound attack** / **Corner rebound attack** | A, B, Y each | 3 + 3 |
| **Corner attack** (opponent groggy in the corner) | A, B, Y | 3 |
| **Corner charge** (running into a cornered opponent; also against the steel barrier) | A | 2 |
| **Get-up attack** (as you get up) | A, B, Y | 3 |
| **Down attack** (opponent down) - head, upper body (left/right), lower body (left/right), legs; face up and face down | A, Y at each position | 24 |
| **Lift throws** (B on a downed opponent: front/back, by face up/down and body half) | B | 4 |
| **Pin** (hold X) - one per body position, face up and face down | X | 12 |
| **Climbing / on the top rope**: attack a climbing or perched opponent (front, back, groggy) | A, B | 5 |
| **Avalanche (superplex) front / back** | B x stun S/M/L | 6 |
| **Top rope to a standing opponent** | A x 4 stun, B and Y at M/L | 8 |
| **Top rope to a downed opponent** (by face up/down, near ropes or corner; Toukon Rush variant) | A | 5 |
| **Top rope to the floor** | A x 4 stun | 4 |
| **Attack to the floor** (opponent outside), at the ropes / from a run-up | A x 4 stun each | 8 |
| **Ring to apron** (opponent on the apron) | A, B, Y | 3 |
| **On the apron**, opponent facing you / away | A, B, Y each | 6 |
| **Apron to ring** / **apron to floor** | A, B, Y / A x 4 stun | 3 + 4 |
| **Full nelson holds** (partner holds the opponent): close, dash, top rope | A | 3 |
| **Double-team attacks** (tag: side by side, front and back, at the corner, flanking a downed opponent) | A, B, Y by position | 13 |
| **Save (cut) attack** (breaking a pin or hold), standing / on the ground | A | 2 |
| **Taunts** | L (R) x +/-dir x opponent normal / groggy-or-down | 4 |
| **Back reversal** (high / low stamina), **kick-catch reversal** | automatic | 4 |

Down attacks: the move depends on the part of the body you stand at - head, upper body or lower body
(either side), legs - read from the slot labels, *from the code*. Face down the body runs the other way,
so the same spot gives the matching face-down slot.

The full move list of every built-in wrestler (hidden ones included) is extracted per slot by
`private/work/moves/extract_moves.py` (not published: it is game data). Example, Shinya Hashimoto's
close attacks (*from the data*):

| | N | S | M | L |
|---|---|---|---|---|
| A | Kesagiri Chop | Thrust Kick | Kesagiri Chop Barrage | Rolling Kesagiri Chop |
| A + dir | Middle Kick | Sweep Kick | High Kick | Heavy Bomb Kick |
| B | High Angle Body Slam | Brainbuster Slam | Harai Goshi | Sinking DDT |
| B + dir | Hip Toss | DDT | Rapid Knees DDT | Vertical Drop DDT |
| Y | Neckbreaker Drop | Neckbreaker Drop | Shoulder Neckbreaker | Shoulder Neckbreaker |
| Y + dir | Headlock | SA/Elbow Combo | Japanese Armbreaker | Wakigatame |

Built-in wrestlers have moves the Edit mode can't assign (267 slot entries outside the editor's lists),
and two slots no editor menu reaches (the kick-catch reversals).

## Priority (rock-paper-scissors)

**Strike (A) beats throw (B), throw beats submission (Y), submission beats strike** - real, and with
no stat or random number in it (*seen headless*, both wrestlers driven frame by frame).

Each moment of a move says which kinds of attack can land on its user (`status+0x17D`: 1 strike,
2 throw, 4 submission). Standing: all three. During the first ~10 frames of a strike you can't be
thrown; during a throw's lock-up you can't be put in a hold; during a hold's lock-up you can't be
struck. Results:

| You | Opponent | Outcome |
|---|---|---|
| A | B, same frame or up to 15 frames earlier | his grab whiffs and he is hit |
| A | Y, up to ~8 frames after your A | he catches the strike at once (no 16-frame wait); 12+ frames into the strike it fails |
| B | Y, either order, up to 15 frames apart | the throw goes through |
| same button | same button | the earlier press wins; on the same frame player 1 wins (processing order) |

## The X button

X is resolved by area (ring, floor, apron, runway), the opponent's state and distance, and whether you
hold a weapon (`0x8C03AB12`). First rule that applies wins.

**Moving** (*seen headless*)
- X: run at the opponent (from 600+ units away). X + direction: run that way. A new X while running
  stops the run (a wrestler sent by a whip can't stop).
- Ring to apron: X + toward the ropes. Press X again during the motion (up to ~58 frames / 1 s) to go
  on to the floor.
- Floor to apron: X + toward the ring. X again between about frames 5 and 20 to go straight in.
- Apron to ring: X + toward the ring. Apron to floor: X + away from it.
- Runway on and off (*from the code*). On top of the turnbuckle: X climbs back down.
- There is no fixed double-tap time: each motion opens its own window for the second X.

**Standing opponent within 600** (whip, *seen headless* for the ropes, the rest *from the code*)
- X: Irish whip into the ropes. With your back near a corner: into the corner. On the floor: into the
  barrier, the ring post or the barrier corner, depending on what you stand next to.
- Your back to the ropes, face to face: throw him over the top rope to the floor.
- On the floor at the ring edge, facing the ring: roll him into the ring. Runway: throw him onto / off it.
- Opponent groggy within 350, X + direction: turn him around (*from the code*).
- 3-4 wrestler matches, behind a groggy opponent: X holds him for your partner.

**Downed opponent** (*seen headless*)
- X: pick him up. **XX**: pick him up facing away.
- **Pin = keep X held** for at least ~17 frames (0.3 s) after the press; let go sooner and it is a pick-up.
  Only on an opponent who is down and hurt; once he is getting up, X just runs.
- X + direction: step over / drag / roll him, chosen by where you stand at the body (*from the code*;
  step-over seen).
- X during the pin did not release it (the FAQs say it does).

**Weapons** (*seen headless* for the chair and bat)
- On the floor: X + toward the crowd barrier takes a **chair** (anywhere along it); X + diagonal toward a
  barrier corner takes a **bat** - **Tatsutoshi Goto and Michiyoshi Ohara get a stick instead**.
- With a weapon: X + away from the ring drops it; X + toward the ring at the ring edge rolls in with it
  (you can fight with it in the ring); other X runs with it.

**Tag matches** (*from the code*)
- Legal man: X + toward your corner with your partner on the apron within reach: **tag**. Without him
  there: leave to your corner's apron.
- Partner on the apron: X + toward the ring enters; X alone reaches out for the tag; L/R taunt.
- On the floor by your corner: X goes to the corner apron.

## Defence: getting up, kick-outs, escapes

Every hit adds to the victim's **damage pool** (`status+0x84`). While it is above zero a downed wrestler
stays down; at zero he gets up (~76 frames). **A pin is kicked out the moment the pool reaches zero; if
the referee reaches 3 first, the pin wins** (*seen headless*: pools of 0-2400 kicked out before 1,
5000 at 2, 10000 lost to the 3-count idle but kicked out at 2 when mashing, 15000 lost even mashing).

The pool drains every frame (`0x8C03E5DC`), faster with mashing. `n` = how many of Up, Down, Left,
Right, X, Y, A, B were *newly pressed* that frame (L, R, Start don't count; a held button counts once):

| Your stamina | Normally | While held or pinned |
|---|---|---|
| over 70 % | 10n + 2 | 16n + 36 |
| 31-70 % | 8n + 2 | 8n + 20 |
| 30 % or less | 4n + 2 | 4n + 8 |

Doubled during your **crowd rush** - which is why the computer almost always kicks out then.

So the best mash is tapping several buttons and directions *together*, repeatedly; low stamina makes
every press worth less. Escaping holds uses the same drain; some holds also run a **mash contest**
comparing both wrestlers' press totals (*from the code*). Rope break: the referee counts to 5 while the
attacker keeps a hold on a wrestler touching the ropes, then the match is decided - probably a
disqualification (*from the code*, not tested).

## Taunts, critical combos, crowd rush

**Taunts** (*seen headless*): L - and R in singles - with no direction / with direction gives taunt 1 / 2
when the opponent is normal, 3 / 4 when he is groggy or down. Each wrestler has 4.

**Critical combos** (*from the code*, pairs *seen headless*): every wrestler has **three** start->finish
pairs (the in-game skill book shows one). When the finish move lands within **12 seconds (720 frames)**
of the start move, with no other move landing in between, "Critical Combo" appears and that hit does
**+25 % damage**. A start can be a taunt. Examples: Hashimoto - taunt 3 -> Vertical Drop DDT, taunt 4
-> Heavy Bomb Kick, Vertical Drop DDT -> Triangle Choke; Liger - taunt 4 -> Thunder Liger Bomb, taunt 4
-> Hanging Powerbomb, taunt 3 -> Running Palm.

**Crowd rush** (Toukon Rush): taking 8 hits in a row without answering while having less stamina than
the opponent starts a 30-second rush - stamina regenerates, damage taken x1.5, the damage pool fills
half as fast and drains twice as fast; some moves have a rush variant. Details in
[TECHNICAL.md](TECHNICAL.md#crowd-rush-comeback-state).

## Match flow: pause, skip, reset, secret inputs

- **Start**: pause ("PAUSE" and "SKIP (R) BUTTON"; there is no pause menu). **R while paused** ends the
  match with a *simulated* result - the same simulation as a computer-vs-computer match - not a forfeit
  (*seen headless*).
- **A+B+X+Y + Start**: soft reset to the title screen (*seen headless*).
- **Referee choice** (at match load, singles): hold both analog sticks of controllers 1 and 2 - both up,
  1 down + 2 up, 1 up + 2 down, 1 right + 2 left, 1 left + 2 right pick five different referees
  (*from the code*; the codes match elbarto's FAQ).
- **Hidden CPU-logic test** (*from the code*): in a computer-vs-computer single match whose first
  wrestler is an edit wrestler, holding L on controller 1 at the match load lets controller 1's A/B/X/Y
  switch a value 0-3 in that wrestler's CPU logic during the match - apparently a developer test of the
  edit mode's thinking patterns.

## FAQ claims checked

| Claim | Verdict |
|---|---|
| Strike > throw > submission > strike (both) | right; faq1's table has the right cycle under garbled labels |
| L = taunt, R = taunt / change target (faq1) vs L appeals 1-4, R appeal / cycle opponents (faq2) | faq2: L always; R taunts in singles, cycles targets in multi-opponent matches |
| "+ D-pad" variants (faq1 columns) | any direction, one variant per button and stun level |
| Stun levels N/S/M/L gate moves | they select a slot; nothing is locked out |
| Analog stick in grapples / fingerlocks (faq2) | not found; the stick only picks opponents in multi-opponent matches |
| Top rope moves: X + toward corner (faq2) | wrong: A + toward the corner climbs; X climbs down |
| Pin = press and hold X | right: hold at least ~0.3 s |
| Release pin = X | not reproduced |
| XX = pick up facing away; ring <-> floor with XX | right; the second-press window differs per motion |
| Mash buttons and D-pad to escape / get up | right; new presses count, several at once count more, low stamina weakens them |
| CPU kicks out during crowd rushes (faq2) | explained: the damage pool drains twice as fast |
| R on pause = skip (forfeit?) (faq2) | skip with a simulated result, not a forfeit |
| Goto / Ohara get a kendo stick instead of the bat (faq2) | right (a separate stick model) |
| Each wrestler has 3 critical combos (faq2) | right |
| Referee codes with two analog sticks (faq2) | right |

## Technical reference

| What | Where |
|---|---|
| `pdGetPeripheral(port)` | `0x8C0F697A`: `0x8C385C30 + port*52` (port 0 = A, 6 = B) |
| Per-player controller object | `wrestler+0x80`, filled by `0x8C059210`: `+0xE` any direction, `+0xF` X, `+0x10` Y, `+0x11` A, `+0x12` B, `+0x13` L, `+0x14` R, `+0x15` Start (pressed this frame), `+0x17..+0x1A` analog stick down/right/up/left (beyond 64), `+0x1B` direction 0-8 (table `0x8C0DD6CC`) |
| Long press (>= 10 frames) | status `+0xF8` X, `+0xF5` Y, `+0xF7` A, `+0xF6` B (`0x8C05955A`) |
| Mash counters | status `+0xA5` new presses this frame, `+0xA6` running total |
| Move resolver | `0x8C035480(handle 0x8C1E0FCC, wrestler, slot)`; chosen slot at `wrestler+0x51A`; built-in sets `MOTION/ACTTBL.PAC` ("ACT2", u16 0x2B, u16 600, 50 rows x 600 u16, row = wrestler id, rows 42-49 unused); edit wrestlers `*(0x8C1E1584) + 0x68 + i*0xAD0` |
| Slot labels and inputs | Edit Move Setup tree `0x8C0E628C` (code & 7: 1 A, 2 B, 3 X, 4 Y, 5 L, 6 auto; & 8: + direction; >> 4: opponent 1 N, 2 S, 3 M, 4 L, 5 any groggy); candidate lists `0x8C0E6414` |
| Standing slots | close A `0xF0`, B `0xF8`, Y `0x100`; rear `0x12E` / `0x136` / `0x13E`; + 2 x stun + direction |
| State machine / handlers | `0x8C03584C`; B `0x8C039524`, A `0x8C03871C`, Y `0x8C039940`, X `0x8C03AB12`, L/R `0x8C03BE58`, running stop `0x8C03BC20` |
| Priority flags | status `+0x17D` (1 strike, 2 throw, 4 submission can land) |
| Moves | 1,794 action scripts in `NBATTLE.PAC` section 1, interpreter `0x8C041530`; damage is in each script (op 40/41 -> `0x8C03E990`), scaled by the 13 attack / defence type ratings (wrestler record `0x8C0D8EEF`, 26 bytes) |
| Critical combos | `0x8C0D8AF8 + id*12` (3 x u16 start, u16 finish), copied to status `+0x72`; check `0x8C03D62A` |
| Damage pool drain | `0x8C03E5DC`; pool status `+0x84` |
| Pause / skip / reset | `0x8C059286` (pause `0x8C1E177E`), skip `0x8C019E94` -> `0x8C016FFC`, reset `0x8C059246` |
| Referee select, L test | `0x8C026684`, `0x8C0267AA` |

Research notes, scripts and savestate recipes: `private/work/moves/` (not published).

## Open questions
- Exact conditions of the back reversals and the kick-catch reversal; which X + direction on a downed
  opponent drags, steps over or rolls him.
- How the stun level rises with damage and wears off.
- What the four damage numbers in a move's hit record mean, and the type-rating multipliers.
- Rope break and tag-match X actions were read in the code but not tried; partner assist rules not traced.
- Whether X can release a pin or hold at all.
