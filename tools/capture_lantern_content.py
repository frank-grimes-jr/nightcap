"""Read public production content for Last Lantern; no player rows or writes."""
import json
from pathlib import Path
import subprocess

from epic05 import load_catalog
from last_lantern_content import ROOT

OUT = ROOT / 'docs/adventure-journal/release-20261107'
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202', 'sudo -n python3 -']


def main():
    catalog = load_catalog()
    npc_ids = sorted({o['npc'] for c in catalog['shared'] + catalog['paths']
                      for o in c['objectives'] if 'npc' in o})
    fields = ('id', 'name', 'level', 'hp', 'mindmg', 'maxdmg', 'npc_spells_id', 'special_abilities')
    pairs = ','.join("'" + f + "',n.`" + f + '`' for f in fields)
    for alias, prefix in [('s', 'spawn'), ('e', 'entry')]:
        for field in ('min_expansion', 'max_expansion', 'content_flags', 'content_flags_disabled'):
            pairs += ", '" + prefix + '_' + field + "'," + alias + '.' + field
    pairs += ", 'condition',s._condition,'chance',e.chance,'min_time',e.min_time,'max_time',e.max_time"
    npcs = ('SELECT JSON_OBJECT(' + pairs + ", 'zone',s.zone,'version',s.version) FROM npc_types n "
            'JOIN spawnentry e ON e.npcID=n.id JOIN spawn2 s ON s.spawngroupID=e.spawngroupID '
            'WHERE n.id IN (' + ','.join(map(str, npc_ids)) + ') AND s.version=0 ORDER BY n.id,s.id;')
    zones = ("SELECT JSON_OBJECT('zone',zoneidnumber,'version',version,'name',short_name,"
             "'map',map_file_name,'x',safe_x,'y',safe_y,'z',safe_z,'min_level',min_level,'expansion',expansion) "
             'FROM zone WHERE zoneidnumber IN (22,65,63,11,66,32,48,39,72,76) AND version=0;')
    hub = ("SELECT JSON_OBJECT('id',s.id,'npc',n.id,'name',n.name,'x',s.x,'y',s.y,'z',s.z) "
           "FROM spawn2 s JOIN spawnentry e ON e.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=e.npcID "
           "WHERE s.zone='ecommons' AND s.version=0 AND s.x BETWEEN -300 AND -100 AND s.y BETWEEN -1710 AND -1500;")
    code = '''import json,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('current',Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1/rollout.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.initialize()
def rows(sql):return [json.loads(line) for line in m.p.sql(sql).splitlines()]
print(json.dumps({'scope':'read-only current production content; not gameplay acceptance','npcs':rows(NPCS),'zones':rows(ZONES),'hub_spawns':rows(HUB)}))
'''
    code = f'NPCS={npcs!r}\nZONES={zones!r}\nHUB={hub!r}\n' + code
    result = subprocess.run(SSH, input=code, text=True, encoding='utf-8', capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr[-1600:])
    data = json.loads(result.stdout)
    OUT.mkdir(exist_ok=True)
    (OUT / 'production-content.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'npcs': len(data['npcs']), 'zones': data['zones'], 'hub_spawns': len(data['hub_spawns'])}, indent=2))


if __name__ == '__main__':
    main()
