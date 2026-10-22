# Install r1 on Creative SXFI GAMER EF0880

## 1. Prepare

This release targets **Creative SXFI GAMER, model EF0880**, USB VID/PID
`041E:3269`. Check the headset's model marking; a USB ID alone is not enough.
SXFI AIR, AIR C and AIR GAMER are different products.

Installation was verified on Windows 11. The ready updater already contains
the firmware. Python, compiling code and installing SXFI Control are not
required for this procedure. Other Windows versions have not been tested.

1. Download **`SXFI_GAMER_2.07.02_three-state-r1_Windows.zip`** from
   <https://github.com/Brian444github/sxfi-gamer-sidetone/releases/tag/v2.07.02-three-state-r1>.
2. Extract the **entire** archive to a local folder. Do not run it inside the ZIP.
3. Close programs using the headset and other Creative updaters. Use a reliable,
   direct USB connection. Connect only the target headset if you own several.
4. Keep the computer powered and awake throughout the update. Do not unplug USB
   or restart the computer while firmware is being written.

The modified EXE is not signed by Creative. Windows may show an unknown-publisher
or SmartScreen warning. Check the source and SHA-256. If Windows offers
“More info → Run anyway”, use it only for the verified file. If your computer's
policy prevents running it, stop; this procedure does not require disabling
Windows protection.

## 2. Enter recovery

1. Disconnect the headset USB cable from the computer.
2. Hold the headset's **RGB lighting button**.
3. Reconnect USB while holding that button.
4. Keep holding for approximately **five seconds**, then release.

Use the lighting button, **not Super X-Fi** and not the microphone button.
This entry method was verified on the tested EF0880. The headset does not
provide playback or recording in recovery. Windows exposes HID and serial
interfaces instead; the COM-port number varies by computer. Missing headset
audio devices in this mode is expected.

To leave recovery without flashing, unplug and reconnect USB without holding
any buttons. This exit method was also verified.

## 3. Install

1. Run **`INSTALL-r1.cmd`** from the extracted folder.
2. The launcher verifies the updater's SHA-256 and stops on a mismatch.
3. The native Creative updater opens with the embedded r1 image. The launcher
   supplies `/F`, allowing an update with the same factory version number 2.07.02.
4. Check that the correct headset is detected and **Upgrade** is available.
   If the device is missing, use troubleshooting below.
5. Click **Upgrade** once. Keep USB connected and the program open while it
   displays **“Upgrading in progress...”**.
6. Wait for **“Upgrade is successful.”** Then close the updater. The headset
   should return to normal USB audio mode. If Windows has not refreshed its
   devices after success, reconnect USB without holding any buttons.

Manual equivalent in PowerShell, from the package folder:

```powershell
& '.\SXFI_GAMER_2.07.02_three-state-r1.exe' /F
```

Check the hash before a manual launch. Do not add `/S` or `/B`: this procedure
uses the visible updater UI and updates the main firmware.

## 4. Verify the result

Turn off software microphone monitoring in Windows and voice-app tests before
checking the headset. In Windows microphone properties → Listen, leave
“Listen to this device” unchecked for this test.

Starting with the first eligible microphone-button press:

1. **Mic on:** no self-monitoring, but recording works. Make a short recording
   and listen to it after recording finishes.
2. **Mic on:** self-monitoring is audible, and recording still works.
3. **Mic off:** the headset mutes the microphone; new recordings receive no
   voice. Unmuting in Windows does not override this headset mute.

The cycle repeats. Initial behavior on power-up remains stock: r1 does not
automatically disable sidetone at startup. The first eligible press selects
Mic on without sidetone. The selected state is not retained across power loss.

The device still reports `2.07.02 (81C80082)`. That is expected and does not
uniquely identify r1; verify the actual three-state behavior.

## 5. Troubleshooting

- **Headset audio disappeared after entering recovery:** expected; run the updater.
- **No device detected or Upgrade unavailable:** if firmware writing is not in
  progress, close the updater, repeat RGB-button recovery entry and run
  `INSTALL-r1.cmd` again. Check the cable/direct USB port and let Windows finish
  installing standard devices. Do not replace drivers with Zadig or select an
  arbitrary COM port. If it still fails, report the exact message in an Issue.
- **Hash mismatch:** stop and download the release again from this repository.
- **Update error:** record the exact message. Do not run multiple updaters.
  Do not interrupt a current write or treat missing audio during an unfinished
  operation as proof that the headset is broken.
- **First two states sound the same:** check software monitoring, then test
  recording and the button cycle again. Include the results in your Issue.

Hardware recovery entry was verified on a working headset. Recovery after
arbitrary corruption or an interrupted write has not been tested; restoration
from every possible failure is not guaranteed.

## 6. Return to factory firmware

The package includes the **unchanged** factory updater 2.07.02. The procedure
below uses the same update mode, but **an actual r1-to-factory rollback has not
yet been tested**.

1. Enter recovery using the RGB button as described above.
2. Run **`RESTORE-factory.cmd`**. It checks the factory EXE hash and opens it with `/F`.
3. Check the target device, click Upgrade and wait for “Upgrade is successful.”
   Keep USB connected throughout the write.
4. Close the updater and check the original microphone behavior.

Manual equivalent after checking the hash:

```powershell
& '.\SXFI_GAMER_2.07.02_FACTORY.exe' /F
```

## 7. Check hashes

In PowerShell, from the package folder:

```powershell
Get-FileHash '.\SXFI_GAMER_2.07.02_three-state-r1.exe' -Algorithm SHA256
Get-FileHash '.\SXFI_GAMER_2.07.02_FACTORY.exe' -Algorithm SHA256
```

Expected SHA-256:

```text
82d96a46f4e43233f0a983ecd06ba10ee73612c46d30afc5a9061c5e60ac6adb  SXFI_GAMER_2.07.02_three-state-r1.exe
1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496  SXFI_GAMER_2.07.02_FACTORY.exe
```

The ZIP's checksum is published as a separate GitHub Release asset. Hashes
confirm byte identity with the published release, not a vendor signature or
compatibility with every headset.
