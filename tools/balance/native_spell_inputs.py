"""Add explicit direct-spell probes to the AA candidate matrix.

This roster tests native actions. It is not the complete accessible spellbook or
a claim of optimal rotation, especially while global spell class patches remain.
"""
import argparse
import json
from pathlib import Path


ROSTER = {
    'war-clr-wiz': {'damage': (732,659), 'heal': (9,13)},
    'war-clr-mnk': {'damage': (672,), 'heal': (9,13)},
    'mag-nec-shm': {'damage': (510,114), 'heal': (15,)},
}


def inputs(matrix, samples):
    if not 1 <= samples <= 100000:
        raise ValueError('Expected 1..100000 native samples')
    result = []
    for b in matrix['builds']:
        roster = ROSTER[b['profile']]
        probes = [{'spell_id': sid, 'npc_id': npc} for sid in roster['damage'] for npc in (32040,73057)]
        probes += [{'spell_id': sid} for sid in roster['heal']]
        result.append(b | {'spell_probes':probes})
    return {'spell_samples':samples,'builds':result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aa-inputs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=4096)
    args = parser.parse_args()
    result = inputs(json.loads(args.aa_inputs.read_text()),args.samples)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'builds':len(result['builds']),'actions':sum(len(b['spell_probes']) for b in result['builds']),
                      'samples_per_action':args.samples}))


if __name__ == '__main__':
    main()
