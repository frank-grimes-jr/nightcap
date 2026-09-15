"""Compare resource math with extracted engine functions, without booting a zone."""
import argparse
import hashlib
import json
import random
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from builds import load_snapshot
from resources import base_hp, base_mana, max_hp, max_mana
from verify_cpp import extract_function


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Active code directory')
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot, manifest = load_snapshot(args.snapshot)
    base_data = snapshot['tables']['base_data']
    sources = {name: (args.source / name).read_bytes() for name in
               ('zone/client_mods.cpp', 'zone/mob.cpp', 'common/classes.h')}
    functions = {}
    for signature in ('int64 Client::CalcBaseHP(', 'int64 Client::CalcBaseMana(',
                      'int64 Client::CalcBaseManaForClass(', 'int64 Client::CalcMaxHP(',
                      'int64 Client::CalcMaxMana(', 'bool Client::HasAnyCasterClass('):
        functions[signature] = extract_function(sources['zone/client_mods.cpp'].decode(), signature)
    for signature in ('bool Mob::IsINTCasterClassID(', 'bool Mob::IsWISCasterClassID('):
        functions[signature] = extract_function(sources['zone/mob.cpp'].decode(), signature)
    constants = re.findall(r'constexpr\s+uint8\s+\w+\s*=\s*\d+;', sources['common/classes.h'].decode())
    harness = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using uint8 = uint8_t;
using uint32 = uint32_t;
using int64 = int64_t;
namespace EQ { namespace versions { enum class ClientVersion { SoF, RoF2 }; } }
namespace SBIndex { enum { RESOURCE_PERCENT_CAP, RESOURCE_AMOUNT_CAP }; }
#define RuleB(category, name) true
#define LogSpells(...)
namespace Class {
''' + '\n'.join(constants) + r'''
}
struct BaseDataRepository {
    struct BaseData { int level, class_; double hp, hp_fac, mana, mana_fac; };
};
struct Zone {
    std::vector<BaseDataRepository::BaseData> rows;
    BaseDataRepository::BaseData GetBaseData(int level, int cls) {
        for (auto row : rows) if (row.level == level && row.class_ == cls) return row;
        throw std::runtime_error("Missing base data");
    }
} fixture_zone, *zone = &fixture_zone;
struct Mob {
    static bool IsINTCasterClassID(uint8);
    static bool IsWISCasterClassID(uint8);
};
struct Bonuses {
    int64 HP=0, Mana=0, heroic_max_hp=0, heroic_max_mana=0;
    int PercentMaxHPChange=0;
    int64 FlatMaxHPChange=0, HPPercCap[2]{}, ManaPercCap[2]{};
};
struct Client : Mob {
    int level=50, sta=100, intel=100, wis=100;
    int64 base_hp=0, max_hp=0, current_hp=0, max_mana=0, current_mana=0;
    int64 leadership_hp=0, leadership_mana=0;
    std::vector<uint8> classes;
    Bonuses itembonuses, spellbonuses, aabonuses;
    int GetLevel() { return level; }
    int GetSTA() { return sta; }
    int GetINT() { return intel; }
    int GetWIS() { return wis; }
    const char* GetName() { return "isolated-oracle"; }
    EQ::versions::ClientVersion ClientVersion() { return EQ::versions::ClientVersion::RoF2; }
    std::vector<uint8> GetMulticlassList() const { return classes; }
    uint32 GetBestClassLevelFactor() { throw std::runtime_error("Legacy branch unexpected"); }
    int64 GroupLeadershipAAHealthEnhancement() { return leadership_hp; }
    int64 GroupLeadershipAAManaEnhancement() { return leadership_mana; }
    bool HasAnyCasterClass() const;
    int64 CalcBaseHP();
    int64 CalcBaseMana();
    int64 CalcBaseManaForClass(uint8);
    int64 CalcMaxHP();
    int64 CalcMaxMana();
};
''' + '\n'.join(functions.values()) + r'''
int main() {
    int count;
    std::cin >> count;
    for (int i=0; i<count; ++i) {
        BaseDataRepository::BaseData row{};
        std::cin >> row.level >> row.class_ >> row.hp >> row.hp_fac >> row.mana >> row.mana_fac;
        zone->rows.push_back(row);
    }
    int c1,c2,c3;
    while (std::cin >> c1 >> c2 >> c3) {
        Client c;
        for (int cls : {c1,c2,c3}) if (cls) c.classes.push_back(cls);
        std::cin >> c.level >> c.sta >> c.intel >> c.wis
                 >> c.itembonuses.heroic_max_hp >> c.itembonuses.heroic_max_mana
                 >> c.itembonuses.HP >> c.itembonuses.Mana
                 >> c.aabonuses.PercentMaxHPChange >> c.spellbonuses.FlatMaxHPChange
                 >> c.leadership_hp >> c.spellbonuses.Mana >> c.aabonuses.Mana >> c.leadership_mana;
        if (!std::cin) return 2;
        std::cout << c.CalcBaseHP() << ' ' << c.CalcBaseMana() << ' '
                  << c.CalcMaxHP() << ' ' << c.CalcMaxMana() << '\n';
    }
}
'''
    rows = []
    for cls in range(1, 17):
        for level in (1, 25, 50, 55):
            for stat in (1, 99, 100, 101, 199, 200, 201, 202, 254, 255, 256, 257, 425, 600):
                rows.append((cls, 0, 0, level, stat, stat, stat, 250, 300,
                             1234, 777, 1500, 501, 100, 200, 55, 10))
    rng = random.Random(20260912)
    for _ in range(2000):
        classes = rng.sample(range(1, 17), rng.randint(1, 3))
        rows.append((*classes, *([0] * (3-len(classes))), rng.randint(1, 55),
                     *(rng.randint(1, 1500) for _ in range(3)),
                     rng.randint(0, 10000), rng.randint(0, 10000),
                     rng.choice((rng.randint(0, 10000), 16777217)), rng.randint(-1000, 10000),
                     rng.randint(-9000, 50000), rng.randint(0, 5000), rng.randint(0, 1000),
                     rng.randint(0, 5000), rng.randint(0, 5000), rng.randint(0, 1000)))
    data = [len(base_data)]
    data += [' '.join(str(r[k]) for k in ('level', 'class', 'hp', 'hp_fac', 'mana', 'mana_fac')) for r in base_data]
    data += [' '.join(map(str, row)) for row in rows]
    binary = '/tmp/nightcap-resource-oracle-' + uuid.uuid4().hex
    container = 'akk-stack-eqemu-server-1'
    try:
        subprocess.run(['docker', 'exec', '-i', container, 'g++', '-std=c++17', '-O2',
                        '-ffp-contract=off', '-x', 'c++', '-o', binary, '-'], input=harness,
                       text=True, capture_output=True, check=True)
        result = subprocess.run(['docker', 'exec', '-i', container, binary],
                                input='\n'.join(map(str, data)) + '\n', text=True,
                                capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(error.stderr) from error
    finally:
        subprocess.run(['docker', 'exec', container, 'rm', '-f', binary], check=True)
    outputs = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
    if len(outputs) != len(rows) or any(len(row) != 4 for row in outputs):
        raise ValueError('Incomplete native oracle results')
    mismatches = []
    for row, cpp in zip(rows, outputs):
        c1,c2,c3,level,sta,intel,wis,h_hp,h_mana,item_hp,item_mana,pct,flat,lead_hp,spell_mana,aa_mana,lead_mana = row
        classes = tuple(c for c in (c1,c2,c3) if c)
        hp = base_hp(classes, level, sta, h_hp, base_data)
        mana = base_mana(classes, level, intel, wis, h_mana, base_data)
        actual = (hp, mana, max_hp(hp, item_hp, percent=pct, flat=flat, leadership=lead_hp),
                  max_mana(classes, mana, item_mana, spell=spell_mana, aa=aa_mana, leadership=lead_mana))
        if actual != cpp:
            mismatches.append({'input': row, 'cpp': cpp, 'python': actual})
    report = {'captured_at': datetime.now(timezone.utc).isoformat(),
              'snapshot_sha256': manifest['snapshot_sha256'],
              'source_sha256': {k: hashlib.sha256(v).hexdigest() for k,v in sources.items()},
              'function_sha256': {k: hashlib.sha256(v.encode()).hexdigest() for k,v in functions.items()},
              'harness_sha256': hashlib.sha256(harness.encode()).hexdigest(),
              'cases': len(rows), 'outputs_compared_per_case': 4, 'mismatches': mismatches,
              'scope': 'RoF2 with SoD resource rule; supplied resolved stats/bonuses; excludes bonus resolution, legacy clients, current-resource percent limits, and combat'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(mismatches))


if __name__ == '__main__':
    raise SystemExit(main())
