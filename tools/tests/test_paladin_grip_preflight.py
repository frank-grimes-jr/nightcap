import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paladin_grip_preflight import REFERENCE, STAT_REFERENCE, STAT_FIELDS, EXPECTED_DISPATCH, validate, validate_fresh

def reference():
    data=json.loads(REFERENCE.read_text())
    stats={r['id']:r for r in json.loads(STAT_REFERENCE.read_text())['items']}
    for row in data['items']:
        if row['id'] in stats: row.update({f:stats[row['id']][f] for f in STAT_FIELDS})
    data['precedence']={key:[path] for key,path in EXPECTED_DISPATCH.items()}
    data['dispatch']={key:[{'npc_id':1,'version':'v0','selected':[path]}] for key,path in EXPECTED_DISPATCH.items()}
    data['dispatch']['paw/Brother_Hayle'].append({'npc_id':1,'version':'v1','selected':[]})
    return data


class PaladinGripPreflight(unittest.TestCase):
    def test_exact_production_reference(self):
        self.assertEqual(validate(reference())['result'],'PASS')

    def test_canonical_damage_and_quest_drift_block_release(self):
        before=reference()
        for field in ['damage','delay','itemtype','slots','classes']:
            data=copy.deepcopy(before)
            next(r for r in data['items'] if r['id']==605504)[field]+=1
            with self.assertRaisesRegex(ValueError,'Canonical weapon drift'): validate(data)
        for field in STAT_FIELDS:
            data=copy.deepcopy(before)
            next(r for r in data['items'] if r['id']==810099)[field]+=1
            with self.assertRaisesRegex(ValueError,'support-stat drift'): validate(data)
        data=copy.deepcopy(before)
        data['scripts']['airplane/Inte_Akera.lua']['source']+='\n-- concurrent edit\n'
        with self.assertRaisesRegex(ValueError,'script digest'): validate(data)
        data=copy.deepcopy(before);data['precedence']['airplane/Inte_Akera'].append('airplane/70001.pl')
        with self.assertRaisesRegex(ValueError,'precedence'):validate(data)
        data=copy.deepcopy(before);data['helpers']['lua_modules/items.lua']['source']+='\n-- regressed helper\n'
        with self.assertRaisesRegex(ValueError,'helper drift'):validate(data)
        helper=data['helpers']['lua_modules/items.lua']
        helper['sha256']=hashlib.sha256(helper['source'].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,'helper drift'):validate(data)
        data=copy.deepcopy(before);data['recipe_references'].append({'item_id':611050})
        with self.assertRaisesRegex(ValueError,'recipe'):validate(data)

    def test_release_rejects_stale_or_future_captures(self):
        data=reference()
        observed=datetime.datetime.fromisoformat(data['observed_utc'])
        self.assertEqual(validate_fresh(data,observed)['result'],'PASS')
        for seconds in [3601,-301]:
            with self.assertRaisesRegex(ValueError,'last hour'):
                validate_fresh(data,observed+datetime.timedelta(seconds=seconds))

    def test_legacy_handlers_cannot_be_shadowed_or_unchecked(self):
        for key in ('ecommons/Epic_Forgemaster','poknowledge/Epic_Forgemaster','hohonora/#Irak_Altil'):
            for selected in ([], ['global/default.pl'], ['ecommons/999.lua'],
                             [EXPECTED_DISPATCH[key], EXPECTED_DISPATCH[key]+'.lua']):
                data=reference();data['dispatch'][key][0]['selected']=selected
                with self.assertRaisesRegex(ValueError,'dispatch drift'):validate(data)
            data=reference();del data['dispatch'][key]
            with self.assertRaisesRegex(ValueError,'dispatch evidence'):validate(data)
