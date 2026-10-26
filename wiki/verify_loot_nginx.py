"""Verify compressed-only JSON routes in two offline local Docker containers."""
import gzip,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/wiki-loot/nginx-fixture'
CLIENT=r'''
import gzip,hashlib,json
from urllib.request import Request,urlopen
from urllib.error import HTTPError
expected=(json.dumps({'schema':1,'text':'fixture '*1000})+'\n').encode()
def get(path,encoding='identity',method='GET'):
 try:r=urlopen(Request('http://127.0.0.1:18999'+path,headers={'Accept-Encoding':encoding},method=method),timeout=10)
 except HTTPError as e:r=e
 with r:return r.status,dict(r.headers),r.read()
for encoding in ['identity','gzip']:
 for path in ['/loot-data/current/index.json','/loot-data/aaaaaaaaaaaaaaaa/item-1.json']:
  status,headers,body=get(path,encoding)
  assert status==200,(status,path)
  if headers.get('Content-Encoding')=='gzip':body=gzip.decompress(body)
  assert body==expected
  assert headers.get('Content-Type')=='application/json',headers
  assert headers.get('X-Content-Type-Options')=='nosniff'
for path in ['/loot-data/current/item-1.json','/loot-data/current/index.json.gz','/loot-data/current/.manifest.json','/loot-data/aaaaaaaaaaaaaaaa/item-0.json']:
 assert get(path)[0]==404,path
assert get('/loot-data/current/index.json',method='POST')[0]==403
print(json.dumps({'status':'PASS','checks':['identity/gzip decoded hashes match','immutable item path','JSON type and nosniff','raw gz/manifest/current item/invalid id denied','POST denied']}))
'''

def main():
 OUT.mkdir(exist_ok=True)
 packed=gzip.compress((json.dumps({'schema':1,'text':'fixture '*1000})+'\n').encode(),mtime=0)
 for directory in ['current','a'*16]:
  target=OUT/'data'/directory;target.mkdir(parents=True,exist_ok=True)
  for name in ['index.json','item-1.json']:(target/(name+'.gz')).write_bytes(packed)
 fragment=(ROOT/'wiki/loot-nginx.conf').read_text().replace('/srv/public/wiki-data/','/fixture/data/')
 (OUT/'nginx.conf').write_text('error_log stderr; pid /tmp/nginx-test.pid; events {} http { server { listen 127.0.0.1:18999; add_header X-Content-Type-Options nosniff always; '+fragment+' location / { return 404; } } }')
 container=subprocess.check_output(['docker','run','--rm','-d','--network','none','--mount',f'type=bind,source={OUT},target=/fixture,readonly','--entrypoint','nginx','akk-stack-peq-editor-proxy:latest','-c','/fixture/nginx.conf','-g','daemon off;'],text=True).strip()
 try:
  result=subprocess.run(['docker','run','--rm','-i','--network','container:'+container,'--entrypoint','python3','eqemulator/eqemu-server:v16','-B','-'],input=CLIENT.encode(),capture_output=True,timeout=30)
  if result.returncode:raise RuntimeError(result.stderr.decode())
  report=json.loads(result.stdout);(OUT.parent/'nginx-integration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 finally:subprocess.run(['docker','stop',container],check=True,capture_output=True)
if __name__=='__main__':main()
