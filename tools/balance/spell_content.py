"""Resolve frozen NPC spell dependencies before constructing encounter actions."""
import argparse
import json
from pathlib import Path

from builds import load_snapshot
from spell_math import buff_duration, effect_value


TYPE_NAMES = {1:'nuke',2:'heal',4:'root',8:'idle_buff',16:'escape',32:'pet',64:'lifetap',
              128:'snare',256:'dot',512:'dispel',1024:'in_combat_buff',2048:'mez',
              4096:'charm',8192:'slow',16384:'debuff'}
INNATE_TYPES = 1|4|64|256|512|2048|4096|8192|16384


def content_enabled(row, expansion=0):
    return (row.get('min_expansion',-1)<=expansion
            and (row.get('max_expansion',-1)==-1 or row['max_expansion']>=expansion)
            and not row.get('content_flags') and not row.get('content_flags_disabled'))


def active_npc_entries(list_id, level, tables):
    if list_id==0:
        return []
    lists = {row['id']:row for row in tables['npc_spells']}
    if list_id not in lists:
        raise ValueError(f'Missing NPC spell list {list_id}')
    parent = lists[list_id]['parent_list']
    if parent and parent not in lists:
        raise ValueError(f'Missing parent NPC spell list {parent}')
    # The engine loads the immediate parent, not an arbitrarily recursive chain.
    child_rows = [r for r in tables['npc_spells_entries'] if r['npc_spells_id']==list_id and content_enabled(r)]
    child_ids = {r['spellid'] for r in child_rows}
    inherited = [r for r in tables['npc_spells_entries'] if parent and r['npc_spells_id']==parent
                 and r['spellid'] not in child_ids and content_enabled(r)]
    active = [dict(r) for r in inherited+child_rows if r['spellid']>0 and r['minlevel']<=level<=r['maxlevel']]
    for row in active:
        if row['priority']==0 and not (row.get('type',1)&INNATE_TYPES):
            row['priority']=1
    # Equal-priority std::sort ordering is not specified. Preserve grouping and
    # provenance rather than pretending this reporting order proves AI selection.
    return sorted(active,key=lambda r:(r['priority'],r['minlevel'],r['id']))


def resolved_effects(spell, level):
    result=[]
    for slot in range(1,13):
        effect,base,formula,maximum = (spell[f'{k}{slot}'] for k in
                                       ('effectid','effect_base_value','formula','max'))
        if effect==254 or (effect==10 and base==0 and formula==100):
            continue
        if effect in (148,149):
            value=base  # stacking metadata is not a scalar application
        else:
            value=effect_value(formula,base,maximum,level,
                               duration_formula=spell['buffdurationformula'],duration=spell['buffduration'])
        result.append({'slot':slot,'effect_id':effect,'base':base,'formula':formula,
                       'maximum':maximum,'value':value,
                       'kind':'stacking_metadata' if effect in (148,149) else 'formula_value'})
    return result


def npc_spell_profile(npc, tables):
    spells={r['id']:r for r in tables['spells_new']}
    active=active_npc_entries(npc['npc_spells_id'],npc['level'],tables)
    rows=[]
    for entry in active:
        sid=entry['spellid']
        if sid not in spells:
            raise ValueError(f'NPC {npc["id"]} references uncaptured spell {sid}')
        s=spells[sid]
        effects=resolved_effects(s,npc['level'])
        runtime_effects=[e for e in effects if e['kind']!='stacking_metadata']
        first=runtime_effects[0] if runtime_effects else None
        mana = s['mana'] if entry['manacost']==-1 else 0 if entry['manacost']==-2 else entry['manacost']
        recast = s['recast_time'] if entry['recast_delay']<0 else entry['recast_delay']*1000
        if entry['recast_delay']>=10000:
            raise ValueError('Special no-cooldown-update NPC recast semantics require explicit handling')
        rows.append({'spell_id':sid,'name':s['name'],'source_list':entry['npc_spells_id'],
                     'entry_id':entry['id'],'priority':entry['priority'],'type':entry['type'],
                     'type_name':TYPE_NAMES.get(entry['type'],'unsupported_combination'),
                     'mana_cost':mana,'cast_ms':0 if entry['manacost']==-2 else s['cast_time'],
                     'spell_recovery_ms':s['recovery_time'],'recast_ms':recast,
                     'target_type':s['targettype'],'min_hp_percent':entry['min_hp'],
                     'max_hp_percent':entry['max_hp'],'resist_type':s['resisttype'],
                     'resist_adjust':entry['resist_adjust'] if entry['resist_adjust'] is not None else s['ResistDiff'],
                     'no_resist':bool(s['field209']), 'no_item_scaling':bool(s['maxtargets']),
                     'min_resist':s['MinResist'],'max_resist':s['MaxResist'],
                     'partial_resist':bool(not s['no_partial_resist'] and first and first['effect_id'] in (0,79) and first['base']<0),
                     'base_duration_ticks':buff_duration(npc['level'],s['buffdurationformula'],s['buffduration']),
                     'effects':effects})
    return {'npc_id':npc['id'],'name':npc['name'],'level':npc['level'],'base_class':npc['class'],
            'spell_list':npc['npc_spells_id'],'mana':npc['mana'],'spells':rows,
            'equal_priority_groups':[[r['spell_id'] for r in rows if r['priority']==priority]
                                      for priority in sorted({r['priority'] for r in rows})],
            'scope':'Base formula values and content/level-filtered immediate-parent dependencies; not final focus-scaled effects or proven equal-priority cast ordering'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    snapshot,manifest=load_snapshot(args.snapshot)
    profiles=[npc_spell_profile(n,snapshot['tables']) for n in snapshot['tables']['npc_types']]
    report={'snapshot_sha256':manifest['snapshot_sha256'],'profiles':profiles,
            'status':'Resolved content dependencies; full actor effects and casting AI integration pending'}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for p in profiles:
        print(p['name']+': '+', '.join(s['name']+' ['+s['type_name']+']' for s in p['spells']))


if __name__=='__main__':
    main()
