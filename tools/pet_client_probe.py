"""Read-only disassembly helper for the pinned client; output is review evidence."""
import argparse
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

p = argparse.ArgumentParser()
p.add_argument('client', type=Path)
p.add_argument('--string')
p.add_argument('--address', type=lambda v: int(v, 0))
p.add_argument('--size', type=lambda v: int(v, 0), default=256)
a = p.parse_args()
pe = pefile.PE(str(a.client), fast_load=True)
raw = a.client.read_bytes()
base = pe.OPTIONAL_HEADER.ImageBase
if a.string:
    offset = raw.find(a.string.encode() + b'\0')
    if offset < 0: raise ValueError('String missing')
    address = base + pe.get_rva_from_offset(offset)
    print('string', hex(address))
    needle = struct.pack('<I', address)
    start = 0
    while (start := raw.find(needle, start)) >= 0:
        print('reference', hex(base + pe.get_rva_from_offset(start)))
        start += 4
if a.address:
    code = pe.get_data(a.address-base, a.size)
    for ins in Cs(CS_ARCH_X86, CS_MODE_32).disasm(code, a.address):
        print(f'{ins.address:08x} {ins.bytes.hex():20s} {ins.mnemonic} {ins.op_str}')
