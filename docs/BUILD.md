# Reproduce r1 (developers)

Installation uses the ready release ZIP; these steps are only for rebuilding
or reviewing the patch. The tools do not open USB devices or flash a headset.

## Requirements

- Python 3 with venv and pip.
- Dependencies pinned in `requirements-dev.txt`.
- The unchanged Creative 2.07.02 updater. It is already included as
  `SXFI_GAMER_2.07.02_FACTORY.exe` in the Windows release ZIP.

The input must have SHA-256
`1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496`.
The tool rejects another version. It reads the EXE as PE data and extracts its
embedded image; it does not execute the factory updater.

## Build firmware and run checks

From the repository directory, create a venv and install dependencies:

```text
python -m venv .venv
```

Activate it using `.venv\Scripts\activate` on Windows or
`source .venv/bin/activate` on Linux, then:

```text
python -m pip install -r requirements-dev.txt
python tools/build.py "path/to/SXFI_GAMER_2.07.02_FACTORY.exe"
```

The output directory defaults to `build/`; use `--out` for a different one.
The tool extracts the exact FMAIN, assembles the cycle and trampoline, rebuilds
CIFF, checks both known r1 hashes and runs the startup/heap/button emulation.
It writes the manifest and detailed offline verification results beneath
`build/candidate/`. No firmware bytes are committed to the source tree.

Expected output hashes:

```text
4ae6e3b6f4e14d310f6dedafe3293c48a6658137f757fd1b1999ce3ec160b05b  FMAIN.experimental.bin
0af6cbe38b9302db1d614374ff20339f556b1cbdf443712bf1082a3350867887  SXFI_GAMER_2.07.02-three-state-r1.experimental.ciff
```

The historical `experimental` filenames identify build outputs; hardware
validation of the shipped r1 is described separately in [VALIDATION.md](VALIDATION.md).
Do not run Python with `-O`: the development checks intentionally use assertions.

## Optional Windows updater wrapping

On Windows, use a fresh output directory:

```text
python tools/build.py "path/to/SXFI_GAMER_2.07.02_FACTORY.exe" --out build-windows --installer
```

`wrap_installer.py` uses the Windows resource APIs to replace only the embedded
firmware resource. It removes the obsolete vendor signature, recalculates the
PE checksum and checks the native code and other resources against the stock
EXE. Resource-writer details can depend on Windows; the published installer is
identified by its own SHA-256 in VALIDATION.md. Reproducing the firmware must
always yield the exact FMAIN and CIFF hashes above.

The optional wrapping helper is derived from the method used to produce the
tested updater. The release itself distributes the original tested updater
bytes, rather than silently substituting a fresh repack.

## Prepare the release ZIP

`tools/package_release.py` takes a directory containing the two verified EXEs
and assembles the ready Windows ZIP using the committed launcher/instruction
files. It refuses unexpected EXE hashes and computes a package manifest and
the standalone ZIP checksum file. It does not execute either updater.

```text
python tools/package_release.py --binaries "path/to/exes" --out dist
```
