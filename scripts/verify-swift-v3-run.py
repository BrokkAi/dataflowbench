#!/usr/bin/env python3
import argparse
from pathlib import Path
from swift_v3_verify import verify
from swift_v3_reports import ROOT

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);args=p.parse_args()
    print('Verified',len(verify(ROOT,args.directory)['results']),'raw-bound rows; resource qualification unavailable')
