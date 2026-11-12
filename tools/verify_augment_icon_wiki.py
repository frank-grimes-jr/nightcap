"""Verify every canonical public hash, security headers and private denials."""
import json
from pathlib import Path
from augment_icon_remote import run

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,urllib.error,urllib.request
root='https://wiki.nightcapgame.org/'
manifest=json.loads(Path('/opt/nightcap/releases/wiki-augment-icons-20261112-v1/20261112-augment-icons-v1.tar.json').read_text())
def verify(pair):
 name,pin=pair;assert not name.startswith('/') and '..' not in Path(name).parts
 url=root+('' if name=='index.html' else name)
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Nightcap-release-verification'}),timeout=30) as response:
  assert response.status==200 and hashlib.sha256(response.read()).hexdigest()==pin,name
  assert response.headers.get('X-Content-Type-Options')=='nosniff',name
  assert response.headers.get('Content-Security-Policy') and response.headers.get('Referrer-Policy'),name
 return name
with ThreadPoolExecutor(max_workers=8) as pool:names=list(pool.map(verify,manifest.items()))
private={}
for path in ('/channel.json','/launcher-channel.json','/nightcap-friends.zip','/guide.html','/.env'):
 try:
  with urllib.request.urlopen(root.rstrip('/')+path,timeout=20) as response:status=response.status
 except urllib.error.HTTPError as error:status=error.code
 assert status in (403,404),(path,status)
 private[path]=status
print(json.dumps({'status':'PASS','release':'20261112-augment-icons-v1','files':len(names),
 'security_headers':True,'private_denials':private,'scope':'All613canonical HTTPS hashes;607retained files; no client/gameplay acceptance inferred'},indent=2))
'''

if __name__ == '__main__':
    result = run(REMOTE)
    (ROOT / 'docs/items/augment-icons-20261112/wiki-public-verification.json').write_text(result, encoding='utf-8')
    print(result, end='')
