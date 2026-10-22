import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
HERE=Path(__file__).resolve().parent
MANIFEST=Path('E:/EQ_Local_Dev/artifacts/aa-pacing-million-20261021/guide20261021-aa-million-v1.tar.json')
def main():
    expected=json.loads(MANIFEST.read_text())
    assert len(expected)==5
    size=0
    for name,digest in expected.items():
        route='/' if name=='index.html' else '/'+name
        req=Request('https://play.nightcapgame.org'+route,headers={'User-Agent':'NightcapLauncher/0.6.0','Accept-Encoding':'identity'})
        with urlopen(req,timeout=45) as response:
            body=response.read();size+=len(body)
            assert response.status==200 and hashlib.sha256(body).hexdigest()==digest,name
            assert response.headers.get('X-Content-Type-Options')=='nosniff',name
            assert "default-src 'none'" in response.headers.get('Content-Security-Policy',''),name
            assert {'private','no-store','no-transform'} <= set(response.headers.get('Cache-Control','').replace(' ','').split(',')),name
    result={'result':'PASS','release':'20261021-aa-million-guide-v1','verified_files':5,'verified_bytes':size,'sha256_and_headers':True,'verified_at':datetime.now(timezone.utc).isoformat()}
    (HERE/'guide-public-verification.json').write_text(json.dumps(result,indent=2)+chr(10))
    print(json.dumps(result))
if __name__=='__main__':main()
