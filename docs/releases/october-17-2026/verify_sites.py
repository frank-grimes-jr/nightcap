"""Verify exact published bytes and response policies; no site mutation."""
import argparse,concurrent.futures,hashlib,json,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['wiki','guide']);p.add_argument('manifest',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    origin='https://wiki.nightcapgame.org' if args.kind=='wiki' else 'https://play.nightcapgame.org'
    def check(pair):
        name,expected=pair;assert not name.startswith('/') and '..' not in Path(name).parts
        route='/' if args.kind=='guide' and name=='index.html' else '/'+name
        request=Request(origin+route,headers={'User-Agent':'NightcapLauncher/0.6.0','Accept-Encoding':'identity'})
        with urlopen(request,timeout=60) as response:
            assert response.status==200
            assert response.headers.get('X-Content-Type-Options')=='nosniff'
            policy=response.headers.get('Content-Security-Policy','')
            assert ("script-src 'self'" if args.kind=='wiki' else "default-src 'none'") in policy
            if args.kind=='guide':assert {'private','no-store','no-transform'} <= set(response.headers.get('Cache-Control','').replace(' ','').split(','))
            digest=hashlib.sha256();size=0
            for chunk in iter(lambda:response.read(65536),b''):digest.update(chunk);size+=len(chunk)
            assert digest.hexdigest()==expected,name
            return size
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:sizes=list(pool.map(check,manifest.items()))
    if args.kind=='wiki':
        for name in ['.env','channel.json','guide.html','content-review.json','articles/multiclass.json']:
            try:
                with urlopen(Request(origin+'/'+name,headers={'User-Agent':'NightcapLauncher/0.6.0'}),timeout=30) as response:status=response.status
            except HTTPError as error:status=error.code;error.close()
            assert status==404,(name,status)
    result={'result':'PASS','kind':args.kind,'origin':origin,'verified_files':len(sizes),'verified_bytes':sum(sizes),'headers':'verified','verified_at_unix':int(time.time())}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
