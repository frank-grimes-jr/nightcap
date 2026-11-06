"""Run only inside game; expose counts/lock state, never credentials or identities."""
import json
from pathlib import Path
import socket
import struct
import sys

method = 'EQW::GetPlayerCount'
cfg = json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp'] == {'ip': '127.0.0.1', 'port': '9001'}

def frame(kind, body):
    return struct.pack('<IB', len(body), kind) + body

with socket.create_connection(('127.0.0.1', 9001), timeout=5) as connection:
    connection.sendall(frame(4, b'WebInterface\0' + cfg['key'].encode() + b'\0'))
    body = json.dumps({'method': method, 'id': 'waypoint-release'}).encode() + b'\0'
    connection.sendall(frame(5, struct.pack('<IH', len(body), 0x002f) + body))

    def receive(size):
        result = bytearray()
        while len(result) < size:
            chunk = connection.recv(size - len(result))
            if not chunk:
                raise RuntimeError('World closed control connection')
            result.extend(chunk)
        return bytes(result)

    for _ in range(10):
        size, kind = struct.unpack('<IB', receive(5))
        assert size <= 65536, 'Unexpected control frame size'
        packet = receive(size)
        if kind != 5:
            continue
        length, opcode = struct.unpack('<IH', packet[:6])
        assert length == len(packet) - 6
        if opcode != 0x002f:
            continue
        result = json.loads(packet[6:].rstrip(b'\0'))
        assert result.get('id') == 'waypoint-release' and 'error' not in result
        print(json.dumps(result['response']))
        break
    else:
        raise RuntimeError('No matching world control response')
