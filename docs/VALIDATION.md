# r1 validation

## Physical test — 2026-10-22 UTC

One Creative SXFI GAMER EF0880, Windows 11, USB connection:

- Entered recovery by holding the RGB lighting button through USB connection
  for about five seconds. HID/CDC interfaces remained; audio interfaces were absent.
- Unplugging/reconnecting without buttons restored normal USB audio operation.
- Flashed the exact r1 CIFF below using the native modified updater with `/F`.
  Its UI reported **“Upgrade is successful.”** The device booted and exposed
  normal playback/recording endpoints afterward.
- The owner independently checked the physical microphone button, listening
  and recordings: first Mic on without sidetone and working recording; second
  Mic on with sidetone and working recording; third Mic off with device mute.
- The original SDK responded after the update with `2.07.02 (81C80082)`.
  This is the stock version string, not a unique identifier for r1.

The release renames the tested updater for clarity; its bytes and SHA-256 are
unchanged. No full installed-flash readback was performed. Other physical
headsets, every mode, prolonged operation, power/reset/unplug lifecycle and
an actual factory rollback have not been validated.

## Offline checks

The included build tool reproduces the exact FMAIN and CIFF hashes below from
the stock updater. `src/verify_candidate.py` executes the final modified image
in Unicorn and checks:

- Actual ARM startup copy and BSS clearing loops.
- All three native heap constructors; pool1 starts beyond the reserved patch.
- 64 real pool1 allocations leave the injected code/state untouched.
- 27 microphone-button presses across internal modes 3, 6 and 7.
- 16 blocked/other-event cases match the stock handler.
- Per-press USB synchronization does not remove the separate sidetone mute owner.
- Native OFF survives a different owner's unmute request.
- External native mute restarts the cycle; allocation failure and invalid state
  follow the tested OFF paths.
- Callee-saved registers and stack are preserved.

Emulation stubs app-mode and disabled-mode getters, the busy result, final audio
backend, event/USB notifications, gain backend and voice queue. The interrupt
mask register is isolated memory; actual IRQ timing is not modeled. Emulation
does not replace the physical tests above or prove every operating condition.

## Binary identity

| Component | SHA-256 |
|---|---|
| Factory updater | `1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496` |
| Factory CIFF | `0ebab178dd4f9aa5b0c3ea975040279df39bd2aec7073bfef55c288bd12c4eb3` |
| Factory FMAIN | `7bcca20699b7bfe746923fd1791a4cc36a5021f0389ae9ce65c56dfd78bec761` |
| r1 FMAIN | `4ae6e3b6f4e14d310f6dedafe3293c48a6658137f757fd1b1999ce3ec160b05b` |
| r1 CIFF | `0af6cbe38b9302db1d614374ff20339f556b1cbdf443712bf1082a3350867887` |
| Ready r1 updater | `82d96a46f4e43233f0a983ecd06ba10ee73612c46d30afc5a9061c5e60ac6adb` |

The native updater's `.text` section and every resource except
`RCDATA(10)/CUDSP600_RDCATA/1033` are byte-identical to the factory EXE. The obsolete
Authenticode signature is removed from the modified EXE and its PE checksum is
valid. FBOOT, voice prompts and the other CIFF chunks are unchanged. CIFF lengths
and CHK2 SHA-256 are rebuilt and verified.
