"""Emit read-only public-content preflight checks; no connection or writes."""
import json
from pathlib import Path
from hate_layout_migration import HERE, SCOPES, rows, runtime_checks


def checks():
    population=rows()['nightcap_dungeon_spawns']
    ids=','.join(str(r['spawn_id']) for r in population if r['npc_id']!=998812)
    groups=','.join(str(i) for i in sorted({r['group_id'] for r in population if r['npc_id']!=998812}))
    result=[c for c in runtime_checks() if '/original-spawn-policy/' in c['label']]
    def add(label,sql,expected=0):
        result.append(dict(label=label,sql=sql,expected=str(expected)))
    for table,scope in SCOPES.items():add('empty/'+table,f'SELECT COUNT(*) FROM `{table}` WHERE {scope}')
    add('original-groups',f'SELECT COUNT(*) FROM spawngroup WHERE id IN ({groups}) AND dist=0',len({r['group_id'] for r in population if r['npc_id']!=998812}))
    add('original-disabled',f'SELECT COUNT(*) FROM spawn2_disabled WHERE instance_id=0 AND spawn2_id IN ({ids})')
    add('traps',"SELECT COUNT(*) FROM traps WHERE zone IN ('hateplane','hateplaneb')")
    add('zone-points',"SELECT COUNT(*) FROM zone_points WHERE zone IN ('hateplane','hateplaneb')")
    add('hotzones','SELECT COUNT(*) FROM zone WHERE zoneidnumber IN (76,186) AND version=0 AND hotzone=0',2)
    add('blocked-spells','SELECT COUNT(*) FROM blocked_spells WHERE zoneid IN (76,186)')
    return result


if __name__=='__main__':
    (HERE/'preflight-checks.json').write_text(json.dumps(checks(),indent=2)+'\n')
    print('Generated read-only public-content checks; no database connection.')
