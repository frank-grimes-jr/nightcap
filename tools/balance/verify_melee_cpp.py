"""Check controlled melee rolls against extracted native engine functions."""
import argparse
import hashlib
import json
import random
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from melee import damage_interval, hit_succeeds, mitigated_damage
from verify_cpp import extract_function


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    signatures = ('double Mob::RollD20(', 'bool Mob::CheckHitChance(',
                  'void Mob::MeleeMitigation(')
    bodies = {s:extract_function(raw.decode(), s) for s in signatures}
    harness = r'''
#include <algorithm>
#include <iostream>
#include <stdexcept>
namespace EQ { template<class T> T Clamp(T n,T low,T high) { return std::clamp(n,low,high); } }
#define Log(...)
struct Rules { int LevelDifferenceRollCheck; double LevelDifferenceRollBonus; } rules;
#define RuleI(category,name) rules.name
#define RuleR(category,name) rules.name
struct Random {
    int a=0,b=0,calls=0; bool tie=false;
    int Roll0(int maximum) {
        int result = calls++ ? b : a;
        if (result < 0 || (maximum > 1 && result >= maximum)) throw std::runtime_error("Invalid controlled roll");
        return result;
    }
    bool Roll(int chance) { return tie; }
};
struct Zone { Random random; } fixture_zone, *zone=&fixture_zone;
struct DamageHitInfo { int tohit=0, offense=0, base_damage=0, damage_done=1; };
struct ExtraAttackOptions { float armor_pen_percent=0; int armor_pen_flat=0; };
struct Mob {
    int avoidance=1, mitigation=1, level=50;
    bool client=false, sitting=false;
    bool IsOfClientBotMerc() { return client; }
    bool IsClient() { return client; }
    bool IsSitting() { return sitting; }
    int GetTotalDefense() { return avoidance; }
    int GetMitigationAC() { return mitigation; }
    int GetLevel() { return level; }
    const char* GetName() { return "fixture"; }
    double RollD20(int,int);
    bool CheckHitChance(Mob*,DamageHitInfo&);
    void MeleeMitigation(Mob*,DamageHitInfo&,ExtraAttackOptions*);
};
''' + '\n'.join(bodies.values()) + r'''
int main() {
    int accuracy,avoidance,hit_a,hit_b,tie,offense,mitigation,atk,def,sitting,base,level_diff;
    while (std::cin >> accuracy >> avoidance >> hit_a >> hit_b >> tie >> offense >> mitigation
           >> atk >> def >> sitting >> base >> level_diff >> rules.LevelDifferenceRollCheck
           >> rules.LevelDifferenceRollBonus) {
        Mob attacker, defender;
        defender.client=true; defender.sitting=sitting; defender.avoidance=avoidance;
        defender.mitigation=mitigation; attacker.level=defender.level+level_diff;
        DamageHitInfo hit; hit.tohit=accuracy; hit.offense=offense; hit.base_damage=base;
        zone->random={hit_a,hit_b,0,tie!=0};
        bool success=defender.CheckHitChance(&attacker,hit);
        zone->random={atk,def,0,false};
        double interval=defender.RollD20(offense,mitigation);
        zone->random={atk,def,0,false};
        defender.MeleeMitigation(&attacker,hit,nullptr);
        std::cout << success << ' ' << interval << ' ' << hit.damage_done << '\n';
    }
}
'''
    rng = random.Random(20260912)
    rows = []
    for _ in range(5000):
        accuracy, avoidance = (rng.choice((-1, 0, 1, rng.randint(2, 2000))) for _ in range(2))
        offense, mitigation = rng.randint(0, 3000), rng.randint(0, 3000)
        rows.append((accuracy, avoidance, rng.randrange(max(1, accuracy)),
                     rng.randrange(max(1, avoidance)), rng.randrange(2), offense, mitigation,
                     rng.randrange(offense+5), rng.randrange(mitigation+5), rng.randrange(2),
                     rng.randint(0, 10000), rng.randint(-20, 20), rng.choice((-1, 0, 5, 10)),
                     rng.choice((0, 0.1, 0.5, 1.0))))
    binary = '/tmp/nightcap-melee-oracle-' + uuid.uuid4().hex
    container = 'akk-stack-eqemu-server-1'
    try:
        subprocess.run(['docker', 'exec', '-i', container, 'g++', '-std=c++17', '-O2',
                        '-x', 'c++', '-o', binary, '-'], input=harness, text=True,
                       capture_output=True, check=True)
        result = subprocess.run(['docker', 'exec', '-i', container, binary],
                                input=''.join(' '.join(map(str,r))+'\n' for r in rows),
                                text=True, capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(error.stderr) from error
    finally:
        subprocess.run(['docker', 'exec', container, 'rm', '-f', binary], check=True)
    outputs = [line.split() for line in result.stdout.splitlines()]
    if len(outputs) != len(rows) or any(len(row) != 3 for row in outputs):
        raise ValueError('Incomplete native melee results')
    mismatches = []
    for row, result in zip(rows, outputs):
        accuracy,avoidance,hit_a,hit_b,tie,offense,mitigation,atk,defense,sitting,base,diff,check,bonus = row
        hit = hit_succeeds(accuracy, avoidance, hit_a, hit_b, bool(tie), sitting=bool(sitting))
        interval = damage_interval(offense, mitigation, atk, defense, sitting=bool(sitting))
        damage = mitigated_damage(base, interval, level_difference=diff,
                                  level_check=check, level_bonus=bonus)
        actual = (int(hit), interval, damage)
        native = (int(result[0]), float(result[1]), int(result[2]))
        if actual != native:
            mismatches.append({'input':row, 'cpp':native, 'python':actual})
    report = {'captured_at':datetime.now(timezone.utc).isoformat(),
              'source_sha256':hashlib.sha256(raw).hexdigest(),
              'functions_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in bodies.items()},
              'cases':len(rows), 'outputs_compared_per_case':3, 'mismatches':mismatches,
              'scope':'Controlled RollD20, hit check, and mitigation; excludes AC/bonus resolution, PvP, armor penetration, outgoing modifiers, and attack scheduling'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(mismatches))


if __name__ == '__main__':
    raise SystemExit(main())
