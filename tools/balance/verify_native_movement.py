"""Validate bounded, applied player movement in native encounter reports."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def verify(report, *, require_movement=False):
    encounter = report['encounter']
    movement = encounter['movement']
    events = movement['events']
    if require_movement and not events:
        raise ValueError('Expected pursuit activity')
    previous = 0
    distance = 0.0
    for event in events:
        if not previous < event['ms'] <= encounter['elapsed_ms'] or event['ms'] % 50:
            raise ValueError('Invalid movement clock')
        previous = event['ms']
        if event['controlled'] or event['casting'] or event['in_range'] or event['speed'] <= 0:
            raise ValueError('Movement requested while inhibited or already in melee range')
        for field in ('from', 'to', 'actual'):
            if len(event[field]) != 3 or not all(math.isfinite(v) for v in event[field]):
                raise ValueError('Invalid movement coordinates')
        expected_limit = 0.05 * event['speed'] * 0.4 * 1.45
        length = math.dist(event['from'], event['to'])
        if abs(event['limit'] - expected_limit) > 1e-5 or length > expected_limit + 1e-4:
            raise ValueError('Player movement exceeds the declared native-speed policy')
        if not event['accepted'] or event['actual'] != event['to']:
            raise ValueError('Position packet did not move the player as reported')
        distance += length
    if events and movement['history_packets'] <= 0:
        raise ValueError('Missing movement-history packet flow')
    trace = encounter['trace']
    returned_to_range = any(
        s['ms'] >= event['ms'] and s['player_combat']['range']
        for event in events for s in trace
    )
    if require_movement and not returned_to_range:
        raise ValueError('Pursuit never restored sampled melee range')
    return {'passed': True, 'movement_packets': len(events), 'distance': distance,
            'returned_to_sampled_melee_range': returned_to_range,
            'history_packets': movement['history_packets'], 'failed_paths': movement['failed_paths'],
            'result': encounter['result'], 'elapsed_ms': encounter['elapsed_ms'],
            'scope': 'Native packet application and bounded mesh pursuit; client physics parity and final balance remain unproven'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-movement', action='store_true')
    parser.add_argument('--matrix-inputs', type=Path)
    args = parser.parse_args()
    raw = args.native.read_bytes()
    report = json.loads(gzip.decompress(raw) if args.native.suffix == '.gz' else raw)
    if args.matrix_inputs:
        from encounter_matrix import verify_matrix
        if args.require_movement:
            raise ValueError('Use the single encounter control to require pursuit in a particular case')
        inputs = json.loads(args.matrix_inputs.read_text())
        verify_matrix(inputs, report)
        checks = [verify(run['report']) | {'id': run['id']} for run in report['runs']]
        result = {'cases': len(checks), 'movement_cases': sum(c['movement_packets'] > 0 for c in checks),
                  'checks': checks, 'input_sha256': hashlib.sha256(args.matrix_inputs.read_bytes()).hexdigest()}
    else:
        result = verify(report, require_movement=args.require_movement)
    result['native_sha256'] = hashlib.sha256(raw).hexdigest()
    args.output.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
