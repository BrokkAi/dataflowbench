#!/usr/bin/env python3
"""Prepare prospective Joern integration or run separately reserved controls."""
import argparse
from pathlib import Path
from joern_normal_runner_v1 import ROOT, prepare, controls, execute, read


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare');p.add_argument('--directory',type=Path,required=True)
    for name in ['joern','java-home','compiler','sdk']:p.add_argument('--'+name,required=True)
    for mode in ['controls','execute']:
        p=sub.add_parser(mode);p.add_argument('--plan',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reservation',type=Path,required=True)
        if mode=='controls':p.add_argument('--controls',required=True)
    args=parser.parse_args()
    if args.mode=='prepare':
        prepare(ROOT,args.directory.resolve(),{k:getattr(args,k) for k in ['joern','java_home','compiler','sdk']})
        print('Prepared only: current108 partition unresolved, no native invocation or reservation.')
    elif args.mode=='controls':controls(ROOT,args.plan,args.controls,args.output.resolve(),read(args.reservation))
    else:execute(ROOT,args.plan,args.output.resolve(),read(args.reservation))


if __name__=='__main__':main()
