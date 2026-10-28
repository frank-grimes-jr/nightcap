"""Approved read-only public item/rule reference; no player/account queries."""
import json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REMOTE = r'''
import datetime, json, subprocess
from pathlib import Path
root=Path('/opt/nightcap/deploy/production')
def query(q):
    r=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq'],cwd=root,input='SET TRANSACTION READ ONLY; START TRANSACTION WITH CONSISTENT SNAPSHOT; '+q+' ROLLBACK;',capture_output=True,text=True,timeout=45)
    if r.returncode: raise RuntimeError(r.stderr[-800:])
    return [json.loads(x) for x in r.stdout.splitlines()]
fields=['id','Name','itemtype','damage','delay','classes','slots','reqlevel','reclevel','ac','hp','mana','endur','astr','asta','aagi','adex','awis','aint','acha','mr','fr','cr','pr','dr','accuracy','avoidance','shielding','strikethrough','attack','haste','regen','manaregen','healamt','spelldmg','heroic_str','heroic_sta','heroic_agi','heroic_dex','heroic_wis','proceffect','procrate','proclevel','proclevel2','worneffect','worntype','wornlevel','wornlevel2','focuseffect','focuslevel','focuslevel2','banedmgamt','banedmgbody','banedmgrace','banedmgraceamt','elemdmgtype','elemdmgamt','augslot1type','augslot2type','augslot3type','augslot4type','augslot5type','augslot6type']
expr='JSON_OBJECT('+','.join("'%s',`%s`"%(f,f) for f in fields)+')'
ids=[5504,205504,405504,605504,11050,211050,411050,611050,10099,810099,5403,205403,405403,605403,5158,205158,405158,605158,5057,605057,5151,605151,5503,605503,5414,605414]
items=query('SELECT '+expr+' FROM items WHERE id IN ('+','.join(map(str,ids))+') ORDER BY id;')
rules=query("SELECT JSON_OBJECT('ruleset_id',ruleset_id,'rule_name',rule_name,'rule_value',rule_value) FROM rule_values WHERE rule_name IN ('Character:ItemAccuracyCap','Character:ItemAvoidanceCap','Combat:LegacyComputeDefense','Combat:PCAccuracyAvoidanceMod2Scale','Combat:LevelToStopDamageCaps','Combat:AdjustProcPerMinute','Combat:AvgProcsPerMinute','Combat:ProcPerMinDexContrib','Combat:OneProcPerWeapon') ORDER BY ruleset_id,rule_name;")
print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':'production','read_only':True,'scope':'Selected public item definitions and combat rule rows only; no runtime active-ruleset claim','items':items,'rules':rules}))
'''

if __name__ == '__main__':
    out = ROOT / 'public-stats-reference.json'
    if out.exists(): raise FileExistsError('Retain original capture')
    r=subprocess.run(['ssh','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -'],input=REMOTE,text=True,capture_output=True,timeout=150)
    if r.returncode: raise RuntimeError(r.stderr[-1000:])
    data=json.loads(r.stdout)
    with out.open('x',encoding='utf-8') as f: json.dump(data,f,indent=2)
    print(json.dumps({'captured':data['observed_utc'],'items':len(data['items']),'rules':len(data['rules']),'path':str(out)}))
