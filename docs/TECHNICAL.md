# How r1 changes the firmware

The patch applies only to the exact Creative SXFI GAMER 2.07.02 image identified
in [VALIDATION.md](VALIDATION.md). Offsets are not portable to other versions.

The stock mute manager combines requests from separate owners. r1 registers
one additional owner for the internal monitoring route (logical input 108).
The native microphone path and native mute handler remain in place. This lets
the USB microphone remain active while the monitoring owner requests mute.
Native OFF still mutes input 108 and output 206.

Only the guarded hardware microphone-button branch changes. Existing busy,
presence and mode routing is retained. The new cycle calls the native guarded
setter and the original voice selector, preserving the original voice files:
`@micunmute → @micunmute → @micmute`, with native report values `9 → 9 → 8`.

## Placement

| Item | Value |
|---|---|
| Reserved area | `0x400d03e0`, 256 bytes |
| Cycle | `0x400d03e0`, 196 bytes Thumb code |
| Trampoline | `0x400d04a4`, 48 bytes |
| State | `0x400d04dc`, 4 bytes |
| Heap pool1 new start | `0x400d04e0` |
| Heap pool1 end | `0x405503e0`, unchanged |
| Hook address | `0x4001a402`, 12 bytes |
| Native guarded setter | `0x4001b214` |
| Native voice selector | `0x4001ac14` |

The firmware gains a 256-byte appended payload. The original heap-start literal
at FMAIN file offset `0x1cd0` moves pool1 start forward by 256 bytes. A formerly
zero-length startup copy entry at `0x4bc` loads the appended payload from
`0x201693d8` to the reserved area. The button hook jumps to the trampoline.

All other original FMAIN bytes are preserved. Original initialized-region
destinations, BSS and stack sizes remain unchanged. CIFF is rebuilt with new
lengths and CHK2. FBOOT and prompts are unchanged. The firmware's version string
is not changed, and power-up initialization remains stock.

`src/cycle.s` is the assembly for the shipped placement. `build_candidate.py`
assembles it, writes the three bounded patches and checks the final known
hashes. The emulator loads the actual resulting image, not an independent
reimplementation of the three states.
