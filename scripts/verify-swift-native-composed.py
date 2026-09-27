#!/usr/bin/env python3
"""Replay composed native observations; expected outcomes are never selection gates."""
import argparse
import json
from pathlib import Path
from swift_native_composed import ROOT,replay

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attempt',type=Path,default=ROOT/'evidence/swift-native-composed-v1/attempt-01')
    p.add_argument('--write',action='store_true');args=p.parse_args()
    result=replay(ROOT,args.attempt)
    content=json.dumps(result,indent=2)+'\n';output=args.attempt.parent/(args.attempt.name+'-observations.json')
    if args.write:
        if output.exists():raise FileExistsError(output)
        output.write_text(content)
    elif output.read_text()!=content:raise ValueError('observation replay changed')
    from collections import Counter
    print('Native composed raw:',dict(Counter(r['raw_outcome'] for r in result['results'])))
    print('Normalized:',dict(Counter(r['outcome'] for r in result['results'])), '; no scoring or fresh extraction')
