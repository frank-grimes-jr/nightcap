"""Verify the complete published wiki and its public compressed JSON contract."""
import concurrent.futures,gzip,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[3]
ARTIFACTS=ROOT/'artifacts/wiki-loot'
RELEASE='20261022-loot-finder-v2'
HOST='https://wiki.nightcapgame.org/'

def probe(path,encoding='identity',method='GET'):
 request=Request(HOST+path,headers={'User-Agent':'NightcapLauncher/0.6.0','Accept-Encoding':encoding,'Cache-Control':'no-cache'},method=method)
 try:response=urlopen(request,timeout=45)
 except HTTPError as error:response=error
 with response:
  if not response.url.startswith(HOST):raise ValueError('Unexpected redirected host')
  body=response.read();headers=response.headers
  if headers.get('Content-Encoding')=='gzip':body=gzip.decompress(body)
  return response.status,body,headers

def policy(headers):
 assert headers.get('X-Content-Type-Options')=='nosniff'
 assert "script-src 'self'" in headers.get('Content-Security-Policy','')

def main():
 manifest=json.loads((ARTIFACTS/(RELEASE+'.tar.json')).read_text())
 def verify(entry):
  path,digest=entry;status,body,headers=probe(path+'?verify='+RELEASE)
  assert status==200 and hashlib.sha256(body).hexdigest()==digest,(path,status)
  policy(headers);return path
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:files=list(pool.map(verify,manifest.items()))
 denied=['.env','articles/loot-finder.json','content-review.json','catalog.json','wiki/current/index.html','loot-data/current/item-1.json','loot-data/current/index.json.gz','loot-data/current/.manifest.json','loot-data/current/content.json.gz']
 for path in denied:assert probe(path)[0]==404,path
 status,body,headers=probe('loot-data/current/index.json?verify='+RELEASE);assert status==200;policy(headers);index=json.loads(body)
 assert index['schema']==1 and len(index['items'])>0
 base=index['base_url'].lstrip('/');itempath=base+'item-1365.json'
 a=probe(itempath,'identity');b=probe(itempath,'gzip')
 assert a[0]==b[0]==200 and a[1]==b[1];policy(a[2]);policy(b[2])
 assert a[2]['Content-Type'].split(';')[0]=='application/json'
 item=json.loads(a[1]);assert item['id']==1365 and item['sources']
 assert probe('loot-data/current/index.json',method='POST')[0] in (403,405)
 result={'result':'PASS','release':RELEASE,'verified_at':datetime.now(timezone.utc).isoformat(),'static_files':len(files),'hashes_and_security_headers':True,'private_routes_denied':denied,'snapshot':index['snapshot'],'captured_at':index['captured_at'],'items':len(index['items']),'era':index['era_name'],'identity_gzip_json_match':True,'fbss':{'id':item['id'],'sources':item['sources']}}
 (ARTIFACTS/'wiki-public-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='fbss'},indent=2))
if __name__=='__main__':main()
