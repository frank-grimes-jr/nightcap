"""Cross-check equipped native HP/mana using resolved bonuses and frozen base data."""
import argparse
import hashlib
import json
from pathlib import Path

from builds import load_snapshot
from resources import base_hp, base_mana, max_hp, max_mana


def verify(report, builds, tables):
    expected = {(b['profile'],b['tier']):b for b in builds}
    actual = {(r['profile'],r['tier']):r for r in report['builds']}
    if len(actual) != len(report['builds']) or len(expected) != len(builds) or actual.keys() != expected.keys():
        raise ValueError('Native report has missing, duplicate, or unexpected builds')
    mismatches = []
    for key, r in actual.items():
        b = expected[key]
        hp = max_hp(base_hp(b['classes'],b['level'],r['sta'],r['heroic_hp'],tables['base_data']),
                    r['item_hp'],percent=r['item_percent_hp'],flat=r['item_flat_hp'])
        mana = max_mana(b['classes'],base_mana(b['classes'],b['level'],r['int'],r['wis'],r['heroic_mana'],tables['base_data']),r['item_mana'])
        if (hp,mana) != (r['hp'],r['mana']):
            mismatches.append({'build':key,'python':{'hp':hp,'mana':mana},'native':{'hp':r['hp'],'mana':r['mana']}})
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--builds',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    snapshot,manifest = load_snapshot(args.snapshot)
    report = json.loads(args.native.read_text())
    builds = json.loads(args.builds.read_text())['builds']
    mismatches = verify(report,builds,snapshot['tables'])
    result = {'native_report_sha256':hashlib.sha256(args.native.read_bytes()).hexdigest(),
              'snapshot_sha256':manifest['snapshot_sha256'],'builds':len(builds),'mismatches':mismatches,
              'scope':'HP/mana from native resolved stats/item bonuses; excludes active buffs, purchased AAs, and leadership'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return int(bool(mismatches))


if __name__ == '__main__':
    raise SystemExit(main())
