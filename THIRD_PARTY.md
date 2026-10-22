# Third-party components

This is an unofficial community modification for the Creative SXFI GAMER
EF0880. It is not made, approved, signed or supported by Creative.

The downloadable Windows release includes Creative's 2.07.02 updater and
firmware, plus a modified copy with the community sidetone patch. The stock
bootloader, voice prompts and other firmware assets retain their original
ownership. Creative's components are proprietary and remain subject to the
manufacturer's applicable terms; this project does not grant a new license
to those components. Creative and SXFI are trademarks of their respective
owners. The MIT license applies to this project's original contributions.

Original updater filename: `SXFI_GAMER_Upgrade_2_07_02.exe`.

Original manufacturer distribution URL (provenance; no download needed for
installation of the ready release):
<http://sxficonnect.creative.com/windows/v1.0/product/SXFI_GAMER_Upgrade_2_07_02.exe>

SHA-256:
`1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496`.

The unchanged factory EXE had a valid Creative Technology Ltd Authenticode
signature when checked during preparation. Modifying its embedded firmware
invalidates that signature, so the obsolete signature was removed from the
community EXE. The community EXE is unsigned; the release does not claim it
is signed by Creative. Release hashes identify the distributed bytes.

Optional development dependencies are pinned in `requirements-dev.txt`:
Capstone, Unicorn, Keystone and pefile. Their licenses remain with their
respective projects. They are not required to install the ready Windows
release and are not bundled into the installer.
