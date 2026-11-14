"""Read exact target SPA rows, coordinate/distance flags and buff storage schema."""
import json
from probe import LOAD, remote, write

code = """
cols = [r.split('\t')[0] for r in prior.sql('SHOW COLUMNS FROM spells_new').splitlines()]
fields = [n for n in cols if n.lower() in ('id','name','good_effect','buffdurationformula','buffduration','suspendable','short_buff_box','persistdeath','targettype','aoerange','range','zone_type','cast_restriction','not_extendable','no_remove','cast_on_fade_duration','powerful_flag') or any(k in n.lower() for k in ('dist','suspend','caston','cast_on','direction','short_buff','extend','persist','song')) or n.lower().startswith(('effectid','effect_base_value','effect_limit_value','max'))]
rows = prior.sql('SELECT JSON_ARRAY('+','.join('`'+n+'`' for n in fields)+') FROM spells_new WHERE id IN (21773,30736) ORDER BY id')
spells = [dict(zip(fields,json.loads(r),strict=True)) for r in rows.splitlines()]
assert len(spells)==2
buffs = [r.split('\t')[:2] for r in prior.sql('SHOW COLUMNS FROM character_buffs').splitlines()]
rules = prior.sql("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name LIKE '%Buff%' AND (rule_name LIKE '%Save%' OR rule_name LIKE '%Suspend%' OR rule_name LIKE '%Persist%') ORDER BY rule_name").splitlines()
ranks = prior.sql("SELECT id,spell,recast_time FROM aa_ranks WHERE id IN (8303,13484,15414) ORDER BY id").splitlines()
saved = prior.sql("SELECT spell_id,COUNT(*) FROM character_buffs WHERE spell_id IN (21773,30736) GROUP BY spell_id ORDER BY spell_id").splitlines()
focus = prior.sql("SELECT rank_id,slot,effect_id,base1,base2 FROM aa_rank_effects WHERE rank_id=15414 ORDER BY slot").splitlines()
print(json.dumps(dict(spells=spells,buff_storage=buffs,save_rules=rules,aa_ranks=ranks,legacy_saved_counts=saved,extended_bloodlust=focus)))
"""

if __name__ == "__main__":
    data = json.loads(remote(LOAD+code))
    write("spell-preimages.json",data)
    print(json.dumps(data))
