"""Differential-check the Python port against the actual C++ function body."""
import argparse
import hashlib
import itertools
import json
import random
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from formulas import SpellRules, extra_spell_amount


def extract_function(source, signature):
    if source.count(signature) != 1:
        raise ValueError('Expected exactly one source function signature')
    start = source.index(signature)
    body_start = source.index('{', start)
    depth = 0
    for end in range(body_start, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if depth == 0:
            return source[start:end + 1]
    raise ValueError('Unclosed function body')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    body = extract_function(raw.decode('utf-8'), 'int64 Mob::GetExtraSpellAmt(')
    harness = r'''
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
using int64 = int64_t;
using uint16 = uint16_t;
struct Spell { int cast_time, recast_time, recovery_time; } spells[1];
struct Rules { bool FlatItemExtraSpellAmt, ItemExtraSpellAmtCalcAsPercent; } rules;
#define RuleB(category, name) (rules.name)
struct Mob { int64 GetExtraSpellAmt(uint16, int64, int64); };
''' + body + r'''
int main() {
    Mob mob;
    int64 base, bonus;
    while (std::cin >> base >> bonus >> rules.FlatItemExtraSpellAmt
           >> rules.ItemExtraSpellAmtCalcAsPercent >> spells[0].cast_time
           >> spells[0].recast_time >> spells[0].recovery_time) {
        std::cout << mob.GetExtraSpellAmt(0, bonus, base) << '\n';
    }
}
'''
    binary = '/tmp/nightcap-balance-oracle-' + uuid.uuid4().hex
    container = 'akk-stack-eqemu-server-1'
    subprocess.run(['docker', 'exec', '-i', container, 'g++', '-std=c++17',
                    '-O2', '-x', 'c++', '-o', binary, '-'], input=harness,
                   text=True, capture_output=True, check=True)
    cases = list(itertools.product(
        (0, 1, 3, 99, 100, 1000, -1000, 10000), (0, 1, 20, 249, 250, 440, 500),
        (0, 1), (0, 1), (0, 1, 2499, 2500, 2501, 6999, 7000, 10000)))
    rows = [(*case, 0, 0) for case in cases]
    rng = random.Random(20260912)
    rows += [(rng.randint(-100000, 100000), rng.randint(0, 1000),
              rng.randrange(2), rng.randrange(2), rng.randint(0, 30000),
              rng.randint(0, 60000), rng.randint(0, 15000)) for _ in range(1000)]
    try:
        result = subprocess.run(['docker', 'exec', '-i', container, binary],
                                input=''.join(' '.join(map(str, row)) + '\n' for row in rows),
                                text=True, capture_output=True, check=True)
    finally:
        subprocess.run(['docker', 'exec', container, 'rm', '-f', binary], check=True)
    outputs = [int(value) for value in result.stdout.splitlines()]
    if len(outputs) != len(rows):
        raise ValueError('C++ oracle returned an incomplete result set')
    mismatches = []
    for row, expected in zip(rows, outputs):
        base, bonus, flat, percent, cast, recast, recovery = row
        actual = extra_spell_amount(base, bonus, SpellRules(bool(flat), bool(percent)), cast, recast, recovery)
        if actual != expected:
            mismatches.append({'input': row, 'cpp': expected, 'python': actual})
    report = {'captured_at': datetime.now(timezone.utc).isoformat(),
              'source_sha256': hashlib.sha256(raw).hexdigest(),
              'function_sha256': hashlib.sha256(body.encode()).hexdigest(),
              'cases': len(rows), 'mismatches': mismatches,
              'scope': 'GetExtraSpellAmt only; not full spell resolution or combat simulation'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(mismatches))


if __name__ == '__main__':
    raise SystemExit(main())
