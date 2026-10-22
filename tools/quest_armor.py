"""Validate the reviewed class-armor catalog and exact reward-only script delta."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT/'docs/releases/quest-armor-20261022/production-reference.json'
CATALOG = ROOT/'docs/items/quest-armor-catalog.json'


def reward_source(source, ids):
    """Replace only one audited literal grant per reward; never inputs/returns."""
    for item_id in ids:
        patterns = [
            rf'((?:quest::summonitem|e\.other:SummonItem)\(["\']?){item_id}(["\']?\))',
            rf'(e\.other:QuestReward\(e\.self,0,0,0,0,){item_id}(,1000\))',
        ]
        count = 0
        for pattern in patterns:
            source, n = re.subn(pattern, lambda m: m[1]+str(item_id+600000)+m[2], source)
            count += n
        if count != 1:
            raise ValueError(f'Expected one terminal grant for {item_id}; found {count}')
    return source


def validate(root=ROOT):
    catalog = json.loads((root/CATALOG.relative_to(ROOT)).read_text())
    reference = json.loads((root/REFERENCE.relative_to(ROOT)).read_text())
    items = {row['id']:row for row in reference['items']}
    seen = set()
    report = []
    expected_classes = {'Warrior':1,'Bard':128,'Shadow Knight':16,'Ranger':8,'Shaman':512}
    identities = ('itemclass','itemtype','slots','classes','races','reqlevel','reclevel','augtype',
                  'augslot1type','augslot2type','augslot3type','augslot4type','augslot5type',
                  'augslot6type','loregroup','attuneable')
    for family in catalog['families']:
        for relative, ids in family['scripts'].items():
            if Path(relative).is_absolute() or '..' in Path(relative).parts:
                raise ValueError('Unsafe quest path')
            before = reference['scripts'][relative]
            if hashlib.sha256(before['source'].encode()).hexdigest() != before['sha256']:
                raise ValueError('Captured script hash mismatch: '+relative)
            if reference['precedence'][relative] != [relative]:
                raise ValueError('Ambiguous quest precedence: '+relative)
            for item_id in ids:
                if type(item_id) is not int or item_id in seen:
                    raise ValueError('Invalid/duplicate reward ID')
                seen.add(item_id)
                base, target = items[item_id], items[item_id+600000]
                if target['id'] > 1048575 or target['Name'] != base['Name']+' (Ascended)':
                    raise ValueError('Invalid Ascended identity')
                if base['itemclass'] != 0 or base['itemtype'] != 10 or not base['slots']:
                    raise ValueError('Reward is not ordinary armor')
                if base['classes'] != expected_classes[family['class']]:
                    raise ValueError('Unexpected class family')
                if any(base[key] != target[key] for key in identities):
                    raise ValueError('Variant changes eligibility/socket identity')
            expected = reward_source(before['source'], ids)
            actual = (root/'server-mods/quests'/relative).read_bytes()
            if actual != expected.encode():
                raise ValueError('Unexpected source delta: '+relative)
            report.append({'path':relative,'before_sha256':before['sha256'],
                'after_sha256':hashlib.sha256(actual).hexdigest(),'rewards':len(ids)})
    if len(seen) != 37 or len(report) != 10:
        raise ValueError('Review required when expanding the catalog')
    compatibility = []
    for relative, entry in catalog['downstream_compatibility'].items():
        if relative != 'overthere/Kurron_Ni.pl':
            raise ValueError('Unreviewed downstream script')
        before = reference['scripts'][relative]
        actual = (root/'server-mods/quests'/relative).read_bytes()
        if (hashlib.sha256(before['source'].encode()).hexdigest() != entry['before_sha256']
                or before['sha256'] != entry['before_sha256']
                or hashlib.sha256(actual).hexdigest() != entry['after_sha256']
                or reference['precedence'][relative] != [relative]):
            raise ValueError('Downstream compatibility drift')
        compatibility.append({'path':relative,'before_sha256':entry['before_sha256'],
                              'after_sha256':entry['after_sha256']})
    if len(compatibility) != 1:
        raise ValueError('Missing downstream compatibility')
    return {'status':'candidate; not deployed','reward_count':len(seen),'scripts':report,
            'compatibility_scripts':compatibility,
            'reference_observed_utc':reference['observed_utc']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=validate()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'reward_count':result['reward_count'],'scripts':len(result['scripts'])}))


if __name__ == '__main__':
    main()
