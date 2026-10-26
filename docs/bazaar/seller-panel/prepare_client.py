"""Stage local assets against the current public inventory. Does not sign or publish."""
import base64,hashlib,json,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from client_gameplay_assets import ui_xml
CLIENT=Path('E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2')
OUT=ROOT/'docs/bazaar/private/seller-panel/client-v2'
BASE='0cc3708d19d663e20d56d579324afe4e85586930ef6cbadaa95b5032cdaac167'
sha=lambda b:hashlib.sha256(b).hexdigest()
def get(url,limit):
 if not url.startswith('https://play.nightcapgame.org/'):raise ValueError('Unexpected origin')
 request=urllib.request.Request(url,headers={'User-Agent':'NightcapLauncher/0.6.0','Accept-Encoding':'identity'})
 with urllib.request.urlopen(request,timeout=45) as response:
  if not response.geturl().startswith('https://play.nightcapgame.org/'):raise ValueError('Unexpected redirect')
  data=response.read(limit+1)
 if len(data)>limit:raise ValueError('Oversized response')
 return data
def main():
 channel=get('https://play.nightcapgame.org/channel.json',2*1024*1024)
 assert sha(channel)==BASE,'Public baseline changed; reconcile before staging'
 manifest=json.loads(base64.b64decode(json.loads(channel)['manifest']))
 assert manifest['release']==2026102402 and len(manifest['files'])==140
 assert sha((CLIENT/'eqgame.exe').read_bytes())=='2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e'
 raw=(CLIENT/'uifiles/default/EQUI_BazaarSearchWnd.xml').read_bytes()
 assert sha(raw)=='98f4e1259dc4a5ef36bcb1bd24abc24503c5e1d1b0c262d1acb439b484b6ff00'
 assets={'dinput8.dll':(ROOT/'eq-client-dll/build/dinput8.dll').read_bytes(),
 'nightcap-patch-sites.json':(ROOT/'eq-client-dll/config/patch-sites.json').read_bytes(),
 'nightcap-patches.cfg':(ROOT/'eq-client-dll/config/nightcap-patches.cfg').read_bytes(),
 'uifiles/nightcap/equi_bazaarsearchwnd.xml':ui_xml(raw,'bazaar')}
 OUT.mkdir(parents=True,exist_ok=False)
 (OUT/'baseline-channel.json').write_bytes(channel)
 for name,data in assets.items():
  target=OUT/'assets'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 retained=[];replaced=[]
 for old in manifest['files']:
  if old['path'] in assets:
   data=get(old['url'],old['size']);assert len(data)==old['size'] and sha(data)==old['sha256']
   target=OUT/'baseline'/old['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);replaced.append(old['path'])
  else:retained.append(old)
 assert len(retained)==137 and len(replaced)==3
 report={'status':'unsigned local candidate; signature/runtime checks required','baseline_release':manifest['release'],
 'baseline_channel_sha256':BASE,'assets':{n:{'sha256':sha(b),'size':len(b)} for n,b in assets.items()},
 'retained_descriptors':retained,'retained_patch_notes':manifest['patch_notes'],'retained_tombstones':manifest.get('tombstones',[]),
 'replaced':replaced,'added':['uifiles/nightcap/equi_bazaarsearchwnd.xml'],'complete_inventory_count':141,
 'published':False,'native_rendered':False}
 (OUT/'candidate.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('retained_descriptors','retained_patch_notes','retained_tombstones')}))
if __name__=='__main__':main()
