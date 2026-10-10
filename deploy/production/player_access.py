#!/usr/bin/env python3
"""Operator-only player credential lifecycle. Never prints access secrets.

Run on the OVH host, outside containers. Registry directory is mounted read-only
by gateway so atomic replacement and revocation do not require a restart.
"""
import argparse
import base64
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import tempfile

MAX_BYTES = 2 << 20
LABEL = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
HEX_ID = re.compile(r"[a-f0-9]{32}\Z")
HEX_HASH = re.compile(r"[a-f0-9]{64}\Z")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def read_registry(path):
    with path.open('rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Registry is not a regular file')
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Registry is too large')
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != {'version', 'credentials'} or type(data['version']) is not int or data['version'] != 1:
        raise ValueError('Registry schema is invalid')
    records = data['credentials']
    if not isinstance(records, list) or len(records) > 10000:
        raise ValueError('Registry credential count is invalid')
    ids = set()
    for row in records:
        if not isinstance(row, dict) or set(row) != {'id', 'player', 'secret_hash', 'created'} or not all(isinstance(v, str) for v in row.values()):
            raise ValueError('Credential record is invalid')
        if not HEX_ID.fullmatch(row['id']) or not HEX_HASH.fullmatch(row['secret_hash']) or not LABEL.fullmatch(row['player']) or row['id'] in ids:
            raise ValueError('Credential identity is invalid or duplicated')
        datetime.datetime.strptime(row['created'], '%Y-%m-%dT%H:%M:%SZ')
        ids.add(row['id'])
    return data


@contextlib.contextmanager
def locked(path):
    flags = os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path.with_suffix('.lock'), flags, 0o600)
    try:
        if os.name == 'nt':
            import msvcrt
            if os.fstat(fd).st_size == 0:
                os.write(fd, b'0')
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def private_file(path, data, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, 'wb') as out:
        out.write(data)
        out.flush()
        os.fsync(out.fileno())


def initialize(path, gid):
    path.parent.mkdir(mode=0o750, parents=False, exist_ok=True)
    with locked(path):
        if os.name != 'nt':
            os.chown(path.parent, -1, gid)
            os.chmod(path.parent, 0o750)
        private_file(path, b'{"version":1,"credentials":[]}\n', 0o640)
        if os.name != 'nt':
            os.chown(path, -1, gid)
            os.chmod(path, 0o640)


def replace_registry(path, data):
    # Backups contain hashes, never delivery codes; keep them operator-only.
    backups = path.parent / '.backups'
    backups.mkdir(mode=0o700, exist_ok=True)
    private_file(backups / (now().replace(':', '') + '-' + secrets.token_hex(8) + '.json'), path.read_bytes())
    raw = (json.dumps(data, indent=2) + '\n').encode('utf-8')
    if len(raw) > MAX_BYTES:
        raise ValueError('Registry is too large')
    info = path.stat()
    fd, temp = tempfile.mkstemp(prefix='.registry-', dir=path.parent)
    try:
        if os.name != 'nt':
            os.fchown(fd, info.st_uid, info.st_gid)
            os.fchmod(fd, 0o640)
        with os.fdopen(fd, 'wb') as out:
            fd = -1
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
        if os.name != 'nt':
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if fd >= 0:
            os.close(fd)
        Path(temp).unlink(missing_ok=True)


def issue(path, player, output):
    if not LABEL.fullmatch(player):
        raise ValueError('Use a lowercase player label with letters, digits, hyphens or underscores')
    if output.resolve().is_relative_to(path.parent.resolve()):
        raise ValueError('Delivery files must be outside the gateway registry directory')
    with locked(path):
        data = read_registry(path)
        if len(data['credentials']) >= 10000:
            raise ValueError('Registry credential limit reached')
        credential_id = secrets.token_hex(16)
        token = 'nc1.' + credential_id + '.' + base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('ascii').rstrip('=')
        record = {'id': credential_id, 'player': player, 'secret_hash': hashlib.sha256(token.encode('ascii')).hexdigest(), 'created': now()}
        data['credentials'].append(record)
        private_file(output, (token + '\n').encode('ascii'))
        # If a write is interrupted, the operator can inspect the registry ID
        # and retained delivery file. Never delete the only copy of a secret on
        # an uncertain post-rename/fsync error.
        replace_registry(path, data)
        return {'id': credential_id, 'player': player, 'delivery_file': str(output), 'created': record['created']}


def revoke(path, credential_id):
    if not HEX_ID.fullmatch(credential_id):
        raise ValueError('Credential ID is invalid')
    with locked(path):
        data = read_registry(path)
        found = [r for r in data['credentials'] if r['id'] == credential_id]
        if len(found) != 1:
            raise ValueError('Credential ID was not found; no changes made')
        data['credentials'] = [r for r in data['credentials'] if r['id'] != credential_id]
        replace_registry(path, data)
        return {'revoked_id': credential_id, 'player': found[0]['player']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True, type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init')
    init.add_argument('--gateway-gid', type=int, default=65532)
    create = commands.add_parser('issue')
    create.add_argument('player')
    create.add_argument('--out', required=True, type=Path)
    remove = commands.add_parser('revoke')
    remove.add_argument('credential_id')
    commands.add_parser('list')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            initialize(args.registry, args.gateway_gid)
            result = {'initialized': str(args.registry)}
        elif args.command == 'issue':
            result = issue(args.registry, args.player, args.out)
        elif args.command == 'revoke':
            result = revoke(args.registry, args.credential_id)
        else:
            with locked(args.registry):
                result = [{k: r[k] for k in ('id', 'player', 'created')} for r in read_registry(args.registry)['credentials']]
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, TypeError):
        print('Player access operation failed; verify paths, permissions, registry integrity and arguments. No secrets were printed.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
