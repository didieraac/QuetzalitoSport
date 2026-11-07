#!/usr/bin/env python3
"""Pato Player 29 V2: parches DEX verificados contra el APK original exacto."""
import hashlib
import struct
import sys
import zipfile
import zlib
from pathlib import Path

EXPECTED_APK="1a63ebb5cd727f2161e225169a16fe82a01c1832220be91d108762ef10f869ed"
EXPECTED_DEX={
    "classes.dex":("fe2106fd16d65addefe7a706e6ec974e77b0671def42989336a64bdec8e8e3cf",None),
    "classes2.dex":("6801b90a415affead1ec652987a924f604b6aebded4628d2e1a700090e237840","17cf2ee4b87909dd5e876aab8bbd8aff1f964e77b1618eef8775a15e71d82451"),
    "classes3.dex":("156c60ce57ac445bf2ddab3d65480ebd3fe5d626c107aed8dda14df085420299","c95fbc921f1781448d90a70cf1dc456c1d6010ca0324fbc32631ca8c37c7f745"),
}
PATCHES={
    "classes2.dex":[
        (1926756,"1a001c02","0e000000"),
    ],
    "classes3.dex":[
        (545544,"6e102a0303000c","0e000000000000"),
        (545632,"6e103a0302000c","0e000000000000"),
        (664726,"6e306d1201000a","0f000000000000"),
        (664752,"5490260b","12000f00"),
        (665854,"6e30721201000a","0f000000000000"),
        (665882,"390303","0f0000"),
        (665958,"6e30721201020a02","0f00000000000000"),
        (665986,"6e30721221000a02","0f00000000000000"),
        (666012,"6e306d1221030a02","12000f0000000000"),
        (667216,"6200ae0b","0e000000"),
        (667256,"2200b004","0e000000"),
        (667292,"2200b004","0e000000"),
        (667328,"12","0e"),
        (667356,"5420260b","0e000000"),
        (667476,"6200ae0b","0e000000"),
        (667516,"6200ae0b","0e000000"),
        (667548,"6200ae0b","0e000000"),
        (668076,"22003f03","0e000000"),
        (668112,"2200b004","0e000000"),
        (668148,"12","0e"),
        (668176,"1215","0e00"),
        (668212,"22003f03","0e000000"),
    ],
}
def sha(data):
    return hashlib.sha256(data).hexdigest()

def patch(name, data):
    old_hash, new_hash=EXPECTED_DEX[name]
    if sha(data)!=old_hash:
        raise SystemExit("DEX original inesperado: "+name)
    if name not in PATCHES:
        return data
    buf=bytearray(data)
    for offset, old_hex, new_hex in PATCHES[name]:
        old=bytes.fromhex(old_hex)
        new=bytes.fromhex(new_hex)
        assert len(old)==len(new)
        assert buf[offset:offset+len(old)]==old,(name,offset)
        buf[offset:offset+len(old)]=new
    buf[12:32]=hashlib.sha1(buf[32:]).digest()
    struct.pack_into("<I",buf,8,zlib.adler32(buf[12:])&0xffffffff)
    if sha(buf)!=new_hash:
        raise SystemExit("El parche no coincide con la V2 comprobada: "+name)
    return bytes(buf)

def main():
    src=Path(sys.argv[1]);dst=Path(sys.argv[2])
    if sha(src.read_bytes())!=EXPECTED_APK:
        raise SystemExit("ERROR: URL oficial no coincide con el APK adjuntado. Se aborta.")
    with zipfile.ZipFile(src) as zin,zipfile.ZipFile(dst,"w") as zout:
        for info in zin.infolist():
            data=zin.read(info)
            if info.filename in EXPECTED_DEX:
                data=patch(info.filename,data)
            # No cambiar las bibliotecas ni los recursos del reproductor.
            zout.writestr(info,data)
    with zipfile.ZipFile(dst) as z:
        assert z.testzip() is None
        for n,(_,target) in EXPECTED_DEX.items():
            if target:
                assert sha(z.read(n))==target
    print("V2 sin firmar reproducida desde el APK original verificado.")

if __name__=="__main__":
    main()
