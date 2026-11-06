#!/usr/bin/env python3
"""Parche local de publicidad para Quetzalito Sport 6.0.
Nunca modifica el orden de string_ids del DEX.
"""
import hashlib
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

ORIGINAL_APK_SHA256 = "96e0b15ded06eb70ae70d551613b2fcafca85328589954222c222793a64c8259"
ORIGINAL_DEX_SHA256 = "0c39feac29fccafad576daa1da498910c719b13b6779609222a20073f6e3d0a5"
ORIGINAL_CERT_SHA256 = b"34B00FDF458A4A511DBFDD74C3844C396B2A7693A1BE4CDA6D9CA1C572DA5001"
CERT_STRING_OFFSET = 3914062

def digest(data):
    return hashlib.sha256(data).hexdigest()

def replace_at(data, offset, old, replacement):
    assert len(old) == len(replacement)
    if data[offset:offset + len(old)] != old:
        raise RuntimeError("Contenido inesperado en la posición " + str(offset))
    data[offset:offset + len(old)] = replacement

def patch_dex(data, cert_sha256):
    if digest(data) != ORIGINAL_DEX_SHA256:
        raise RuntimeError("El DEX original no coincide")
    cert_sha256 = cert_sha256.upper().encode("ascii")
    if not re.fullmatch(rb"[0-9A-F]{64}", cert_sha256):
        raise RuntimeError("Huella de certificado inválida")
    # El valor ocupa un string_id entre "30" y "4". Mantener ese orden
    # evita la excepción Out-of-order string_ids que provocaba la V5.
    if not b"30" < cert_sha256 < b"4":
        raise RuntimeError("La huella no mantiene el orden DEX requerido")
    buf = bytearray(data)
    # V7: no cancelar el método entero: su último paso abre el canal original.
    # Al entrar: v8=Context, v9=Intent. Ejecutar Context.startActivity(Intent)
    # (invoke-virtual method@0x0289) y devolver, sin abrir la URL publicitaria.
    replace_at(buf, 1282636, bytes.fromhex("1a00646812011212"),
               bytes.fromhex("6e20890298000e00"))
    replace_at(buf, CERT_STRING_OFFSET, ORIGINAL_CERT_SHA256, cert_sha256)
    # Reparar ambos checksums obligatorios del formato DEX.
    buf[12:32] = hashlib.sha1(buf[32:]).digest()
    buf[8:12] = struct.pack("<I", zlib.adler32(buf[12:]) & 0xffffffff)
    assert struct.unpack_from("<I", buf, 8)[0] == (zlib.adler32(buf[12:]) & 0xffffffff)
    return bytes(buf)

def main():
    if len(sys.argv) != 4:
        sys.exit("Uso: patch.py Original.apk Unsigned.apk CERT_SHA256")
    source, output, fingerprint = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    if digest(source.read_bytes()) != ORIGINAL_APK_SHA256:
        sys.exit("El APK original difiere del archivo analizado")
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, "w", allowZip64=True) as dst:
        for info in src.infolist():
            if info.filename in ("META-INF/CERT.SF", "META-INF/CERT.RSA", "META-INF/MANIFEST.MF"):
                continue
            payload = src.read(info)
            if info.filename == "classes.dex":
                payload = patch_dex(payload, fingerprint)
            dst.writestr(info, payload)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert z.read("classes.dex")[:8] == b"dex\n035\x00"
    print("Paquete preparado con el certificado elegido:", fingerprint.upper())

if __name__ == "__main__":
    main()
