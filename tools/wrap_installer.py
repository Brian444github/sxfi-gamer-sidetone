"""Replace the native updater's embedded image, using Windows resource APIs."""
import ctypes
import hashlib
from pathlib import Path
import shutil
import sys

import pefile

FACTORY_SHA = "1e451307c07e6ea643ed5f88eb4e7e074f985f6b740adea219940ce596965496"
CIFF_SHA = "0af6cbe38b9302db1d614374ff20339f556b1cbdf443712bf1082a3350867887"


def resources(pe):
    result = {}
    def walk(entries, path=()):
        for entry in entries:
            name = str(entry.name) if entry.name is not None else str(entry.id)
            if hasattr(entry, "directory"):
                walk(entry.directory.entries, path + (name,))
            else:
                d = entry.data.struct
                result[path + (name,)] = pe.get_data(d.OffsetToData, d.Size)
    walk(pe.DIRECTORY_ENTRY_RESOURCE.entries)
    return result


def main():
    if sys.platform != "win32":
        raise SystemExit("The optional EXE wrapping step requires Windows.")
    if len(sys.argv) != 4:
        raise SystemExit("Usage: wrap_installer.py factory.exe r1.ciff output.exe")
    stock, image, output = [Path(x).resolve() for x in sys.argv[1:]]
    if stock == output or image == output:
        raise SystemExit("Output must be a separate file.")
    original, ciff = stock.read_bytes(), image.read_bytes()
    if hashlib.sha256(original).hexdigest() != FACTORY_SHA or hashlib.sha256(ciff).hexdigest() != CIFF_SHA:
        raise SystemExit("Input hash mismatch.")
    if output.exists():
        raise SystemExit("Output already exists; choose a fresh path.")
    shutil.copyfile(stock, output)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.BeginUpdateResourceW.argtypes = [ctypes.c_wchar_p, ctypes.c_int]
    kernel.BeginUpdateResourceW.restype = ctypes.c_void_p
    kernel.UpdateResourceW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p,
                                     ctypes.c_ushort, ctypes.c_void_p, ctypes.c_uint]
    kernel.UpdateResourceW.restype = ctypes.c_int
    kernel.EndUpdateResourceW.argtypes = [ctypes.c_void_p, ctypes.c_int]
    kernel.EndUpdateResourceW.restype = ctypes.c_int
    handle = kernel.BeginUpdateResourceW(str(output), False)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    buf = ctypes.create_string_buffer(ciff)
    if not kernel.UpdateResourceW(handle, ctypes.c_void_p(10), "CUDSP600_RDCATA", 1033, buf, len(ciff)):
        error = ctypes.get_last_error()
        kernel.EndUpdateResourceW(handle, True)
        raise ctypes.WinError(error)
    if not kernel.EndUpdateResourceW(handle, False):
        raise ctypes.WinError(ctypes.get_last_error())
    pe = pefile.PE(data=output.read_bytes())
    security = pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
    offset, length = security.VirtualAddress, security.Size
    security.VirtualAddress = security.Size = pe.OPTIONAL_HEADER.CheckSum = 0
    data = pe.write()
    if offset and offset + length == len(data):
        data = data[:offset]
    pe = pefile.PE(data=data)
    pe.OPTIONAL_HEADER.CheckSum = pe.generate_checksum()
    output.write_bytes(pe.write())
    before, after = pefile.PE(data=original), pefile.PE(data=output.read_bytes())
    old, new = resources(before), resources(after)
    key = ("10", "CUDSP600_RDCATA", "1033")
    if old.keys() != new.keys() or new[key] != ciff or any(old[k] != new[k] for k in old if k != key):
        raise SystemExit("Resource verification failed.")
    text = lambda p: next(s.get_data() for s in p.sections if s.Name.rstrip(b"\0") == b".text")
    if text(before) != text(after) or not after.verify_checksum() or after.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size:
        raise SystemExit("Executable verification failed.")
    print("Built EXE SHA-256:", hashlib.sha256(output.read_bytes()).hexdigest())
    print("Embedded r1 exact; native updater code and all other resources unchanged; unsigned.")


if __name__ == "__main__":
    main()
