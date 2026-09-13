"""Acceptance states for atomic class release and earned-AA refunds."""
import copy
from aa_owned_view_controls import prepare
from aa_bulk_controls import assess


def cases(matrix):
    template=prepare(matrix)
    template.pop('stored')
    template['input']['profile_save_fixture']=True
    # Keep the earlier skill-test rows on character 4 untouched. Character 1
    # has the same synthetic WAR/CLR/WIZ classes and no persisted skills.
    template['input']['builds'][0]['test_character_id']=1
    definitions=[
        ('release-full-earned-wizard',0,False,False,None,False),
        ('release-partially-usable-wizard',4,False,False,None,False),
        ('release-suspended-wizard',-1,False,False,None,False),
        ('release-preserves-shared-earned-aa',0,True,False,None,False),
        ('failed-class-write-preserves-entire-character',0,False,False,'character_multiclass',False),
        ('failed-point-write-preserves-entire-character',0,False,False,'character_data',False),
        ('release-second-promotes-wizard-without-refund',0,False,True,None,True),
    ]
    result=[]
    for identity,mask,shared,second,failure,before_pass in definitions:
        case=copy.deepcopy(template)
        case.update(id=identity,initial_wallet=17,fail_table=failure,expected_before_pass=before_pass)
        char=case['input']['builds'][0]['test_character_id']
        case['rows']=[{'id':char,'aa_id':267,'aa_value':6,'charges':0}]
        if shared:
            case['rows'].append({'id':char,'aa_id':107,'aa_value':6,'charges':0})
        operations=['load']
        if mask: operations += ['restrict_expansions','load']
        release='release_second' if second else 'release_third'
        operations += [release,'load','save']
        if not failure and not second: operations += [release]
        probe=case['input']['aa_ownership_probe']
        probe.update(first_rank_id=267,initial_spent_points=35+(24 if shared else 0),initial_expended_points=5,
                     inspect_earned=True,inspect_lifecycle=True,inspect_classes=True,
                     expansion_mask=0 if mask==-1 else mask,operations=operations,
                     allowed_failures=sorted(set([release,'load','save'] if failure else [release])))
        active=6; released=False; valid=True; restricted=False; failure_count=0
        case['expected']=[]
        for operation in operations:
            success=True
            if operation=='restrict_expansions': restricted=True
            if operation=='load':
                if not valid: success=False
                else: active=0 if released and not second else (0 if mask==-1 else 3) if restricted else 6
            if operation==release:
                if released or failure:
                    success=False
                    if failure: valid=False; failure_count=1
                else:
                    released=True
                    if not second: active=0
            if operation=='save' and not valid: success=False
            count=0 if released and not second else 6
            wallet=47 if released and not second else 17
            spent=5+(30 if count else 0)+(24 if shared else 0)
            def row(first,n): return {'first_rank_id':first,'rank_count':n,'charges':0}
            stored=([row(267,count)] if count else [])+([row(107,6)] if shared else [])
            profile=([row(267,active)] if active else [])+([row(107,6)] if shared else [])
            classes=[1,12,0] if released and second else [1,2,0] if released else [1,2,12]
            case['expected'].append(dict(effective_rank_count=active,earned_rank_count=count,
                stored=sorted(stored,key=lambda r:r['first_rank_id']),profile=sorted(profile,key=lambda r:r['first_rank_id']),unspent_points=wallet,spent_points=spent,expended_points=5,
                saved_points={'wallet':wallet,'spent':spent,'expended':5},earned_state_valid=valid,success=success,
                loaded_classes=classes,saved_classes=classes,injected_release_failures=failure_count))
        result.append(case)
    return result
