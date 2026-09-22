#!/usr/bin/env python3
"""Verify load-bearing Swift model controls; these are not scored fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('evidence/codeql-swift/activation-218/final-activation-v2')
EXPECT={
 'models': {'dfb/swift-modeling': {6,16,18,22,27,43,47,51}, 'dfb/swift-modeling-off': {26,27,48}},
 'receiver-positive': {'dfb/swift-modeling': {8}, 'dfb/swift-modeling-off': set()},
 'receiver-negative': {'dfb/swift-modeling': set(), 'dfb/swift-modeling-off': set()},
 'calibration-on': {'dfb/swift-kernel': {9}},
 'calibration-off': {'dfb/swift-kernel': {10}},
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify():
 evidence={}
 for name, expected in EXPECT.items():
  result_path=BASE/(name+'.sarif');command_path=BASE/(name+'.command.json')
  command=json.loads((ROOT/command_path).read_text())
  if command.get('exit_status') != 0 or '--rerun' not in command['argv']:raise ValueError('control did not freshly execute: '+name)
  runs=json.loads((ROOT/result_path).read_text()).get('runs',[])
  if len(runs)!=1:raise ValueError('missing control run')
  run=runs[0];invocations=run.get('invocations',[])
  if not invocations or any(i.get('executionSuccessful') is not True for i in invocations):raise ValueError('failed invocation')
  for i in invocations:
   if any(n.get('level')=='error' for key in ('toolExecutionNotifications','toolConfigurationNotifications') for n in i.get(key,[])):raise ValueError('error notification in '+name)
  findings={rule:set() for rule in expected};roles=set()
  for r in run.get('results',[]):
   rule=r.get('ruleId','')
   if rule.endswith('-endpoint-probe'):
    roles.update(r.get('message',{}).get('text','').splitlines());continue
   if rule not in findings:raise ValueError('unexpected rule: '+rule)
   location=r['locations'][0]['physicalLocation']
   if location['artifactLocation']['uri']!='main.swift':raise ValueError('wrong control file')
   findings[rule].add(location['region']['startLine'])
  if findings!=expected:raise ValueError('load-bearing control mismatch: '+name+' '+repr(findings))
  if roles != {'Benchmark source endpoint observed.','Benchmark sink endpoint observed.'}:raise ValueError('missing control endpoints')
  for p in (result_path,command_path):evidence[str(p)]=sha(ROOT/p)
 queries=json.loads((ROOT/BASE/'query-hashes.json').read_text())
 for path,digest in queries.items():
  if sha(ROOT/path)!=digest:raise ValueError('query drift: '+path)
 return {'schema_version':1,'status':'active','scope':'modeling-and-calibration','query_sha256':queries,'evidence_sha256':evidence}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write-certificate',type=Path);args=parser.parse_args();certificate=verify()
 if args.write_certificate:
  if args.write_certificate.exists():raise ValueError('refusing certificate overwrite')
  args.write_certificate.write_text(json.dumps(certificate,indent=2)+'\n')
 print('Verified controlled-model and calibration activation; no scored result.')
