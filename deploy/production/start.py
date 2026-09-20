"""Private runtime supervisor. No SSH, public login lookup, updater or web admin."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

BIN = Path('/opt/nightcap/bin')


def validate_native():
    """Refuse the old binary/new-quest combination before accepting players."""
    world, zone = (BIN/'world').read_bytes(), (BIN/'zone').read_bytes()
    if not world.startswith(b'\x7fELF') or not zone.startswith(b'\x7fELF'):
        raise ValueError('Native runtime must contain the reviewed Linux ELF pair')
    if b'CALL nightcap_market_rotate({},{},{})\x00' not in world or b'CALL nightcap_market_rotate({})\x00' in world:
        raise ValueError('World lacks the current economy startup contract')
    for marker in (b'LivingEconomy\x00', b'MarketAnnouncement\x00', b'_Z9Perl__oocPKc',
                   b'Your selected classes cannot cast this spell at your current level.'):
        if marker not in zone:
            raise ValueError('Zone lacks a required production quest/spell contract')

def validate():
    if 'LSPX' in os.environ:
        raise ValueError('LSPX must be absent, even an empty value enables public lookup')
    cfg = json.loads(Path('eqemu_config.json').read_text())['server']
    login = json.loads(Path('login.json').read_text())
    world = cfg['world']
    checks = [
        world['address'] == world['localaddress'] == cfg['ucs']['host'] == '127.77.0.1',
        world['loginserver']['host'] == '127.0.0.1' and str(world['loginserver']['legacy']) == '0',
        [k for k in world if k.startswith('loginserver')] == ['loginserver'],
        cfg['zones']['ports'] == {'low': '7000', 'high': '7030'},
        str(cfg['zones']['defaultstatus']) == '0',
        str(cfg['ucs']['port']) == '7778',
        world['tcp'] == {'ip':'127.0.0.1','port':'9001'},
        world['telnet']['enabled'] == 'false' and world['telnet']['ip'] == '127.0.0.1',
        world['http']['enabled'] == 'false',
        cfg['auto_database_updates'] == 'false',
        str(world['loginserver']['port']) == '5998',
        login['general']['listen_port'] == login['client_configuration']['titanium_port'] == 5998,
        login['security'] == {'mode': 14, 'allow_token_login': False},
        login['account']['auto_create_accounts'] is False,
        login['worldservers']['unregistered_allowed'] is False,
        login['web_api']['enabled'] is False,
        login['general']['default_loginserver_name'] == 'local',
    ]
    if not all(checks):
        raise ValueError('Private runtime configuration drift; refusing startup')

def health():
    # UDP listeners plus the world interserver TCP socket. This proves processes
    # are listening, not successful native account login (a separate launch gate).
    ports = set()
    for line in Path('/proc/net/udp').read_text().splitlines()[1:]:
        ports.add(int(line.split()[1].split(':')[1], 16))
    if not {5998, 9000, 7778}.issubset(ports):
        raise RuntimeError('native listeners not ready')
    with socket.create_connection(('127.0.0.1', 9001), timeout=2):
        pass

def main():
    validate()
    if sys.argv[1:] == ['--health']:
        health()
        return
    validate_native()
    subprocess.run([str(BIN/'loginserver'), '--nightcap-crypto-self-test'], check=True)
    for path in ('logs', 'shared'):
        Path(path).mkdir(exist_ok=True)
    subprocess.run([str(BIN/'shared_memory')], check=True)
    children = []
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for name in ('loginserver', 'world'):
            children.append(subprocess.Popen([str(BIN/name)]))
        # Zone clients retry world connectivity; the healthcheck gates gateway start.
        children.append(subprocess.Popen([str(BIN/'ucs')]))
        workers = int(os.environ.get('NIGHTCAP_ZONE_WORKERS', '12'))
        if not 1 <= workers <= 31:
            raise ValueError('zone worker count must be between 1 and 31')
        for _ in range(workers):
            children.append(subprocess.Popen([str(BIN/'zone')]))
        while not stopping:
            if any(p.poll() is not None for p in children):
                raise RuntimeError('a native process exited; restarting the complete runtime')
            time.sleep(1)
    finally:
        for p in children:
            if p.poll() is None:
                p.terminate()
        deadline = time.monotonic() + 75
        for p in children:
            try:
                p.wait(timeout=max(0.1, deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()

if __name__ == '__main__':
    main()
