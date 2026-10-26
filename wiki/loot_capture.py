"""Fixed, field-allowlisted production content queries in one read-only snapshot.

Run on the production host. Uses the existing private client option file inside
the database container; secrets never enter arguments or the public projection.
There is no HTTP endpoint and no user-supplied SQL.
"""
from datetime import datetime, timezone
import gzip
import json
import re
from pathlib import Path
import subprocess
import sys

BASE = Path('/opt/nightcap/deploy/production')
GATES = 'min_expansion max_expansion content_flags content_flags_disabled'
FIELDS = {
    'zones': ('zone','id zoneidnumber short_name long_name expansion min_status ruleset hotzone '+GATES),
    'spawns': ('spawn2','id spawngroupID zone version x y z respawntime variance pathgrid _condition cond_value '+GATES),
    'disabled_spawns': ('spawn2_disabled','spawn2_id disabled'),
    'spawn_entries': ('spawnentry','spawngroupID npcID chance condition_value_filter min_time max_time '+GATES),
    'npcs': ('npc_types','id name level maxlevel loottable_id race class bodytype rare_spawn raid_target skip_global_loot'),
    'tables': ('loottable','id '+GATES),
    'links': ('loottable_entries','loottable_id lootdrop_id multiplier droplimit mindrop probability'),
    'drops': ('lootdrop','id '+GATES),
    'entries': ('lootdrop_entries','lootdrop_id item_id chance multiplier npc_min_level npc_max_level trivial_min_level trivial_max_level '+GATES),
    'items': ('items','id Name classes slots reqlevel reclevel ac hp mana endur damage delay bagslots bagwr itemtype minstatus deity races astr asta aagi adex awis aint acha heroic_str heroic_sta heroic_agi heroic_dex heroic_wis heroic_int heroic_cha haste regen manaregen spelldmg healamt attack accuracy mr fr cr dr pr'),
    'global_loot': ('global_loot','id loottable_id enabled min_level max_level rare raid race class bodytype zone hot_zone '+GATES),
    'rules': ('rule_values','ruleset_id rule_name rule_value'),
    'flags': ('content_flags','flag_name enabled'),
}
RULES = ['Expansion:CurrentExpansion','Character:MaxLevel','Zone:GlobalLootMultiplier',
         'Zone:LootTierRareChance','Zone:LootTierEpicChance','Zone:LootTierLegendaryChance']
CTE = '''WITH z AS (SELECT short_name FROM zone WHERE version=0 AND min_status=0 AND expansion<=@era),
s AS (SELECT id,spawngroupID FROM spawn2 WHERE zone IN (SELECT short_name FROM z) AND version IN (0,-1)
      AND (min_expansion=-1 OR min_expansion<=@era) AND (max_expansion=-1 OR max_expansion>=@era)),
n AS (SELECT id,loottable_id FROM npc_types WHERE id IN (SELECT npcID FROM spawnentry WHERE spawngroupID IN (SELECT spawngroupID FROM s))),
t AS (SELECT loottable_id id FROM n UNION SELECT loottable_id FROM global_loot WHERE enabled=1),
d AS (SELECT DISTINCT lootdrop_id id FROM loottable_entries WHERE loottable_id IN (SELECT id FROM t)),
i AS (SELECT DISTINCT item_id id FROM lootdrop_entries WHERE lootdrop_id IN (SELECT id FROM d)) '''
SCOPES = {
    'zones':'version=0 AND short_name IN (SELECT short_name FROM z)',
    'spawns':'id IN (SELECT id FROM s)',
    'disabled_spawns':'instance_id=0 AND spawn2_id IN (SELECT id FROM s)',
    'spawn_entries':'spawngroupID IN (SELECT spawngroupID FROM s)',
    'npcs':'id IN (SELECT id FROM n)',
    'tables':'id IN (SELECT id FROM t)',
    'links':'loottable_id IN (SELECT id FROM t)',
    'drops':'id IN (SELECT id FROM d)',
    'entries':'lootdrop_id IN (SELECT id FROM d)',
    'items':"id IN (SELECT id FROM i UNION SELECT id+200000 FROM i WHERE id<200000 UNION SELECT id+400000 FROM i WHERE id<200000 UNION SELECT id+600000 FROM i WHERE id<200000)",
    'global_loot':'enabled=1',
    'rules':"rule_name IN ("+','.join("'"+r+"'" for r in RULES)+')',
    'flags':'1=1',
}
ERAS = ['Classic','Ruins of Kunark','Scars of Velious','Shadows of Luclin','Planes of Power','Legacy of Ykesha',
        'Lost Dungeons of Norrath','Gates of Discord','Omens of War','Dragons of Norrath','Depths of Darkhollow',
        'Prophecy of Ro','The Serpent’s Spine','The Buried Sea','Secrets of Faydwer','Seeds of Destruction',
        'Underfoot','House of Thule','Veil of Alaris','Rain of Fear']


def statements(default_name):
    # Config is private trusted input, still validate before constructing literals.
    if not default_name or not all(c.isalnum() or c in '_+-' for c in default_name):
        raise ValueError('Unsupported configured ruleset name')
    sql = ["SET SESSION max_statement_time=45;",
           'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;',
           'START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;',
           f"SET @ruleset=(SELECT ruleset_id FROM rule_sets WHERE name='{default_name}');",
           "SET @era=(SELECT CAST(rule_value AS SIGNED) FROM rule_values WHERE ruleset_id=@ruleset AND rule_name='Expansion:CurrentExpansion');",
           "SELECT JSON_ARRAY('meta',JSON_OBJECT('default_ruleset',@ruleset,'era',@era));"]
    for key,(table,fields) in FIELDS.items():
        pairs=','.join("'"+('name' if f=='Name' else f)+"',`"+f+'`' for f in fields.split())
        if key=='items':
            # Drive indexed item lookups from a materialized ID set. An IN UNION
            # subquery is correlated by MariaDB and rescans loot for every item.
            ids='(SELECT id FROM i UNION SELECT id+200000 FROM i WHERE id<200000 UNION SELECT id+400000 FROM i WHERE id<200000 UNION SELECT id+600000 FROM i WHERE id<200000)'
            sql.append(CTE+f"SELECT STRAIGHT_JOIN JSON_ARRAY('items',JSON_OBJECT({pairs})) FROM {ids} wanted JOIN items USING(id);")
        else:
            sql.append(CTE+f"SELECT JSON_ARRAY('{key}',JSON_OBJECT({pairs})) FROM `{table}` WHERE {SCOPES[key]};")
    return '\n'.join(sql+['ROLLBACK;'])


def capture(base=BASE):
    config=json.loads((base/'private/eqemu_config.json').read_text())
    default_name=config['server'].get('rules',{}).get('default','default')
    command=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config',
             '--batch','--raw','--skip-column-names','peq']
    started=datetime.now(timezone.utc).isoformat()
    p=subprocess.run(command,cwd=base,input=statements(default_name),capture_output=True,text=True,timeout=300)
    if p.returncode:
        # Do not echo SQL, connection diagnostics, config or raw server errors.
        error = re.search(r'ERROR (\d+) \([A-Z0-9]+\) at line (\d+)', p.stderr)
        completed = {key:0 for key in FIELDS}
        for line in p.stdout.splitlines():
            try:
                key,_=json.loads(line)
                if key in completed: completed[key]+=1
            except (ValueError,TypeError): pass
        raise RuntimeError('Production content capture failed; previous public data retained. '+
                           ('Database error '+error.group(1)+' at SQL line '+error.group(2) if error else 'Process failure')+
                           '; completed row counts '+json.dumps(completed))
    result={key:[] for key in FIELDS}
    for line in p.stdout.splitlines():
        key,row=json.loads(line)
        if key=='meta':
            for name in ['era','default_ruleset']:
                value=row.get(name)
                if not re.fullmatch(r'-?\d+',str(value)):
                    raise ValueError('Missing production era or configured ruleset')
                result[name]=int(value)
        else: result[key].append(row)
    if type(result.get('era')) is not int or not 0<=result['era']<len(ERAS):
        raise ValueError('Production era is missing or unsupported; refusing publication')
    if not result.get('default_ruleset') or not all(result[k] for k in ['items','npcs','spawns','zones','rules']):
        raise ValueError('Incomplete production content capture')
    result.update(captured_at=started,era_name=ERAS[result['era']])
    return result


if __name__=='__main__':
    sys.stdout.buffer.write(gzip.compress(json.dumps(capture(),separators=(',',':')).encode(),mtime=0))
