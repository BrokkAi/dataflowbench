#!/usr/bin/env python3
"""Verify immutable canonical sanitizer observations without activating scores."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
from swift_extraction_integrity import inspect_logs

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/swift-resolved-native-v1'
PLAN=ROOT/'adapters/codeql/swift-resolved-native-v1/canonical-sanitizer-plan.json'
PROFILES=('adapter-patched-resolved-sanitizer',)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def manifest(directory):
    values=read(directory/'manifest.json')
    require(set(values)=={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'manifest.json'},'artifact closure')
    for name,digest in values.items():require(sha(directory/name)==digest,'artifact digest: '+name)

def check_semantics(rows,case,observation):
    source=case['source_anchors'][0]['line_hint'];sink=case['sink_anchors'][0]['line_hint'];expected=bool(case['expected_flows'])
    require(set(observation['lanes'])==set(PROFILES),'lane set')
    require(all(r[2] in PROFILES for r in rows['roles']) and all(r[3] in PROFILES for r in rows['flow']),'profile attribution')
    for profile in PROFILES:
        sources=[r for r in rows['roles'] if r[2]==profile and r[3]!='sink'];sinks=[r for r in rows['roles'] if r[2:]==[profile,'sink']];flows=[r for r in rows['flow'] if r[3]==profile]
        require(len(sources)==1 and sources[0][0]==source and sources[0][3]=='environment','source roles')
        require(len(sinks)==2 and all(r[0]==sink for r in sinks),'sink roles')
        require(flows==([[source,sink,87,profile]] if expected else []),'canonical expected flow')
        projected={'source_rows':sources,'sink_rows':sinks,'flow_rows':flows,'source_anchor_recognized':True,'sink_anchor_recognized':True,'observed_anchor_flow':expected,'matches_case_expectation':True}
        require(observation['lanes'][profile]==projected,'observation projection')
    require(any(r[0]==source and r[1:5]==['Foundation','Foundation','ProcessInfo','environment'] for r in rows['identity']), 'resolved source identity')
    identities=rows['conversion-identity']
    if expected:
        require(identities==[], 'unexpected positive conversion')
        require(not any(r[4] is True for r in rows['barriers']), 'positive scalar barrier')
    else:
        require(len(identities)==2 and {tuple(r[2:7]) for r in identities}=={
            ('Swift','Swift','FixedWidthInteger','init(_:radix:)',2),
            ('Swift','Swift','String','init(_:radix:uppercase:)',3)},'resolved numeric conversion identity')
        require(any(r[0]==6 and r[2:5]==['Swift','Int',True] for r in rows['barriers']), 'real scalar barrier')
    for name in ['barriers','numeric-bases','conversion-identity']:
        require(observation['sanitizer_observations'][name]=={'row_count':len(rows[name]),'rows':rows[name]},'sanitizer observation projection')

def verify(attempt=None):
    attempt=Path(attempt) if attempt else BASE/'canonical-sanitizer-attempt-01'
    spec=importlib.util.spec_from_file_location('runner',ROOT/'scripts/run-swift-resolved-sanitizer-qualification.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    plan,config,population=runner.verify_preregistration(False)
    manifest(attempt);run=read(attempt/'run.json');runtime=read(attempt/'runtime.json')
    require(run['scored_activation'] is False and run['plan_sha256']==sha(PLAN) and run['configuration']==config,'run provenance/scope')
    require(run['status']=='retained-non-scored-attempts' and [a['case_id'] for a in run['attempts']]==plan['cases'] and all(a['status']=='observed-unqualified' for a in run['attempts']),'pair incomplete')
    require(runtime['runtime_manifest_sha256']==sha(ROOT/plan['runtime_manifest']) and runtime['pack_version']=='6.8.4-dfb.4' and runtime['pack_files_verified']==3398,'runtime library identity')
    assets=read(ROOT/'evidence/swift-candidate-qualification-220/codeql-runtime/assets.json');prior=read(ROOT/'evidence/swift-foundation-sources-v1/control-attempt-01/witness.json')
    require(runtime['assets']==assets and runtime['compiler_sha256']==prior['compiler_sha256'] and runtime['sdk_settings_sha256']==plan['sdk_settings_sha256'],'runtime tools')
    entries={c['id']:c for c in population['cases']}
    for case_id in plan['cases']:
        entry=entries[case_id];path=ROOT/entry['path'];case=read(path);source=(path.parent/'main.swift').read_bytes();directory=attempt/case_id;probe=directory/'probe'
        require((directory/'canonical-case.json').read_bytes()==path.read_bytes(),'canonical case metadata')
        join=read(directory/'canonical-join.json');require(join=={'case_id':case_id,'canonical_entry':entry,'population':population['population'],'fixture_revision':population['fixture_revision'],'staged_source_sha256':hashlib.sha256(source).hexdigest()},'immutable canonical join')
        require((directory/'control/main.swift').read_bytes()==source and (probe/'main.swift').read_bytes()==source,'canonical source')
        manifest(probe);witness=read(probe/'witness.json');require(witness['source_commit']==run['source_commit'] and not witness.get('probe_error') and not witness.get('cleanup_error') and witness['status']=='unqualified','probe provenance')
        require(witness['compiler_sha256']==runtime['compiler_sha256'] and witness['extractor_sha256']==assets['codeql/swift/tools/osx64/extractor.real'],'probe runtime identity')
        require(inspect_logs(probe/'log/swift/extractor')['ready_for_observation'],'extractor errors')
        measurements=runner.inspect_phases(probe,witness)
        for name in plan['query_files']:require((probe/'queries'/Path(name).name).read_bytes()==(ROOT/name).read_bytes(),'executed query identity')
        observation=read(directory/'observation.json');require(observation['status']=='observed-unqualified' and observation['scored_activation'] is False and observation['aggregate_memory_compliance']==observation['semantic_completeness']=='unproven','observation promotion')
        require(observation['phase_measurements']==measurements,'measurement join')
        with zipfile.ZipFile(directory/'source.zip') as z:
            members=[n for n in z.namelist() if n.endswith('/source/main.swift')];require(len(members)==1 and z.read(members[0])==source,'archived canonical source')
        require(observation['archive_sha256']==sha(directory/'source.zip') and observation['archive_member']==members[0] and observation['source_sha256']==hashlib.sha256(source).hexdigest(),'archive join')
        check_semantics({n:read(probe/(n+'.json'))['#select']['tuples'] for n in runner.QUERIES},case,observation)
    print('Canonical sanitizer pair verified in the resolved patched lane; non-scored and not whole-profile qualification.')

if __name__=='__main__':verify()
