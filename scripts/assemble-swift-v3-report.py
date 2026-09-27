#!/usr/bin/env python3
"""Assemble a new contract-bound incomplete coverage report without overwrite."""
import argparse,json
from pathlib import Path
from swift_v3_reports import ROOT,assemble,read

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    output=args.output.resolve();output.relative_to(ROOT/'reports/swift-v3')
    report=assemble(ROOT,read(args.run))
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
