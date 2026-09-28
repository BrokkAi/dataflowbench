#!/usr/bin/env python3
"""Check preserved diagnostic bytes and reproduce the known rejection; no clean report."""
import json,tarfile,tempfile
from pathlib import Path
from collections import Counter
from swift_v3_reports import ROOT,read,sha,require,inputs
from swift_v3_verify import verify_case


def check(root=ROOT, subset=False):
    evidence=root/('evidence/swift-v3-budget8-75s-record' if subset else 'evidence/swift-v3-full108-60s-record')
    selected_inputs=inputs;replay_case=verify_case
    if subset:
        from swift_v3_reports75 import inputs as selected_inputs
        from swift_v3_verify75 import verify_case as replay_case
    record=read(evidence/'record.json');archive=evidence/'portable-evidence.tar.gz'
    require(record['scope']==('unreportable-eight-case-diagnostic-archive' if subset else 'unreportable-full108-diagnostic-archive') and record['full_database_replay_portable'] is False,'diagnostic scope')
    require(sha(archive)==record['archive_sha256'],'archive digest')
    with tempfile.TemporaryDirectory() as temporary:
        directory=Path(temporary)
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                path=Path(member.name)
                require(member.isfile() and not path.is_absolute() and '..' not in path.parts,'archive path/type')
                target=directory/path;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())
        require(sha(directory/'export-manifest.json')==record['export_manifest_sha256'],'export manifest')
        manifest=read(directory/'export-manifest.json')
        require({str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}-{'export-manifest.json'}==set(manifest['files']),'portable closure')
        for name,digest in manifest['files'].items():require(sha(directory/name)==digest,'portable digest')
        audit=read(directory/'replay-audit.json');require(audit==record['replay_audit'],'audit binding')
        run=read(directory/'run.json');launch=read(directory/'run-plan.json');pop,contract,cases,ph,ch=selected_inputs(root)
        if subset:
            selection=read(root/'adapters/codeql/swift-v3-75/selection.json')
            with tarfile.open(root/'evidence/swift-v3-full108-60s-record/portable-evidence.tar.gz') as original_archive:
                original_run_bytes=original_archive.extractfile('run.json').read()
                import hashlib
                require(hashlib.sha256(original_run_bytes).hexdigest()==selection['original_run_sha256'],'original run selection binding')
                original_run=json.loads(original_run_bytes);exhausted=[]
                for original_row in original_run['results']:
                    original_raw=json.loads(original_archive.extractfile(original_row['case_id']+'/observation.json').read())
                    if original_raw.get('failure_kind')=='timeout':
                        exhausted.append({'case_id':original_row['case_id'],'raw_sha256':original_row['raw_sha256'],'diagnostics':original_raw['diagnostics']})
                require(exhausted==selection['cases'],'exact original budget-exhausted selection')
        selected=read(root/'adapters/codeql/swift-v3-75/selection.json')['case_ids'] if subset else list(cases)
        require(len(run['results'])==len(selected) and [r['case_id'] for r in run['results']]==selected,'population membership')
        require(run['population_sha256']==ph and run['contract_sha256']==ch and run['phases']==contract['phases'],'original 60s contract')
        require(launch['source_commit']==record['source_commit'],'source revision')
        require(sha(directory/'preregistered-runner-plan.json')==launch['runner_plan_sha256'],'plan binding')
        errors=[];changed=[]
        for row in run['results']:
            base=directory/row['case_id'];raw=read(base/'observation.json')
            require(sha(base/'observation.json')==row['raw_sha256'],'raw binding')
            require(sha(base/'artifacts.json')==raw['artifacts_sha256'],'original artifact manifest')
            require(raw['case_id']==row['case_id'] and raw['outcome']==row['outcome'],'row identity')
            original=read(base/'artifacts.json')
            for path in base.rglob('*'):
                if path.is_file() and path.name not in ['artifacts.json','observation.json']:
                    name=str(path.relative_to(base))
                    if sha(path)!=original.get(name):changed.append((row['case_id'],name))
            try:replay_case(root,base,cases[row['case_id']],raw,launch['paths'])
            except ValueError as error:errors.append({'case_id':row['case_id'],'reason':str(error)})
        expected=[e for e in audit['case_replay_errors'] if e['reason'] not in ['artifact closure changed','artifact digest changed','artifact symlink']]
        require(errors==expected and (errors or subset),'known rejection must remain observable')
        expected_changed={(e['case_id'],e['path']) for e in audit['case_replay_errors'] if e['reason']=='artifact digest changed'}
        require(set(changed)<=expected_changed,'unexpected portable digest drift')
        require(dict(Counter(r['outcome'] for r in run['results']))==audit['raw_outcomes'],'raw census')
        require(read(directory/'report-status.json')['status']=='unreportable' and not (directory/'coverage-report.json').exists(),'no verified report')
        return errors

if __name__=='__main__':
    print('Full108 diagnostic bytes checked; reproduced rejection:',check())
    print('Eight-case diagnostic bytes checked; per-case replay:',check(subset=True))
    print('Full database closure remains invalid/local-only; no normalized report emitted.')
