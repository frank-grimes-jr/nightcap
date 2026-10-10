#!/usr/bin/env python3
"""Exercise the built gateway with disposable credentials and a UDP echo target.

Run inside a disposable container with --network none, never in a host namespace.
The only game target is this script's loopback echo socket, not the live game.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import secrets
import socket
import struct
import subprocess
import tempfile
import threading
import time

import player_access as access


def connect(token, ip):
    sock = socket.create_connection(('127.0.0.1', 8080), timeout=4)
    headers = [
        'GET /connect HTTP/1.1', 'Host: play.nightcapgame.org',
        'Connection: Upgrade', 'Upgrade: websocket', 'Sec-WebSocket-Version: 13',
        'Sec-WebSocket-Key: ' + base64.b64encode(secrets.token_bytes(16)).decode(),
        'CF-Connecting-IP: ' + ip,
    ]
    if token:
        headers.append('Authorization: Bearer ' + token)
    sock.sendall(('\r\n'.join(headers) + '\r\n\r\n').encode('ascii'))
    response = b''
    while b'\r\n\r\n' not in response:
        response += sock.recv(1)
        assert len(response) < 8192, 'Unbounded response headers'
    status = int(response.split(b' ', 2)[1])
    return sock, status


def exchange(sock, payload):
    packet = struct.pack('!HI', 5998, 1) + payload
    mask = secrets.token_bytes(4)
    sock.sendall(bytes((0x82, 0x80 | len(packet))) + mask + bytes(v ^ mask[i % 4] for i, v in enumerate(packet)))
    header = sock.recv(2, socket.MSG_WAITALL)
    assert header == bytes((0x82, len(packet))), 'Unexpected relay frame'
    assert sock.recv(len(packet), socket.MSG_WAITALL) == packet, 'UDP relay payload mismatch'


def require_closed(sock):
    sock.settimeout(5)
    assert sock.recv(1) == b'', 'Revoked or invalid registry session survived'
    sock.close()


def run(binary):
    # Network isolation is independently enforced by the parent Docker command.
    with tempfile.TemporaryDirectory(prefix='player-access-') as temp:
        root = Path(temp)
        registry = root / 'registry' / 'credentials.json'
        access.initialize(registry, os.getgid())
        joe = access.issue(registry, 'joe-test', root / 'joe.txt')
        access.issue(registry, 'owner-test', root / 'owner.txt')
        token = (root / 'joe.txt').read_text().strip()
        owner = (root / 'owner.txt').read_text().strip()
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind(('127.0.0.1', 5998))
        udp.settimeout(0.2)
        stopped = threading.Event()

        def echo():
            while not stopped.is_set():
                try:
                    data, sender = udp.recvfrom(65535)
                    udp.sendto(data, sender)
                except socket.timeout:
                    continue

        worker = threading.Thread(target=echo)
        worker.start()
        process = subprocess.Popen([binary], env={**os.environ, 'GAME_TARGET': '127.0.0.1', 'TRUSTED_PROXIES': '127.0.0.1/32', 'PLAYER_ACCESS_FILE': str(registry), 'DENY_CIDRS': ''}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            deadline = time.monotonic() + 10
            while True:
                try:
                    s, status = connect('', '198.51.100.10')
                    s.close()
                    assert status == 401, 'Unauthenticated player admitted'
                    break
                except ConnectionRefusedError:
                    assert process.poll() is None and time.monotonic() < deadline, 'Gateway did not start'
                    time.sleep(0.05)
            sockets = []
            for ip in ('198.51.100.10', '203.0.113.27', '2001:db8:1::77', '2001:db8:2::99'):
                s, status = connect(token, ip)
                assert status == 101, 'Credential rejected after address change'
                sockets.append(s)
                exchange(s, b'isolated-game-datagram')
            unaffected, status = connect(owner, '203.0.113.27')
            assert status == 101
            before_pid = process.pid
            access.revoke(registry, joe['id'])
            for s in sockets:
                require_closed(s)
            s, status = connect(token, '198.51.100.10')
            s.close()
            assert status == 401, 'Revoked reconnect admitted'
            exchange(unaffected, b'other-player-remains-connected')
            valid = registry.read_bytes()
            registry.write_text('{bad')
            require_closed(unaffected)
            s, status = connect(owner, '2001:db8::1')
            s.close()
            assert status == 401, 'Invalid registry failed open'
            registry.write_bytes(valid)
            deadline = time.monotonic() + 5
            while True:
                s, status = connect(owner, '2001:db8:999::1')
                if status == 101:
                    exchange(s, b'registry-recovered')
                    s.close()
                    break
                s.close()
                assert time.monotonic() < deadline, 'Registry did not recover'
                time.sleep(0.05)
            assert process.poll() is None and process.pid == before_pid, 'Gateway restarted during revocation'
            return {'ipv4_and_ipv6_changes': True, 'actual_udp_roundtrip': True, 'live_revocation': True, 'other_player_preserved': True, 'invalid_registry_fail_closed': True, 'registry_recovery_without_restart': True}
        finally:
            process.terminate()
            logs, _ = process.communicate(timeout=10)
            stopped.set()
            worker.join(timeout=2)
            udp.close()
            assert token not in logs and owner not in logs, 'Credential leaked into gateway logs'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    print(json.dumps(run(parser.parse_args().binary), indent=2))
