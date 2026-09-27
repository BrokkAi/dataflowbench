#!/usr/bin/env python3
"""Recompute exact-fixture observations from the retained artifact closure."""
import argparse
import json
from pathlib import Path
from swift_opaque_v3_evidence import ROOT, verify_attempt, read
from swift_opaque_v3_provenance import verify_commands

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',type=Path,default=ROOT/'evidence/swift-opaque-v3/attempt-01')
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    result=verify_attempt(ROOT,args.attempt)
    verify_commands(ROOT,args.attempt,read(ROOT/'adapters/codeql/swift-opaque-v3/plan.json'))
    path=args.attempt.parent/(args.attempt.name+'-observations.json')
    content=json.dumps(result,indent=2)+'\n'
    if args.write:
        if path.exists():raise FileExistsError(path)
        path.write_text(content)
    elif path.read_text()!=content:
        raise ValueError('retained observations differ from bound evidence')
    print('Exact staged opaque evidence bound; '+str(len(result['results']))+' rows; no scored activation.')
