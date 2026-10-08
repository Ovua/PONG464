# PONG 464

### A tiny Pong game for the Amstrad CPC 464 — Z80 Assembly + Locomotive BASIC 1.0

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Amstrad_CPC464.jpg" alt="Amstrad CPC 464 with monitor" width="700">
</p>

<p align="center">
  <sub>Photo by <a href="https://commons.wikimedia.org/wiki/File:Amstrad_CPC464.jpg">Bill Bertram</a> — CC BY-SA 2.5</sub>
</p>

# Back to where it all started

The **Amstrad CPC 464 was the first computer I ever programmed on. I was 7 years old.**

I remember experimenting with BASIC and being amazed that a few lines of code could make something happen on the screen. I didn't know much about CPUs, memory maps or machine code at the time. I just knew I wanted to understand how it worked.

Years later, I wanted to revisit the computer that introduced me to programming — this time with the knowledge I've gained since then.

**PONG 464 started with a simple idea:** write a classic Pong game for the original CPC 464, using its own Locomotive BASIC and Z80 Assembly. No modern engine, no upgraded CPU, and no extra RAM. Just a small game built around the limitations of a real 1980s home computer.

**This project is a work in progress.** I'm continuing to work on the game logic, rendering, input handling and testing. Part of the fun is studying the hardware again and discovering what can be done with so little.

For me, this is more than a Pong clone. It's a return to where my journey into programming began.

## The computer behind the game

The **Amstrad CPC 464**, released in **1984**, was an 8-bit home computer with an integrated cassette recorder and a built-in BASIC interpreter.

|Component|Original CPC 464|
|-|-|
|CPU|Zilog Z80A, nominally 4 MHz|
|RAM|64 KB|
|Built-in ROM|32 KB (16 KB firmware + 16 KB Locomotive BASIC 1.0)|
|Video|6845-compatible CRTC and Amstrad Gate Array|
|Sound|AY-3-8912 programmable sound generator (three tone channels)|
|Storage|Integrated cassette deck|
|Available video modes|MODE 0: 160 × 200 / 16 colors; MODE 1: 320 × 200 / 4 colors; MODE 2: 640 × 200 / 2 colors|
|Game display mode|MODE 1|

### A quick look at the Z80 CPU

The **Zilog Z80A** is an 8-bit processor with an 8-bit data bus and 16-bit address bus, giving it a **64 KB address space**. Its registers, jumps, arithmetic instructions and direct memory access make it a great machine for learning what software does at a low level.

The nominal 4 MHz clock doesn't mean the CPU performs four million instructions per second: different Z80 instructions take different numbers of cycles, and the CPC's video/memory timing also affects execution. That makes small, efficient routines especially valuable.

### ROM, firmware and EPROM

The CPC 464 normally boots straight into **Locomotive BASIC 1.0** because the system software is stored in ROM rather than loaded from cassette. Its **32 KB of built-in ROM** are logically split into two 16 KB regions:

* **Lower ROM:** system firmware, including low-level services for input, video and other hardware.
* **Upper ROM:** the Locomotive BASIC interpreter.

The CPC uses **ROM/RAM banking** so those ROM regions can be mapped into the Z80's address space while RAM remains available underneath. Depending on the motherboard revision, the two logical banks can live in a single physical 32 KB ROM chip.

An **EPROM** (*Erasable Programmable Read-Only Memory*) is a programmable chip that can hold firmware or software persistently; traditional UV-erasable EPROMs can be erased and programmed again with suitable equipment. Custom ROM software is possible on CPC systems using compatible expansion hardware or carefully designed hardware modifications. The original CPC 464 does **not** need an EPROM replacement to run this game.

**PONG 464 runs from RAM.** The BASIC loader copies its Z80 machine code to `&9000` and calls it directly. No ROM flashing, soldering or hardware modification is involved.

## What the game does

A one-player Pong match against the computer:

* You control the **left paddle**; the CPC controls the **right paddle**.
* Keep the ball in play and try to get it past the computer's paddle.
* The ball bounces off the upper/lower playfield limits and the paddles.
* BASIC keeps track of both scores; **first to 5 points wins**.
* A short sound is played after a point.
* The game offers a replay prompt after a completed match.

### Controls

|Key|Action|
|-|-|
|`Q` or `↑`|Move up|
|`A` or `↓`|Move down|
|`ESC`|Exit|

The AI follows the ball with a deliberately limited update rate. The point is to make a compact, playable example rather than an unbeatable opponent.

## How to run it

### Option 1: CPC 464 emulator

1. Open **`PONG464.BAS`** in a text editor on your PC.
2. Start an Amstrad CPC 464 emulator with Locomotive BASIC 1.0.
3. Import or paste the **entire numbered BASIC listing**, using your emulator's supported text-entry feature.
4. At the BASIC prompt, enter:

```basic
RUN
```

The BASIC program reserves RAM, sets `MODE 1`, writes the machine-code bytes from `DATA` statements into memory at `&9000`, checks their checksum, and starts the game.

**Important:** `PONG464.BAS` is a **plain-text BASIC listing**. It is **not** a tokenized CPC BASIC file, a `.CDT` cassette image or a `.DSK` disk image. Pasting a text file into an emulator only works if that emulator supports the appropriate import/keyboard-injection mechanism.

### Option 2: original CPC 464 hardware

On a real CPC 464, the numbered listing must be **typed in** or transferred using a compatible interface/tool. You can also convert the program to a CPC-compatible cassette format with a suitable external utility.

Do **not** expect `RUN"PONG464.BAS"` to read the plain-text file from a cassette that has not been created. Once the BASIC listing is actually loaded into the computer, enter `RUN`.

No additional memory or custom ROM is required by the design.

## How the code is organized

The game intentionally divides the work between BASIC and Assembly.

**Locomotive BASIC** handles initialization, loading the machine code, displaying the score, detecting the result of each rally, and restarting play. The loader includes all 475 machine-code bytes as decimal `DATA` values.

**Z80 Assembly** handles the active game loop: waiting for a screen frame, reading keys, moving the player and CPU paddles, updating the ball, checking collisions and drawing objects directly into video RAM.

```text
Locomotive BASIC 1.0
  |
  +-- MEMORY &8FFF           Reserve the code area
  +-- MODE 1 / palette       Prepare the display
  +-- DATA -> POKE &9000     Load 475 bytes of machine code
  +-- CALL &9000             Run one rally
  |     |
  |     +-- &BD19            Wait for frame flyback
  |     +-- &BB1E            Test key state
  |     +-- Update paddles / ball / collisions
  |     +-- Draw to RAM at &C000
  |     +-- Return a result code
  |
  +-- PEEK &91D9             Read rally result
  +-- Update scoreboard
  +-- Repeat or show winner
```

### Addresses worth knowing

|Address|Purpose|
|-|-|
|`&9000`|Start of the Z80 program (`START`)|
|`&91D9`|Result byte read by BASIC (`RESULT`)|
|`&C000`|Standard MODE 1 screen RAM base used by the drawing routines|
|`&BD19`|CPC firmware: wait for frame flyback|
|`&BB1E`|CPC firmware: test whether a key is pressed|

The Assembly routine returns these values via the result byte: `1` = player scores, `2` = computer scores, `3` = ESC/exit. After a point, BASIC updates the score and starts another rally.

### Drawing directly to video RAM

The CPC screen is not a simple linear pixel array. In the normal 16 KB layout, screen data is **interleaved by scanline**. For the game's MODE 1 layout:

* A full 320-pixel scanline occupies **80 bytes**.
* One character row contains **8 scanlines**.
* Corresponding scanlines in successive character rows are separated by **80 bytes**, while moving to the next scanline within a character row involves an offset of `&0800`.
* The code draws small, solid blocks for the paddles and ball rather than using BASIC drawing instructions every frame.

The engine calls the firmware routine at `&BD19` for frame synchronization and performs a game-logic update approximately every third flyback (about **16.7 updates per second** on a 50 Hz CPC).

## Repository contents

```text
PONG464/
├── README.md          This documentation
├── PONG464.BAS        Full BASIC listing and machine-code DATA loader
├── PONG464.ASM        Z80 Assembly source (origin &9000)
├── PONG464.BIN        Raw 475-byte machine-code image
└── PONG464.MAP        Symbol/address map for debugging
```

`PONG464.BIN` is a **raw binary**, not a standalone bootable cassette or disk image. `PONG464.MAP` provides label addresses useful when studying the Assembly or debugging machine code.

## Working with the Assembly source

`PONG464.ASM` contains the editable Z80 source, while `PONG464.BIN` is the current assembled machine-code image. The BASIC listing (`PONG464.BAS`) embeds the machine-code bytes in `DATA` statements.

To modify the engine, use a compatible Z80 assembler with the code assembled at `&9000`. After assembling, the updated machine-code bytes and checksum must also be reflected in the BASIC loader.

## Development status and testing

**Status: work in progress — successfully tested on an original Amstrad CPC 464.**

The current build has been generated from the source. Previous project checks included relative-branch validation, BASIC loader checksum verification and instruction-level simulation of selected scoring/exit paths.

**The game has now been run successfully on an original Amstrad CPC 464.** This confirms that the current version runs on real hardware. Further testing is still valuable as development continues.

### Stress testing and hardware safety

Beyond the basic compatibility check, **extensive stress tests and hardware-level checks have been carried out on the original CPC 464**. These included monitoring operating temperatures and observing the machine's overall stability during testing, with the goal of identifying abnormal behavior or signs of overheating.

The aim is to maintain a careful, controlled testing process and minimize potential risks to the original hardware. Temperature monitoring is a hardware-level check, not a feature or reading provided by the game itself. These tests provide additional confidence, but they do not guarantee that every possible hardware issue has been ruled out.

Areas for further testing and refinement include keyboard behavior, rendering, collision edge cases, AI difficulty, timing, scoring, sound and returning cleanly to BASIC.

### Ideas for later

* A two-player mode and adjustable AI difficulty.
* Joystick support.
* Improved ball deflection and speed progression.
* Better sound and a more polished title screen.
* A ready-to-load cassette image (`.CDT`).
* Further memory/performance optimization.

These are **possible improvements**, not finished features.

## Why build this?

Modern machines make it easy to forget how much software developers achieved with a few kilobytes of RAM and a modest 8-bit CPU. Working with the CPC forces me to think about memory layout, instruction costs, firmware calls and the boundary between software and hardware.

The original idea is deliberately simple. That's what makes it fun: build something small, understand every part of it, then improve it step by step.

And, most importantly, get to write code again for the first computer I ever used to program.

## Credits, references and usage

* **Code/project:** Copyright © 2026. Educational example; free to use and modify, as noted in the original distribution. A formal license file has not yet been added.
* **Header photograph:** [Bill Bertram / Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Amstrad_CPC464.jpg), [CC BY-SA 2.5](https://creativecommons.org/licenses/by-sa/2.5/). Photo unchanged.
* **Hardware and firmware references:** [CPCWiki](https://www.cpcwiki.eu/index.php/CPC), [CPC hardware revisions](https://cpctech.cpcwiki.de/docs/cpcrev.html), [Amstrad CPC firmware guide](https://cpctech.cpcwiki.de/docs/manual/s158se01.pdf).

---

*PONG 464 — back to where it all started.*

