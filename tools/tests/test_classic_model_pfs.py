"""PFS writer compatibility checks independent of the production PFS reader.

RoF2's version 2 PFS reader selects 8192-byte blocks at eqgame.exe VA
0x7AA860 (supported SHA256 2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e).
Its stock global_chr.s3d and nektulos_chr.s3d use this size too.
EQZip independently uses the same limit in EQArchiveFile.SetContents:
https://github.com/Shendare/EQZip/blob/master/EQArchive.cs#L945-L1005
The 2026-10-01 startup incident shipped 65536-byte blocks instead. A
round-trip through our unbounded read_pfs cannot detect that incompatibility.
"""
import struct
import unittest
import zlib

from classic_model_archives import read_pfs, write_pfs


def read_with_native_block_capacity(raw):
    """Extract by physical offset, as EQRI does, with an 8 KiB output buffer."""
    directory, magic, version = struct.unpack_from('<III', raw)
    if (magic, version) != (0x20534650, 0x20000):
        raise ValueError('Not a version 2 PFS archive')
    count, = struct.unpack_from('<I', raw, directory)
    entries = sorted(
        (struct.unpack_from('<III', raw, directory + 4 + i * 12)
         for i in range(count)),
        key=lambda entry: entry[1],
    )
    contents = []
    for _, position, size in entries:
        extracted = bytearray()
        while len(extracted) < size:
            packed_size, expected_size = struct.unpack_from('<II', raw, position)
            position += 8
            if not 0 < expected_size <= 8192:
                raise ValueError(f'PFS block exceeds native 8192-byte capacity: {expected_size}')
            if position + packed_size > directory:
                raise ValueError('Block crosses the PFS index')
            decoder = zlib.decompressobj()
            block = decoder.decompress(raw[position:position + packed_size], 8192)
            if (len(block) != expected_size or not decoder.eof
                    or decoder.unconsumed_tail or decoder.unused_data):
                raise ValueError('Block cannot inflate completely into the native buffer')
            extracted.extend(block)
            position += packed_size
        if len(extracted) != size:
            raise ValueError('Entry length mismatch')
        contents.append(bytes(extracted))

    # EQRI sorts entries by offset and treats the last entry as the name table.
    names = contents.pop()
    name_count, = struct.unpack_from('<I', names)
    if name_count != len(contents):
        raise ValueError('Filename count mismatch')
    result, position = {}, 4
    for content in contents:
        length, = struct.unpack_from('<I', names, position)
        position += 4
        name = names[position:position + length]
        if not name.endswith(b'\0'):
            raise ValueError('Unterminated filename')
        result[name[:-1].decode('ascii')] = content
        position += length
    if position != len(names):
        raise ValueError('Filename table length mismatch')
    return result


class ClassicModelPfsCompatibility(unittest.TestCase):
    def test_validator_rejects_oversized_version_2_block(self):
        # Construct a valid zlib/PFS entry with matching lengths. Merely
        # changing a block count would also trip the old entry-length guard
        # and would fail to prove the native-capacity check is necessary.
        payload = b'x' * 8193
        name = b'ncm01_chr.wld\0'
        table = struct.pack('<II', 1, len(name)) + name
        packed_payload, packed_table = zlib.compress(payload), zlib.compress(table)
        payload_block = struct.pack('<II', len(packed_payload), len(payload)) + packed_payload
        table_block = struct.pack('<II', len(packed_table), len(table)) + packed_table
        table_offset = 12 + len(payload_block)
        directory_offset = table_offset + len(table_block)
        raw = (struct.pack('<III', directory_offset, 0x20534650, 0x20000)
               + payload_block + table_block + struct.pack('<I', 2)
               # Fixed CRC of the literal filename, then the filename table.
               + struct.pack('<III', 0x01DD1BA9, 12, len(payload))
               + struct.pack('<III', 0x61580AC9, table_offset, len(table)))
        with self.assertRaisesRegex(ValueError, 'Invalid PFS block size'):
            read_pfs(raw)

    def test_large_actor_data_remains_readable_with_native_block_capacity(self):
        for size in (8191, 8192, 8193, 65536, 65537):
            with self.subTest(size=size):
                content = bytes(range(256)) * (size // 256) + bytes(range(size % 256))
                files = {'ncm01_chr.wld': content}
                self.assertEqual(read_with_native_block_capacity(write_pfs(files)), files)

    def test_large_filename_table_also_uses_native_sized_blocks(self):
        # Stock global_chr has 1617 payload entries and about 29 KiB of names.
        # Each payload here is tiny, isolating the filename-table block path.
        files = {f'ncm{i:05d}.bmp': bytes([i % 256]) for i in range(1617)}
        self.assertEqual(read_with_native_block_capacity(write_pfs(files)), files)


if __name__ == '__main__':
    unittest.main()
