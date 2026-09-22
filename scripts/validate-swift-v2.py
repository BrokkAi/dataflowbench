#!/usr/bin/env python3
"""Compile the new v2 inputs; execute only Result controls, never native fixtures."""
import argparse
import importlib.util
from pathlib import Path
import sys
import tempfile
from swift_population_v2 import ROOT, audit, runtime_control_allowed, sha

spec=importlib.util.spec_from_file_location('swift_v1_validation',Path(__file__).with_name('validate-swift-fixtures.py'))
validation=importlib.util.module_from_spec(spec);sys.modules[spec.name]=validation;spec.loader.exec_module(validation)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=['local','github-xcode27'],default='local')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    manifest,additions=audit()
    evidence=validation.Evidence(validation.create_evidence_directory(args.output,ROOT))
    env=validation.child_environment(args.profile)
    evidence.data['profile']=args.profile
    evidence.data['validator']={'path':str(Path(__file__).resolve()),'sha256':sha(Path(__file__))}
    evidence.data['execution_environment']={'allowlist':sorted(validation.SAFE_ENV_KEYS),'sanitized':env}
    try:
        witness=validation.witness_environment(None,evidence,profile=args.profile,child_env=env)
        evidence.data['population']={'id':'swift-synthetic-v2','fixture_revision':manifest['fixture_revision'],'manifest_sha256':sha(ROOT/'populations/swift-synthetic-v2.json')}
        evidence.data['policy']={'compile_only':'all 12 tool-native additions; no shell or store execution','concrete_controls':'only two Result extension cases; source values 7 and 19','prior_population':'v1 validated independently and unchanged'}
        for path,metadata in additions:
            files=tuple(metadata['fixture_files'])
            case=validation.SwiftCase(path.parent,metadata,sha(path),files,tuple({'path':name,'sha256':sha(path.parent/name),'bytes':(path.parent/name).stat().st_size} for name in files))
            evidence.data['metadata_digests'].append({'case_id':case.case_id,'sha256':case.metadata_digest})
            evidence.data['cases'].append({'case_id':case.case_id,'fixture_files':list(case.source_records),'policy':'concrete-control' if runtime_control_allowed(metadata) else 'compile-only'})
            evidence.write()
            with tempfile.TemporaryDirectory(prefix='dfb-swift-v2-compile-') as temp:
                validation.compile_sources(witness['compiler_path'],case.fixture_paths,sdk_path=witness['sdk_path'],output_dir=Path(temp),output_name='fixture',cwd=path.parent,evidence=evidence,child_env=env,case_id=case.case_id,instrumented=False,source_value=None)
            if runtime_control_allowed(metadata):
                validation.run_control(case,witness['compiler_path'],witness['sdk_path'],evidence,env)
            else:
                evidence.event({'kind':'control-skipped','case_id':case.case_id,'reason':'tool-native compile-only; must not invoke shell or mutate platform store'})
            print(case.case_id, 'concrete-control' if runtime_control_allowed(metadata) else 'compile-only',flush=True)
        evidence.data['status']='passed'
    except Exception as error:
        evidence.data['status']='failed';evidence.data['error']=str(error)
        raise
    finally:
        evidence.write()

if __name__=='__main__':main()
