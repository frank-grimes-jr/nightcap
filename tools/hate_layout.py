"""Hate terrain successor; retain classic encounter and earned-reward identities."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/dungeons/hate-layout-20261029'


def apply_catalog(dungeons):
    legacy = copy.deepcopy(next(d for d in dungeons if d['zone_id'] == 76))
    successor = next(d for d in dungeons if d['zone_id'] == 76)
    successor['zone_id'] = 186
    successor['zone'] = 'hateplaneb'
    poses={r['spawn_id']:r for r in population()}
    for boss in successor['bosses']:
        p=poses[boss['spawn_id']]
        boss['spawn'].update(zone='hateplaneb',x=p['x'],y=p['y'],z=p['z'],
                             heading=p['heading'],pathgrid=p['grid_id'],managed_private=True)
    # Index 19 continues to own the same tasks and six exclusive item IDs.
    # Spawn/NPC/objective identities are scoped by zone/run and remain stable.
    return legacy


def population():
    return json.loads((HERE / 'population.json').read_text())['rows']


def book_pose():
    return json.loads((HERE / 'population.json').read_text())['book_pose']
