"""Run inside the game container; use the configured authenticated world link.

Sends the same global Rules request as #reload rules global. Does not advertise
a client port, register a loaded zone, alter configuration, or stop processes.
"""
import json
import socket
import struct
from pathlib import Path

cfg = json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp'] == {'ip': '127.0.0.1', 'port': '9001'}
key = cfg['key'].encode()
assert key and b'\0' not in key

def frame(kind, payload):
    return struct.pack('<IB', len(payload), kind) + payload

def read_exact(sock, size):
    data = b''
    while len(data) < size:
        part = sock.recv(size-len(data))
        if not part:
            raise RuntimeError('World closed the authenticated connection')
        data += part
    return data

# ServerReload::Rules = 24; Request is the native Linux x64 24-byte struct.
request = struct.pack('<i?3xqiI', 24, False, 0, 0, 0)
assert len(request) == 24
message = struct.pack('<IH', len(request), 0x4100) + request
with socket.create_connection(('127.0.0.1', 9001), timeout=5) as sock:
    # One write: authenticate with the existing shared key, then request reload.
    sock.sendall(frame(4, b'Zone\0' + key + b'\0') + frame(5, message))
    for _ in range(20):
        length, kind = struct.unpack('<IB', read_exact(sock, 5))
        assert length < 1024*1024, 'Unexpected world frame size'
        payload = read_exact(sock, length)
        if kind != 5 or len(payload) < 6:
            continue
        size, opcode = struct.unpack('<IH', payload[:6])
        assert size == len(payload)-6
        if opcode == 0x4100:
            assert size == 24
            rule_type, needs_zone, when, option, zone_id = struct.unpack('<i?3xqiI', payload[6:])
            assert (rule_type, needs_zone, option, zone_id) == (24, False, 0, 0)
            print(json.dumps({'reload': 'Rules', 'global': True, 'world_broadcast_received': True}))
            break
    else:
        raise RuntimeError('No global Rules reload broadcast received')
