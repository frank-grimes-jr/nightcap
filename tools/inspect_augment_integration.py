"""Bounded, read-only HTML source comparison for the augment integration."""
import difflib
import json
import re
import subprocess


def article(ref, name):
    return json.loads(subprocess.check_output(['git', 'show', ref + ':wiki/articles/' + name + '.json']).decode('utf-8'))


for name in ('features', 'recent-changes', 'unreleased', 'zone-hunt'):
    base = article('1b443b5a', name)
    dev = article('origin/dev', name)
    tokenize = lambda s: re.split(r'(?=<(?:h[1-6]|p|section|aside|div|nav|details)\b)', s)
    a, b = tokenize(base['body']), tokenize(dev['body'])
    print(name)
    for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != 'equal':
            print(tag, 'BASE:', ''.join(a[i:j])[:1300], 'DEV:', ''.join(b[k:l])[:2000])
