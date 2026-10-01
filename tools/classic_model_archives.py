"""Bounded PFS/WLD transforms for isolated classic actor and texture names.

Format reference: EQEmu's Client Race Inventory / EQCommon S3DPackage and WLDFile.
This module never writes to a client directory and does not change mesh data.
"""
import re
import struct
import zlib

XOR = bytes.fromhex('953ac52a957a956a')
DIRECTORY_CRC = 0x61580AC9
MAX_ENTRY = 64 * 1024 * 1024
# RoF2's PFS reader expects the native 8 KiB block size, including the
# filename table. Larger zlib blocks round-trip here but fail in the client.
PFS_BLOCK_SIZE = 8192


def crc_name(name):
    value = 0
    for byte in name.lower().encode('ascii') + b'\0':
        value ^= byte << 24
        for _ in range(8):
            value = ((value << 1) ^ (0x04C11DB7 if value & 0x80000000 else 0)) & 0xFFFFFFFF
    return value


def read_pfs(raw):
    if len(raw) < 16 or raw[4:8] != b'PFS ':
        raise ValueError('Invalid PFS header')
    directory, _, version = struct.unpack_from('<III', raw)
    if version != 0x20000 or directory < 12 or directory + 4 > len(raw):
        raise ValueError('Invalid PFS directory')
    count = struct.unpack_from('<I', raw, directory)[0]
    if not 1 <= count <= 65536 or directory + 4 + count * 12 > len(raw):
        raise ValueError('Invalid PFS entry count')
    entries = {}
    for i in range(count):
        crc, offset, size = struct.unpack_from('<III', raw, directory + 4 + i * 12)
        if crc in entries or not 12 <= offset < directory or size > MAX_ENTRY:
            raise ValueError('Invalid PFS entry')
        entries[crc] = (offset, size)

    def inflate(entry):
        pos, size = entry
        result = bytearray()
        while len(result) < size:
            if pos + 8 > directory:
                raise ValueError('Truncated PFS block')
            packed, unpacked = struct.unpack_from('<II', raw, pos)
            pos += 8
            if not packed or not 0 < unpacked <= PFS_BLOCK_SIZE or len(result) + unpacked > size or pos + packed > directory:
                raise ValueError('Invalid PFS block size')
            decoder = zlib.decompressobj()
            block = decoder.decompress(raw[pos:pos + packed], unpacked + 1)
            if len(block) != unpacked or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                raise ValueError('Invalid PFS compressed block')
            result.extend(block)
            pos += packed
        return bytes(result)

    if DIRECTORY_CRC not in entries:
        raise ValueError('Missing PFS filename table')
    names = inflate(entries[DIRECTORY_CRC])
    if len(names) < 4:
        raise ValueError('Truncated PFS filename table')
    number = struct.unpack_from('<I', names)[0]
    if number > count:
        raise ValueError('Invalid PFS filename count')
    result, pos = {}, 4
    for _ in range(number):
        if pos + 4 > len(names):
            raise ValueError('Truncated PFS filename')
        length = struct.unpack_from('<I', names, pos)[0]
        pos += 4
        if not 1 <= length <= 256 or pos + length > len(names) or names[pos + length - 1] != 0:
            raise ValueError('Invalid PFS filename length')
        name = names[pos:pos + length - 1].decode('ascii').lower()
        pos += length
        if not re.fullmatch(r'[a-z0-9_. -]+', name) or name in result:
            raise ValueError('Invalid or duplicate PFS filename: ' + repr(name))
        key = crc_name(name)
        if key == DIRECTORY_CRC:
            continue  # Some native tables include their own directory entry.
        if key not in entries:
            raise ValueError('PFS filename CRC is missing: ' + repr(name))
        result[name] = inflate(entries[key])
    if pos != len(names):
        raise ValueError('Trailing PFS filename data')
    return result


def write_pfs(files):
    names = sorted(files)
    if not names or len({crc_name(n) for n in names}) != len(names) or DIRECTORY_CRC in {crc_name(n) for n in names}:
        raise ValueError('Empty archive or colliding filenames')
    table = bytearray(struct.pack('<I', len(names)))
    for name in names:
        encoded = name.encode('ascii') + b'\0'
        table.extend(struct.pack('<I', len(encoded)) + encoded)
    raw, entries = bytearray(12), []
    for crc, content in [(crc_name(name), files[name]) for name in names] + [(DIRECTORY_CRC, bytes(table))]:
        if not content or len(content) > MAX_ENTRY:
            raise ValueError('Invalid output entry size')
        offset = len(raw)
        for pos in range(0, len(content), PFS_BLOCK_SIZE):
            block = content[pos:pos + PFS_BLOCK_SIZE]
            packed = zlib.compress(block, 9)
            raw.extend(struct.pack('<II', len(packed), len(block)) + packed)
        entries.append((crc, offset, len(content)))
    directory = len(raw)
    raw.extend(struct.pack('<I', len(entries)))
    for entry in sorted(entries):
        raw.extend(struct.pack('<III', *entry))
    struct.pack_into('<III', raw, 0, directory, 0x20534650, 0x20000)
    return bytes(raw)


def crypt(raw):
    return bytes(value ^ XOR[i % 8] for i, value in enumerate(raw))


def wld_parts(raw):
    if len(raw) < 28:
        raise ValueError('Truncated WLD header')
    magic, version, count, _, _, size, _ = struct.unpack_from('<7I', raw)
    if magic != 0x54503D02 or version not in (0x15500, 0x1000C800) or 28 + size > len(raw):
        raise ValueError('Invalid WLD header')
    strings, fragments, pos = crypt(raw[28:28 + size]), [], 28 + size
    for _ in range(count):
        if pos + 12 > len(raw):
            raise ValueError('Truncated WLD fragment')
        length, kind, name = struct.unpack_from('<IIi', raw, pos)
        if length < 4 or pos + length + 8 > len(raw) or (name < 0 and -name >= len(strings)):
            raise ValueError('Invalid WLD fragment')
        fragments.append((pos, length, kind, name))
        pos += length + 8
    if raw[pos:] not in (b'', b'\xff\xff\xff\xff'):
        raise ValueError('Trailing WLD data')
    return strings, fragments


def actor_names(raw):
    strings, fragments = wld_parts(raw)
    return [strings[-name:].split(b'\0', 1)[0].decode('ascii')
            for _, _, kind, name in fragments if kind == 0x14 and name < 0]


def rename_wld(raw, aliases, filenames):
    """Retain byte lengths, all fragment references, geometry and animations."""
    strings, fragments = wld_parts(raw)
    def rename(value):
        # Actor names begin with the code; animation tracks prepend e.g. L01.
        # Never replace bone suffixes (IKSPE means IKS + pelvis, not SPE).
        start = 3 if re.match(rb'^[A-Z][0-9]{2}', value, re.I) else 0
        prefix = value[start:start + 3]
        if not prefix.isascii():
            return value  # Preserve unused string-table padding verbatim.
        source = prefix.decode('ascii').upper()
        if source not in aliases:
            return value
        replacement = aliases[source].encode('ascii')
        if value[start:start + 3].islower():
            replacement = replacement.lower()
        return value[:start] + replacement + value[start + 3:]

    renamed = b'\0'.join(rename(value) for value in strings.split(b'\0'))
    if len(renamed) != len(strings):
        raise ValueError('Actor alias changes WLD offsets')
    result = bytearray(raw)
    result[28:28 + len(strings)] = crypt(renamed)
    for pos, length, kind, _ in fragments:
        if kind != 0x03:
            continue
        # Fragment payload follows its signed name reference. Each filename has
        # a separate XOR stream, not the string table's running position.
        count = struct.unpack_from('<I', raw, pos + 12)[0] + 1
        cursor = pos + 16
        for _ in range(count):
            if cursor + 2 > pos + length + 8:
                raise ValueError('Truncated WLD texture filename')
            size = struct.unpack_from('<H', raw, cursor)[0]
            cursor += 2
            if not size or cursor + size > pos + length + 8:
                raise ValueError('Invalid WLD texture filename length')
            original = crypt(raw[cursor:cursor + size])
            name = original.rstrip(b'\0').decode('ascii')
            if name.lower() not in filenames:
                raise ValueError('Texture outside the pinned archive: ' + name)
            renamed_file = filenames[name.lower()]
            if len(renamed_file) != len(name):
                raise ValueError('Texture alias changes filename length')
            # Native WLD references often use uppercase while the PFS table
            # uses lowercase. Preserve that lexical casing for reversibility.
            renamed_file = ''.join(new.upper() if old.isupper() else new.lower()
                                   for old, new in zip(name, renamed_file))
            replacement = renamed_file.encode('ascii')
            replacement += b'\0' * (size - len(replacement))
            if len(replacement) != size:
                raise ValueError('Texture alias changes WLD offsets')
            result[cursor:cursor + size] = crypt(replacement)
            cursor += size
    return bytes(result)
