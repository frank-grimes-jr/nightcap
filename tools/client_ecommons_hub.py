"""Build EC hub client data from read-only inputs and the approved placement plan."""
import hashlib,json,math
from pathlib import Path
from client_hub_models import add_models

ROOT=Path(__file__).resolve().parents[1]
PINNED={
 'poknowledge_obj.s3d':'de46dd2bdb55daac2e559148f62d83108da2697bb7c0079edd4c8ec09ee7a9e1',
 'nektulos.s3d':'6cfb7612bfe2703242add44d7cff285a37e08423df8082fffe10ce3dd84c7f21',
 'nektulos_obj.s3d':'980717cdf70834429ed9667c14321a93f15aa38f78e331e8b6a15938f626969c'}

def recall_spell(raw,arrival):
 lines=raw.decode('latin1').splitlines(keepends=True)
 templates=[line.rstrip('\r\n').split('^') for line in lines if line.startswith('3134^')]
 if len(templates)!=1:raise ValueError('Missing or duplicate teleport template')
 f=templates[0]
 if len(f)!=237 or f[86:98]!=['83']+['254']*11 or f[16:18]!=['0','0'] or f[98]!='6':raise ValueError('Unsupported teleport template')
 f[0:2]=['42604','Ancient Attunement'];f[3]='ecommons';f[13:16]=['5000','1500','600000']
 f[20:24]=[str(int(arrival['y'])),str(int(arrival['x'])),str(math.ceil(arrival['z'])),str(int(arrival['heading']))]
 f[104:120]=['255']*16
 expected='^'.join(f)
 existing=[l.rstrip('\r\n') for l in lines if l.startswith('42604^')]
 if existing:
  if existing!=[expected]:raise ValueError('Client recall spell ID collision')
  return raw
 ending='\r\n' if b'\r\n' in raw else '\n'
 return raw+(b'' if raw.endswith(b'\n') else ending.encode())+(expected+ending).encode('latin1')

def recall_strings(raw):
 wanted={('22200','1'):'Ancient Attunement',('22200','2'):'Nightcap Recall',('22200','4'):'Return to the East Commonlands tunnel hub. Cast time: 5 seconds. Reuse: 10 minutes. Your bind point is unchanged.'}
 seen=set()
 for line in raw.decode('latin1').splitlines():
  f=line.split('^');key=tuple(f[:2])
  if key in wanted:
   if key in seen or f[2:]!=[wanted[key],'0']:raise ValueError('Recall string ID collision')
   seen.add(key)
 ending=b'\r\n' if b'\r\n' in raw else b'\n'
 out=raw+(b'' if raw.endswith(b'\n') else ending)
 for key,text in wanted.items():
  if key not in seen:out+=('^'.join((*key,text,'0'))).encode('latin1')+ending
 return out

def hub_files(client,plan=None):
 if plan is None:plan=json.loads((ROOT/'docs/ecommons-hub/plan.json').read_bytes())
 files={'ecommons_chr.txt':add_models((client/'ecommons_chr.txt').read_bytes()),'dbstr_us.txt':recall_strings((client/'dbstr_us.txt').read_bytes())}
 imports=(client/'ecommons_assets.txt').read_bytes() if (client/'ecommons_assets.txt').exists() else b''
 tokens=imports.decode('ascii').split()
 if any('/' in t or '\\' in t or '.' in t for t in tokens):raise ValueError('Unsupported zone object import token')
 if 'poknowledge_obj' not in tokens:tokens.append('poknowledge_obj')
 files['ecommons_assets.txt']=('\n'.join(tokens)+'\n').encode('ascii')
 for name,sha in PINNED.items():
  data=(client/name).read_bytes()
  if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('Unsupported zone archive: '+name)
  files[name]=data
 labels=[]
 for ident,p in plan['services'].items():
  name='Class_'+str(int(ident)-997899) if int(ident)<998000 else {'999220':'Class_Guide','999225':'Bags','999226':'Epic_Forge','999237':'Restora','999238':'Goldwind','999239':'Waypoints'}[ident]
  labels.append(f"P {-p['x']}, {-p['y']}, {p['z']}, 255, 220, 0, 2, Nightcap_{name}")
 for p in plan['doors']:
  if p['zone']=='ecommons':labels.append(f"P {-p['pos_x']}, {-p['pos_y']}, 0, 0, 255, 255, 2, Nightcap_To_{p['dest_zone']}")
 name='maps/ecommons_3.txt';existing=(client/name).read_bytes() if (client/name).exists() else b''
 # Retain all pre-existing map lines; deduplicate only our exact generated labels.
 additions=[l for l in labels if l.encode('ascii') not in existing.splitlines()]
 files[name]=existing+(b'\n' if existing and not existing.endswith(b'\n') else b'')+(('\n'.join(additions)+'\n').encode('ascii') if additions else b'')
 return files
