"""Authenticated world status and targeted Doors reload; run inside game.

The reviewed operator supplies AFFECTED and MODE. No credentials are emitted.
Only empty affected zones may refresh; the caller verifies native reload logs.
"""
import json
from pathlib import Path
import re
import socket
import struct


def frame(kind, payload):
    return struct.pack('<IB', len(payload), kind) + payload


def packet(opcode, payload):
    return frame(5, struct.pack('<IH', len(payload), opcode) + payload)


def read_exact(sock, count):
    result = b''
    while len(result) < count:
        part = sock.recv(count - len(result))
        if not part:
            raise RuntimeError('World connection closed')
        result += part
    return result


def parse_status(message):
    rows = []
    for line in message.split('^'):
        if not line.startswith('#'):
            continue
        fields = [s.strip() for s in line.split(' :: ')]
        assert len(fields) == 7, 'Unexpected status format'
        zone = re.fullmatch(r'([a-zA-Z0-9_]+) \((\d+)\)', fields[5])
        pid = int(fields[6].strip('()'))
        if pid == 0:
            continue  # This status-only authenticated connection has no worker.
        assert fields[5] == '' or zone, 'A zone is still booting'
        rows.append({'server_id': int(fields[0][1:]), 'pid': pid,
                     'players': int(fields[3]), 'zone': zone[1].lower() if zone else '',
                     'zone_id': int(zone[2]) if zone else 0})
    assert len(rows) == 12 and len({r['pid'] for r in rows}) == 12
    return rows


def selected(rows, affected):
    result = [r for r in rows if r['zone'] in {z.lower() for z in affected}]
    assert all(r['players'] == 0 for r in result), 'Affected zone occupied; no live object refresh'
    return result


def inspect_workers(rows):
    result = []
    for row in rows:
        p = Path('/proc', str(row['pid']))
        assert (p / 'comm').read_text().strip() == 'zone'
        logs = {str(f.resolve()): f.resolve().stat().st_size for f in (p / 'fd').iterdir()
                if '/logs/' in str(f.resolve()) and f.resolve().is_file()}
        if row['zone']:
            assert any('/' + row['zone'] + '_version_' in name.lower() for name in logs)
        result.append({**row, 'start': (p / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                       'logs': logs})
    return result


def emote(sock):
    for _ in range(50):
        length, kind = struct.unpack('<IB', read_exact(sock, 5))
        assert length < 1024 * 1024
        data = read_exact(sock, length)
        if kind == 5 and len(data) >= 6:
            size, opcode = struct.unpack('<IH', data[:6])
            assert size == len(data) - 6
            if opcode == 0x0009:
                return data[80:].split(b'\0')[0].decode(errors='replace')
    raise RuntimeError('No world response')


def locked_zones(sock):
    sock.sendall(packet(0x002B, struct.pack('<B64sH', 0, b'keyless-door-operator', 0)))
    ids = set()
    for _ in range(100):
        message = emote(sock)
        row = re.fullmatch(r'Zone \d+ \| Name: .* \([a-zA-Z0-9_]+\) ID: (\d+)', message)
        if row:
            ids.add(int(row[1]))
        if 'zones locked.' in message.lower() or 'zones are locked.' in message.lower():
            return ids
    raise RuntimeError('No complete zone lock list')


def change_hold(sock, hold, expected_locks):
    before = locked_zones(sock)
    assert before == set(expected_locks), 'Native lock list changed'
    assert (75 in before) != hold, 'Unexpected Paineel lock preimage'
    sock.sendall(packet(0x002B, struct.pack('<B64sH', 1 if hold else 2, b'keyless-door-operator', 75)))
    # Success broadcasts target loaded zones, not this status-only connection.
    # An ordered explicit List request provides the authoritative acknowledgment.
    after = locked_zones(sock)
    assert after == (before | {75} if hold else before - {75})
    return {'held': hold, 'zone_id':75, 'other_locks_preserved':True,
            'before': sorted(before), 'after': sorted(after)}


def execute(affected, mode, expected_targets=None, expected_locks=None):
    assert mode in ('probe', 'reload', 'hold', 'release')
    cfg = json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
    assert cfg['tcp'] == {'ip': '127.0.0.1', 'port': '9001'}
    key = cfg['key'].encode()
    assert key and b'\0' not in key
    with socket.create_connection(('127.0.0.1', 9001), timeout=5) as sock:
        sock.sendall(frame(4, b'Zone\0' + key + b'\0') +
                     packet(0x0007, struct.pack('<64sh', b'keyless-door-operator', 255)))
        message = ''
        for _ in range(50):
            length, kind = struct.unpack('<IB', read_exact(sock, 5))
            assert length < 1024 * 1024
            data = read_exact(sock, length)
            if kind != 5 or len(data) < 6:
                continue
            size, opcode = struct.unpack('<IH', data[:6])
            assert size == len(data) - 6
            if opcode == 0x0009:
                message += data[6 + 74:].split(b'\0')[0].decode(errors='replace')
                if 'zones available.' in message:
                    message = message.split('zones available.', 1)[0] + 'zones available.'
                    assert '\ufffd' not in message, 'Malformed world status'
                    break
        else:
            raise RuntimeError('Incomplete world status')
        rows = inspect_workers(parse_status(message))
        targets = selected(rows, affected)
        if mode in ('hold','release'):
            return change_hold(sock, mode == 'hold', expected_locks)
        if mode == 'reload':
            assert 75 in locked_zones(sock), 'Paineel admission hold is absent'
            actual = sorted((r['server_id'], r['pid'], r['zone']) for r in targets)
            assert actual == sorted(map(tuple, expected_targets)), 'Affected worker identity changed'
            for row in targets:
                request = struct.pack('<i?3xqiI', 8, True, 0, 0, row['server_id'])
                sock.sendall(packet(0x4100, request))
        return {'workers': rows, 'targets': targets, 'request_sent': mode == 'reload',
                'locks': sorted(locked_zones(sock))}


if __name__ == '__main__':
    print(json.dumps(execute(AFFECTED, MODE, globals().get('EXPECTED_TARGETS'),
                             globals().get('EXPECTED_LOCKS'))))
