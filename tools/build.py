"""Rebuild r1 from the exact stock updater, without accessing USB devices."""
import argparse
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys

import pefile

ROOT = Path(__file__).resolve().parents[1]
FACTORY_SHA = "1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496"
CIFF_SHA = "0ebab178dd4f9aa5b0c3ea975040279df39bd2aec7073bfef55c288bd12c4eb3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("factory", type=Path, help="Unchanged Creative 2.07.02 updater")
    parser.add_argument("--out", type=Path, default=ROOT / "build")
    parser.add_argument("--installer", action="store_true", help="Also rebuild Windows EXE on Windows")
    args = parser.parse_args()
    stock = args.factory.resolve()
    data = stock.read_bytes()
    if hashlib.sha256(data).hexdigest() != FACTORY_SHA:
        raise SystemExit("Wrong input: only the exact factory updater 2.07.02 is supported.")
    pe = pefile.PE(data=data)
    matches = []
    for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if kind.id != 10:
            continue
        for name in kind.directory.entries:
            if str(name.name) != "CUDSP600_RDCATA":
                continue
            for lang in name.directory.entries:
                if lang.id == 1033:
                    entry = lang.data.struct
                    matches.append(pe.get_data(entry.OffsetToData, entry.Size))
    if len(matches) != 1 or hashlib.sha256(matches[0]).hexdigest() != CIFF_SHA:
        raise SystemExit("Factory firmware resource mismatch.")
    ciff = matches[0]
    chunks = []
    pos = 8
    while pos < len(ciff):
        tag, size = struct.unpack_from("<4sI", ciff, pos)
        chunk = ciff[pos + 8:pos + 8 + size]
        if len(chunk) != size:
            raise SystemExit("Truncated CIFF.")
        if tag == b"DATA" and chunk[:32].decode("utf-16le").rstrip("\0") == "FMAIN":
            chunks.append(chunk[32:])
        pos += 8 + size
    if len(chunks) != 1 or pos != len(ciff):
        raise SystemExit("Unexpected factory CIFF layout.")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "FMAIN.bin").write_bytes(chunks[0])
    (out / "CUDSP600_RDCATA.bin").write_bytes(ciff)
    env = dict(os.environ, SXFI_BUILD_DIR=str(out))
    for script in ["build_candidate.py", "verify_candidate.py"]:
        subprocess.run([sys.executable, str(ROOT / "src" / script)], env=env, check=True)
    if args.installer:
        subprocess.run([sys.executable, str(ROOT / "tools" / "wrap_installer.py"),
                        str(stock), str(out / "candidate" / "SXFI_GAMER_2.07.02-three-state-r1.experimental.ciff"),
                        str(out / "SXFI_GAMER_2.07.02_three-state-r1.exe")], check=True)
    print("r1 firmware reproduced and offline emulation passed. No device commands sent.")


if __name__ == "__main__":
    main()
