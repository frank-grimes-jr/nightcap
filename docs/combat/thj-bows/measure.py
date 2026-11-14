"""Compile unmodified server hit methods with controlled dependencies and measure paired arrows."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
METHODS = {
    'zone/special_attacks.cpp': ['void Mob::DoArcheryAttackDmg('],
    'zone/attack.cpp': [
        'int Mob::compute_tohit(', 'int Mob::GetTotalToHit(', 'bool Mob::CheckHitChance(',
        'int Mob::offense(', 'double Mob::RollD20(', 'void Mob::MeleeMitigation(',
        'void Mob::DoAttack(', 'const DamageTable &Mob::GetDamageTable(',
        'void Mob::ApplyDamageTable(', 'void Mob::CommonOutgoingHitSuccess(', 'bool Mob::HasCombatClass(',
    ],
    'zone/bonuses.cpp': ['void Mob::SetHeroicDexBonuses('],
    'zone/mob.cpp': ['int Mob::GetSkillDmgAmt(', 'bool Mob::IsWarriorClass('],
}


def method(source, signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def aa_data():
    policy = json.loads((ROOT / 'config/aa-policy.json').read_text())
    catalog = ROOT / policy['catalog']
    data = json.load(gzip.open(catalog))
    rank_map = {row['id']: row for row in data['aa_ranks']}
    result = {}
    for ability_id in (82, 878, 84, 557):
        ability = next(row for row in data['aa_ability'] if row['id'] == ability_id)
        rank_id = ability['first_rank_id']
        ranks = []
        for _ in range(policy['rank_caps'][str(ability_id)]):
            rank = rank_map[rank_id]
            effects = [row for row in data['aa_rank_effects'] if row['rank_id'] == rank_id]
            ranks.append(dict(id=rank_id, cost=rank['cost'], level_req=rank['level_req'],
                              effects=effects, prereqs=[row for row in data['aa_rank_prereqs']
                                                       if row['rank_id'] == rank_id]))
            rank_id = rank['next_id']
        result[str(ability_id)] = dict(name=ability['name'], classes=ability['classes'], ranks=ranks)
    return result, digest(catalog.read_bytes())


def run(args):
    fixture = (HERE / 'bow_boundary.cpp').read_text()
    extracted = []
    fingerprints = {}
    for name, signatures in METHODS.items():
        data = (args.source / name).read_bytes()
        fingerprints[name] = digest(data)
        text = data.decode()
        extracted.extend(method(text, signature) for signature in signatures)
        if name == 'zone/attack.cpp' and 'void Mob::DoAttackWithBowOrigin(' in text:
            extracted.append(method(text, 'void Mob::DoAttackWithBowOrigin('))
            fixture = '#define BOW_ORIGIN 1\n' + fixture
    for header in ('common/nightcap_melee.h', 'common/ruletypes.h'):
        fingerprints[header] = digest((args.source / header).read_bytes())
    aa, catalog_sha = aa_data()
    percent, flat = aa['82']['ranks'], aa['878']['ranks']
    for rank in percent:
        assert [(e['effect_id'], e['base2']) for e in rank['effects']] == [(301, 0)]
    assert [(e['effect_id'],e['base2']) for e in flat[0]['effects']] == [(220, 7)]
    profiles = [('none', 0, 0, 0)]
    spent = 0
    for number, rank in enumerate(percent, start=1):
        spent += rank['cost']
        profiles.append((f'archery_{number}', rank['effects'][0]['base1'], 0, spent))
    bow_value = flat[0]['effects'][0]['base1']
    profiles.append(('bow_1', 0, bow_value, flat[0]['cost']))
    profiles.append(('both', profiles[3][1], bow_value, spent + flat[0]['cost']))
    profile_cpp = ',\n'.join(f'{{"{label}", {pct}, {amt}, {cost}}}'
                              for label, pct, amt, cost in profiles)
    fixture = fixture.replace('// EXTRACTED METHODS', '\n'.join(extracted))
    fixture = fixture.replace('/* AA PROFILES */', profile_cpp)
    with tempfile.TemporaryDirectory(prefix='nightcap-bow-') as temp:
        tmp = Path(temp)
        (tmp / 'bow.cpp').write_text(fixture)
        exe = tmp / ('bow.exe' if os.name == 'nt' else 'bow')
        env = os.environ.copy()
        if os.name == 'nt' and not args.compiler:
            build = tmp / 'build.cmd'
            build.write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\n'
                             f'cl /nologo /EHsc /O2 /std:c++17 /I"{args.source.resolve()}" bow.cpp /Fe:bow.exe\n')
            subprocess.run(['cmd', '/d', '/c', str(build)], cwd=tmp, check=True)
            version = 'MSVC x64 C++17 /O2'
        else:
            compiler = args.compiler or shutil.which('g++') or 'clang++'
            version = subprocess.check_output([compiler, '--version'], text=True).splitlines()[0]
            subprocess.run([compiler, '-std=c++17', '-O2', '-I', str(args.source),
                            str(tmp/'bow.cpp'), '-o', str(exe)], check=True)
            env['PATH'] = str(Path(compiler).parent) + os.pathsep + env.get('PATH', '')
        output = subprocess.check_output([str(exe)], text=True, env=env)
    rows = list(csv.DictReader(io.StringIO(output)))
    for row in rows:
        histogram = row.pop('histogram')
        for key in row.keys() - {'profile', 'scenario'}:
            row[key] = int(row[key])
        if histogram:
            row['damage_counts'] = {damage:int(count) for damage, count in
                                    (pair.split(':') for pair in histogram.split())}
    validate(rows, profiles, '#define BOW_ORIGIN' in fixture)
    return dict(source_sha256=fingerprints, compiler=version, aa_catalog_sha256=catalog_sha,
                aa_policy_id=json.loads((ROOT/'config/aa-policy.json').read_text())['id'],
                aa_catalog=aa, samples=rows)


def validate(rows, profiles, candidate):
    """Verify the cross product against the measured base hit distribution independently."""
    indexed = {(r['scenario'], r['profile'], r['hdex']): r for r in rows}
    base = indexed['normal', 'none', 0]
    histogram = {int(h): n for h, n in base['damage_counts'].items()}
    assert len(indexed) == len(rows) == 117
    assert sum(histogram.values()) == base['landed'] and 0 < base['landed'] < base['attempts']
    for profile, percent, flat, spent in profiles:
        for hdex in (0, 9, 10, 99, 100, 101, 199, 200, 249, 250, 299, 300, 400):
            row = indexed['normal', profile, hdex]
            # Piecewise interpolation of the published guide anchors, in basis points.
            anchors = [(0,0), (100,2500), (200,3400), (250,3700), (300,4000), (400,4600)]
            lo, hi = next((a,b) for a,b in zip(anchors, anchors[1:]) if a[0]<=hdex<=b[0])
            boost = lo[1] + (hi[1]-lo[1])*(hdex-lo[0])//(hi[0]-lo[0]) if candidate else 0
            def expected(hit):
                h = hit*(10000+boost)//10000
                return h + h*percent//100 + flat + hdex//10
            assert row['spent'] == spent and row['flat'] == hdex//10
            assert (row['landed'],row['offense'],row['tohit']) == (base['landed'],250,504)
            assert row['total'] == sum(expected(h)*n for h,n in histogram.items()), row
            assert (row['min'],row['max'],row['first']) == tuple(expected(base[k]) for k in ('min','max','first'))
    for hdex in (0,100,300):
        def stats(scenario):
            r = indexed[scenario,'none',hdex]
            return tuple(r[k] for k in ('landed','total','min','max','first'))
        assert stats('normal') == stats('immediate') == stats('non_ranger')
        assert stats('51_rooted') == stats('51_moving') == stats('51_held_rooted') == stats('51_held_moving')
        assert stats('51_held') == stats('51_primary' if candidate else '51_moving')
        assert stats('51_primary')[1] == 2*stats('51_moving')[1] - (hdex//10)*stats('51_moving')[0]
        assert stats('throwing') == stats('skill_archery') == stats('scripted_bow')
        assert stats('throwing')[1] == base['total'] + (hdex//10)*base['landed']
        assert stats('headshot')[2:4] == (1000+hdex//10,1000+hdex//10)
        assert stats('npc')[1] == indexed['npc','none',0]['total']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'server-mods/code')
    parser.add_argument('--compiler')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(run(args), indent=2) + '\n')
