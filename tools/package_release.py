"""Package the exact tested binaries with offline instructions; no device access."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "SXFI_GAMER_2.07.02_three-state-r1_Windows"
BINARIES = {
    "SXFI_GAMER_2.07.02_three-state-r1.exe": "82d96a46f4e43233f0a983ecd06ba10ee73612c46d30afc5a9061c5e60ac6adb",
    "SXFI_GAMER_2.07.02_FACTORY.exe": "1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    files = {}
    for name, digest in BINARIES.items():
        data = (args.binaries / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit("Unrecognized binary: " + name)
        files[name] = data
    for name in ["INSTALL-r1.cmd", "RESTORE-factory.cmd"]:
        data = (ROOT / "package" / name).read_text(encoding="ascii")
        files[name] = data.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")
    for lang in ["ru", "en"]:
        files[f"INSTALL-{lang}.md"] = (ROOT / "docs" / f"INSTALL.{lang}.md").read_bytes()
    for name in ["LICENSE", "THIRD_PARTY.md"]:
        files[name] = (ROOT / name).read_bytes()
    lines = [f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items())]
    files["SHA256SUMS.txt"] = "".join(lines).encode("ascii")
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out / (NAME + ".zip")
    if output.exists():
        raise SystemExit("Release ZIP already exists; choose a fresh output directory.")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(NAME + "/" + name, date_time=(2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (args.out / "SHA256SUMS.txt").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(digest, output.name, output.stat().st_size)


if __name__ == "__main__":
    main()
