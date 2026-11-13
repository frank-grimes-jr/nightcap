"""Verify all published Inventory wiki hashes, security headers and private denials."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from inventory_release_support import HERE,ART,save
from prepare_inventory_wiki import RELEASE


def get(name):
    url='https://wiki.nightcapgame.org/'+urllib.parse.quote(name,safe='/')
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'NightcapLauncher/0.7.0','Accept-Encoding':'identity'}),timeout=60)


def verify(row):
    name,pin=row
    with get(name) as response:
        assert response.status==200 and urllib.parse.urlsplit(response.url).hostname=='wiki.nightcapgame.org',name
        assert response.headers.get('X-Content-Type-Options')=='nosniff',name
        assert "script-src 'self'" in response.headers.get('Content-Security-Policy',''),name
        data=response.read(32*1024**2)
        assert hashlib.sha256(data).hexdigest()==pin,name
        return len(data)


def main():
    pins=json.loads((ART/(RELEASE+'.tar.json')).read_text());assert len(pins)==614
    with ThreadPoolExecutor(max_workers=8) as pool:counts=list(pool.map(verify,pins.items()))
    denials={}
    for name in ('README.md','content-review.json','articles/equipment.json','catalog.json','.git/config'):
        try:
            with get(name) as response:code=response.status
        except urllib.error.HTTPError as e:code=e.code
        assert code in (403,404),(name,code);denials[name]=code
    result={'status':'PASS','release':RELEASE,'canonical_https_hashes':len(pins),'verified_bytes':sum(counts),
        'security_headers':True,'private_denials':denials,'native_visual_acceptance':'OPEN'}
    save(HERE/'wiki-public-verification.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
