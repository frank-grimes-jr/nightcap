"""Read-only native zone status through the authenticated game loopback link.

No player port or loaded zone is
advertised. No mutating protocol messages are sent.
"""
import json
import re
import socket
import struct
import time
from pathlib import Path

cfg=json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp']=={'ip':'127.0.0.1','port':'9001'}
key=cfg['key'].encode()
assert key and b'\0' not in key
def frame(kind,payload):return struct.pack('<IB',len(payload),kind)+payload
def exact(sock,n):
    data=b''
    while len(data)<n:
        part=sock.recv(n-len(data))
        if not part:raise RuntimeError('World disconnected')
        data+=part
    return data
def send(sock,opcode,payload):
    sock.sendall(frame(5,struct.pack('<IH',len(payload),opcode)+payload))
def decode_status(payload):
    # Native fmt buffers can include stale bytes after the explicit summary.
    terminal=b'zones available.'
    end=payload.find(terminal)
    return (payload[:end+len(terminal)] if end>=0 else payload.rstrip(b'\0')).decode()
def parse_status(text):
    rows=[]
    for line in text.split('^'):
        m=re.fullmatch(r'#(\d+)\s+:: [DS] :: [^:]+:\d+\s+::\s*(\d+) :: .*? :: (.*?) :: \((\d+)\)',line)
        if m:rows.append(dict(server_id=int(m[1]),players=int(m[2]),zone=m[3],pid=int(m[4])))
    summaries=re.findall(r'(?:^|\^)(\d+) servers listed\. (\d+) servers online\.\^(\d+) zones are static zones, (\d+) zones are booted zones, (\d+) zones available\.$',text)
    assert len(summaries)==1,'Missing complete zone status summary'
    summary=summaries[0]
    assert int(summary[0])==int(summary[1])==len(rows),'Incomplete zone status'
    assert sum(map(int,summary[2:]))==len(rows),'Inconsistent zone status totals'
    assert len(rows)>=12 and len({r['server_id'] for r in rows})==len(rows),'Unrecognized zone status'
    return rows
def status(sock):
    send(sock,0x0007,struct.pack('<64sh',b'WaypointDeploy',255))
    text=''
    for _ in range(40):
        n,kind=struct.unpack('<IB',exact(sock,5))
        assert n<1024*1024
        data=exact(sock,n)
        if kind==5 and len(data)>=6:
            size,opcode=struct.unpack('<IH',data[:6])
            assert size==len(data)-6
            if opcode==9:
                text+=decode_status(data[6+74:])
                if 'zones available.' in text:break
    else:raise RuntimeError('Missing complete zone status')
    return parse_status(text)
with socket.create_connection(('127.0.0.1',9001),timeout=5) as sock:
    sock.sendall(frame(4,b'Zone\0'+key+b'\0'))
    before=status(sock)
print(json.dumps({'after':before}))
