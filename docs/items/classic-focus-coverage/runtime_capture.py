"""Read current production NPC/rule/cache pins for the isolated pressure fixture."""
import json
from capture import CODE,remote,HERE,ROOT
old=json.loads((ROOT/'docs/combat/fast-healing/input.json').read_bytes())['rules']
names=','.join(repr(r[0]) for r in old)
code=CODE.split('pairs=[')[0]+'''
game=o.r.compact('game')
channel=json.loads(base64.b64decode(json.loads((o.ROOT/'data/public/channel.json').read_bytes())['manifest']))
receipt=Path('/opt/nightcap/releases/titles-live-20261114-v1/evidence/activation/deployed.json')
out=dict(npcs=table('npc_types','id IN (63009,66011,32002,73057)'),rules=rows(RULES),
 image=game['image_id'],game=game,binaries={k[4:]:v for k,v in o.r.image_hashes(game['image_id']).items() if k.startswith('bin/')},
 caches=o.h.caches(),channel=o.sha(o.ROOT/'data/public/channel.json'),client=channel['release'],stock_operator=o.sha(p),
 titles_receipt=o.sha(receipt),players=o.a.prior.players(),wiki=str((o.ROOT/'data/public/wiki/current').readlink()))
print(json.dumps(out))
'''
if __name__=='__main__':
    q='SELECT JSON_ARRAY(rule_name,rule_value) FROM rule_values WHERE ruleset_id=1 AND rule_name IN ('+names+') ORDER BY rule_name'
    d=json.loads(remote('RULES='+repr(q)+'\n'+code,timeout=180));(HERE/'runtime.json').write_text(json.dumps(d,indent=2)+'\n')
    data=json.loads((HERE/'input.json').read_bytes());data['rules']=d['rules'];(HERE/'input.json').write_text(json.dumps(data,indent=2)+'\n')
    print({k:d[k] for k in ('players','client','caches','wiki')});print('rules',len(d['rules']))
