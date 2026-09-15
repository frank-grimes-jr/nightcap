"""Add legally available Resist Magic to matched owner and pet preparation."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from release_pool_controls import verify as verify_pool


def prepare(original,binary_sha256,pilot=False):
    matrix=copy.deepcopy(original)
    matrix['binary_sha256']=binary_sha256
    matrix['scope']='Matched pet preparation: add Resist Magic to owner and all pets; same gear, AA purchases and original combat routine.'
    matrix['resistance_preparation']={'spell':64,'pilot':pilot}
    cases=[]
    for original_case in original['cases']:
        build=original_case['input']['builds'][0]
        if build['profile']!='mag-nec-shm':continue
        combat=original_case['input']['pet_probe']['combat']
        if pilot and (original_case['seed']!=1729 or combat['npc_id']!=32040 or build['aa_budget'] not in (0,165,306)):
            continue
        case=copy.deepcopy(original_case)
        case['paired_gear_case_id']=case['id'];case['id']+='-resist-magic'
        actions=case['input']['pet_probe']['actions']
        if any(a['spell']==64 for a in actions):raise ValueError('Resist Magic already present')
        lich=next(i for i,a in enumerate(actions) if a['spell']==644)
        actions[lich:lich]=[{'spell':64}]+[{'spell':64,'target_class':c} for c in (13,11,10)]
        cases.append(case)
    if len(cases)!=(3 if pilot else 36):raise ValueError('Expected all source-constrained pet allocations')
    matrix['cases']=cases
    return matrix


def verify(matrix,evidence,original,catalog):
    if matrix!=prepare(original,matrix['binary_sha256'],matrix['resistance_preparation']['pilot']):
        raise ValueError('Resistance comparison changed matched gear, AA or combat inputs')
    rows=verify_pool(matrix,evidence,catalog)
    for run in evidence['runs']:
        state=run['report']['pet_probe']['final']
        if 64 not in {b['spell'] for b in state['player']['buffs']} or len(state['pets'])!=3 or any(
                64 not in {b['spell'] for b in p['buffs']} for p in state['pets']):
            raise ValueError('Resist Magic did not survive native preparation on owner and all pets')
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--binary-sha256')
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--verify',type=Path)
    parser.add_argument('--catalog',type=Path)
    args=parser.parse_args()
    original=json.loads(args.original.read_text(encoding='utf-8'))
    if args.verify:
        if not args.inputs or not args.catalog:parser.error('--verify requires --inputs and --catalog')
        rows=verify(json.loads(args.inputs.read_text(encoding='utf-8')),
                    json.loads(gzip.decompress(args.verify.read_bytes())),original,
                    json.loads(args.catalog.read_text(encoding='utf-8')))
        output={'cases':rows};print(f'Verified {len(rows)} pet resistance comparisons')
    else:
        if not args.binary_sha256:parser.error('Input generation requires --binary-sha256')
        output=prepare(original,args.binary_sha256,args.pilot)
        print(f'Prepared {len(output["cases"])} pet resistance comparisons')
    args.output.write_bytes((json.dumps(output,indent=2)+'\n').encode())
