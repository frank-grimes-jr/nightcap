"""Additional native release contracts: real skills, grants, charges and API bounds."""
from copy import deepcopy
from aa_owned_view_controls import prepare
from aa_bulk_controls import assess as assess_state


def cases(matrix):
    result=[]
    def add(identity,classes,*,first=267,rank=0,cost=0,charges=0,skills=None,operations=None,extra=None,final=None,fail=None):
        case=prepare(matrix);case.pop('stored')
        build=case['input']['builds'][0]
        build.update(test_character_id=1,classes=classes,equipment=[])
        case['input']['profile_save_fixture']=True
        case['input']['capture_class_release_transport']=True
        case.update(id=identity,classes=classes,rows=([{'id':1,'aa_id':first,'aa_value':rank,'charges':charges}] if rank else []),
                    skills={str(k):v for k,v in (skills or {}).items()},fail_table=fail)
        probe=case['input']['aa_ownership_probe']
        probe.update(first_rank_id=first,initial_spent_points=5+cost,initial_expended_points=5,inspect_earned=True,
                     inspect_lifecycle=True,inspect_classes=True,inspect_release_details=True,inspect_release_packets=True,load_release_skills=True,
                     watched_skills=sorted(int(s) for s in case['skills']),operations=operations or ['load','release_third'],
                     allowed_failures=['release_slot','release_second','release_third','save','load'])
        probe.update(extra or {})
        case['expected']=[{} for _ in probe['operations']]
        final.update(effective_rank_count=final['earned_rank_count'],profile=deepcopy(final['stored']),expended_points=5,
                     injected_release_failures=1 if fail else 0,
                     bonuses_before_recalculation={'spell_crit':0,'hp_percent':0},
                     bonuses_after_recalculation={'spell_crit':0,'hp_percent':0})
        final['connected']=not final['session_exited']
        changed=final['saved_classes']!=classes+[0]*(3-len(classes))
        final['release_publication_expected']=changed
        case['expected'][-1]=final
        result.append(case)
    def rows(first,rank,charges=0): return [] if not rank else [{'first_rank_id':first,'rank_count':rank,'charges':charges}]
    def state(classes,first=267,rank=0,wallet=17,spent=5,valid=True,success=True,skills=None,disconnected=False):
        slots=classes+[0]*(3-len(classes))
        values=[{'id':int(k),'value':v} for k,v in sorted((skills or {}).items(),key=lambda p:int(p[0]))]
        return dict(loaded_classes=slots,saved_classes=slots,class_mask=sum(1<<c for c in classes),
                    stored=rows(first,rank),earned_rank_count=rank,unspent_points=wallet,spent_points=spent,
                    saved_points={'wallet':wallet,'spent':spent,'expended':5},earned_state_valid=valid,success=success,
                    loaded_skills=values,saved_skills=values,session_exited=disconnected)
    skills={0:270,19:200,26:250}
    after={0:250,19:200,26:0}
    add('monk-skill-only-release-clamps-and-preserves',[1,2,7],skills=skills,final=state([1,2],skills=after))
    for table in ('character_skills','character_data'):
        add('monk-release-rollback-'+table,[1,2,7],skills=skills,fail=table,
            final=state([1,2,7],skills=skills,valid=False,success=False,disconnected=True))
    final=state([1,2,7],skills=skills,valid=False,success=False,disconnected=True)
    final['loaded_skills']=[{'id':0,'value':270},{'id':19,'value':200},{'id':26,'value':251}]
    add('stale-skill-refuses-entire-release',[1,2,7],skills=skills,
        operations=['load','stale_release_skill','release_third'],extra={'stale_skill':26},final=final)
    add('class-only-grant-removed-without-refund',[1,3],first=1643,rank=1,
        operations=['load','release_second'],final=state([1],first=1643))
    add('charged-class-only-aa-refunds-unused-charge',[1,2],first=4704,rank=1,cost=4,charges=1,
        operations=['load','release_second'],final=state([1],first=4704,wallet=21))
    add('charged-class-only-aa-does-not-refund-consumed-charge',[1,2],first=4704,rank=1,cost=4,charges=0,
        operations=['load','release_second'],final=state([1],first=4704))
    for slot in (-1,0,1,4,258,259):
        add('invalid-release-slot-'+str(slot),[1,2,12],operations=['load','release_slot'],extra={'release_slot':slot},
            final=state([1,2,12],success=False))
    for slot,chosen in ((258,0),(3,256),(3,13)):
        add('invalid-or-occupied-set-'+str(slot)+'-'+str(chosen),[1,2,12],operations=['load','set_class_slot'],
            extra={'set_slot':slot,'set_class':chosen},final=state([1,2,12]))
    add('empty-release-slot',[1,2],operations=['load','release_third'],final=state([1,2],success=False))
    final=state([1,2,12],valid=False,disconnected=True)
    final.update(loaded_classes=[1,2,0],class_mask=6)
    add('stale-empty-selection-cannot-overwrite-held-class',[1,2,12],
        operations=['load','stale_release_classes','set_class_slot'],extra={'stale_classes':[2,0],'set_slot':3,'set_class':13},final=final)
    final=state([1,2,12],valid=False,success=False,disconnected=True)
    final.update(loaded_classes=[1,2,14],class_mask=16390)
    add('stale-loaded-class-refuses-release',[1,2,12],operations=['load','stale_release_classes','release_third'],
        extra={'stale_classes':[2,14]},final=final)
    add('wizard-passive-bonus-removed-before-harness-recalculation',[1,2,12],first=267,rank=6,cost=30,
        final=state([1,2],first=267,wallet=47))
    result[-1]['expected'][0]={'effective_rank_count':6,'earned_rank_count':6,
        'bonuses_after_recalculation':{'spell_crit':9,'hp_percent':0}}
    return result


def assess(case,report):
    expected=deepcopy(case)
    publishes=expected['expected'][-1].pop('release_publication_expected')
    result=assess_state(expected,report)
    packets=report['aa_ownership_probe']['steps'][-1].get('release_packets',{})
    final=expected['expected'][-1]
    publication=({'in_transaction':0,'classes':final['saved_classes'],'points':final['saved_points'],
                  'aa_rows':len(final['stored']),'skills':final['saved_skills']} if publishes else None)
    changes=[r for r in final['saved_skills'] if case['skills'].get(str(r['id']))!=r['value']]
    required={'publication':publication,'clear_packets':1 if publishes else 0,'table_before_clear':False,'skill_packets':changes,'transport_closed':final['session_exited']}
    for field,value in required.items():
        if packets.get(field)!=value: result['differences'].append({'field':'release_packets.'+field,'expected':value,'actual':packets.get(field)})
    if publishes and packets.get('table_packets',0)<1:
        result['differences'].append({'field':'release_packets.table_packets','expected':'positive','actual':packets.get('table_packets')})
    result['passed']=not result['differences']
    return result
