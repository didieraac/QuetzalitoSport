#!/usr/bin/env python3
"""Aplica el parche V5 al APK original, tras verificar sus hashes."""
import hashlib
import struct
import sys
import zipfile
import zlib
from pathlib import Path

ORIGINAL_APK_SHA256 = "96e0b15ded06eb70ae70d551613b2fcafca85328589954222c222793a64c8259"
ORIGINAL_DEX_SHA256 = "0c39feac29fccafad576daa1da498910c719b13b6779609222a20073f6e3d0a5"
EXPECTED_MODIFIED_DEX_SHA256 = "1d797c5976e8d98a64119d921efc126dd5e964c903d0817fb6fe76b17ce66546"

PATCHES = [
    (1282636, "1a", "0e"),
    (1282638, "6468", "0000"),
    (3914062, "3334423030464446343538413441353131444246444437344333383434433339", "3432304141394145393337353643464438373642343539454135354436374638"),
    (3914095, "4232", "3235"),
    (3914098, "37363933413142", "35304238433737"),
    (3914106, "3443", "3035"),
    (3914109, "41364439434131433537324441", "42343134454437423241364138"),
    (3914123, "303031", "443230"),
]

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def patch_dex(data):
    if sha256(data) != ORIGINAL_DEX_SHA256:
        raise RuntimeError("classes.dex original no coincide")
    buf = bytearray(data)
    for offset, old_hex, new_hex in PATCHES:
        old, new = bytes.fromhex(old_hex), bytes.fromhex(new_hex)
        if len(old) != len(new) or buf[offset:offset + len(old)] != old:
            raise RuntimeError(f"Contenido inesperado en {offset}")
        buf[offset:offset + len(old)] = new
    buf[12:32] = hashlib.sha1(buf[32:]).digest()
    buf[8:12] = struct.pack("<I", zlib.adler32(buf[12:]) & 0xffffffff)
    if sha256(buf) != EXPECTED_MODIFIED_DEX_SHA256:
        raise RuntimeError("La versión DEX resultante es distinta a V5")
    return bytes(buf)

def main():
    if len(sys.argv) != 3:
        sys.exit("Uso: patch.py Original.apk Unsigned.apk")
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    if sha256(source.read_bytes()) != ORIGINAL_APK_SHA256:
        sys.exit("El APK descargado difiere del original; se aborta")
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, "w", allowZip64=True) as dst:
        for info in src.infolist():
            if info.filename in ("META-INF/CERT.SF", "META-INF/CERT.RSA", "META-INF/MANIFEST.MF"):
                continue
            data = src.read(info)
            if info.filename == "classes.dex":
                data = patch_dex(data)
            dst.writestr(info, data)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert z.read("classes.dex")[:8] == b"dex\\n035\\x00"
    print(f"APK sin firmar generado: {output}")

if __name__ == "__main__":
    main()
