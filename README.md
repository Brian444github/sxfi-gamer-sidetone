# Creative SXFI GAMER: optional sidetone

**Keep your microphone working without hearing yourself in the headset.**
Unofficial firmware modification for **Creative SXFI GAMER EF0880**, based on
firmware **2.07.02**. The microphone button cycles through three states:

| Press | Voice prompt | Microphone | Sidetone / self-monitoring |
|---|---|---|---|
| 1 | Mic on | On | Off |
| 2 | Mic on | On | On |
| 3 | Mic off | Muted by the headset | Off |

The cycle then repeats. At power-up, the factory initial behavior is retained;
the first eligible microphone-button press selects **mic on / sidetone off**.
The selected state is not saved across power cycles.

**[Download the ready Windows package](https://github.com/Brian444github/sxfi-gamer-sidetone/releases/download/v2.07.02-three-state-r1/SXFI_GAMER_2.07.02_three-state-r1_Windows.zip)**

No Python, compiler or separate factory-firmware download is needed to install.
Use the release ZIP above; GitHub's **Code → Download ZIP** contains source code.

**[Русская инструкция и описание →](README.ru.md)**

## Install

1. Confirm the headset label says **SXFI GAMER / EF0880**. This package is not
   for SXFI AIR, AIR C or AIR GAMER.
2. Download and extract the release ZIP to a normal local folder on Windows.
3. Unplug the headset USB cable. Hold its **RGB lighting button**, plug USB
   back in, keep holding for about **five seconds**, then release. It is the
   lighting button, not the Super X-Fi button. Audio devices disappearing in
   recovery is expected.
4. Run **`INSTALL-r1.cmd`**. It verifies the updater hash and opens the native
   updater with `/F`. This opens the UI; it does not click Upgrade for you.
5. Confirm the correct headset, click **Upgrade**, and keep USB connected until
   the updater says **“Upgrade is successful.”** Close the updater afterward.
6. Check the three microphone-button states, including an actual recording
   in both Mic on states.

Full instructions, Windows prompts, troubleshooting and factory return:
**[Installation guide](docs/INSTALL.en.md)**.

## Release contents

| File | Purpose |
|---|---|
| `INSTALL-r1.cmd` | Hash-check and launch the ready r1 updater |
| `SXFI_GAMER_2.07.02_three-state-r1.exe` | Native updater with embedded r1 firmware |
| `RESTORE-factory.cmd` | Hash-check and launch the bundled stock updater |
| `SXFI_GAMER_2.07.02_FACTORY.exe` | Unchanged factory updater 2.07.02 |
| `INSTALL-ru.md`, `INSTALL-en.md` | Offline instructions |
| `SHA256SUMS.txt` | Checksums of the package files |

## What has been tested

The exact r1 image was installed successfully on **one EF0880 headset using
Windows 11**. Its owner confirmed: recording works with sidetone off, recording
works with sidetone on, and the third press disables the device microphone.
RGB-button recovery entry and normal USB reconnection were also verified.

This is a community release with limited hardware coverage. Other hardware
revisions, operating systems, every audio mode and extended power/reset
behavior have not been validated. The factory-return procedure is documented
and its original updater is included, but an actual factory rollback has
not been tested. Firmware flashing carries a risk of an unusable device if
interrupted or used on incompatible hardware.

The community updater is **unsigned**. It contains modified Creative firmware;
its code section and all resources except the embedded firmware are identical
to the factory updater. See [validation](docs/VALIDATION.md),
[technical changes](docs/TECHNICAL.md) and [third-party notices](THIRD_PARTY.md).

The firmware still reports `2.07.02 (81C80082)`. That version string alone
does not identify r1; use the release hashes and the three-state behavior.

## Source and feedback

- [Reproduce the firmware and run offline emulation](docs/BUILD.md).
- [Report a problem](https://github.com/Brian444github/sxfi-gamer-sidetone/issues/new).
  Include the model, Windows version, release name and exact updater message.
  Remove serial numbers, account names and other personal data from screenshots.
- Original patch code and tools: MIT. Vendor components retain their original
  terms; see [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md).

This project is not affiliated with or supported by Creative.
