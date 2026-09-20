"""Reject a stale ELF world startup contract before installing market binaries.

This focused check does not replace a fresh paired build or runtime smoke test.
"""
import argparse
from pathlib import Path


def verify_world(data):
    if not data.startswith(b'\x7fELF'):
        raise ValueError('Expected an ELF world binary')
    if b'CALL nightcap_market_rotate({},{},{})\x00' not in data:
        raise ValueError('World lacks the current three-argument market startup contract')
    if b'CALL nightcap_market_rotate({})\x00' in data:
        raise ValueError('World contains the obsolete one-argument market startup contract')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('world',type=Path)
    args=parser.parse_args()
    verify_world(args.world.read_bytes())
    print('World market startup contract verified (three arguments).')
