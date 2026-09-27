"""Portable command provenance checks over the preregistered opaque artifacts."""
from pathlib import Path
import shlex
from swift_opaque_v3_evidence import read, require, sha


def verify_commands(root, attempt, plan):
    run = read(attempt/'run.json')
    require(run['scored_activation'] is False and run['resource_qualification'] == 'unavailable', 'run scope')
    expected_packs = len(read(root/'evidence/swift-candidate-qualification-220/codeql-runtime/resolved-pack-files.json'))
    require(run['pack_files_verified'] == expected_packs, 'pack witness count')
    for case_id, record in run['cases'].items():
        if record['status'] != 'observed':
            continue
        directory = attempt/case_id; probe=directory/'probe'; witness=read(probe/'witness.json')
        argv=record['argv']
        def option(key):
            require(argv.count(key)==1, 'unique runner argument: '+key)
            return argv[argv.index(key)+1]
        old_probe=Path(option('--output')); packs=option('--packs'); cli=option('--codeql')
        require(old_probe.parts[-3:] == (attempt.name,case_id,'probe'), 'case output binding')
        require(option('--compiler')==witness['compiler'] and option('--sdk')==witness['sdk'] and
                option('--target')==witness['target']=='arm64-apple-macosx26.5', 'toolchain arguments')
        require(option('--control-directory')==str(old_probe.parent/'input'), 'control path')
        db=Path(witness['retained_scratch'])/'db'
        create=read(probe/'database-create.command.json')
        require(create['argv'][:4]==[cli,'database','create',str(db)], 'extraction command')
        command=[a for a in create['argv'] if a.startswith('--command=')]
        require(len(command)==1, 'compiler command')
        compiler=shlex.split(command[0].split('=',1)[1])
        require(compiler[0]==witness['compiler'] and
                str(db.parent/'source/main.swift') in compiler and
                compiler[compiler.index('-sdk')+1]==witness['sdk'] and
                compiler[compiler.index('-target')+1]==witness['target'], 'compiler source/toolchain')
        require(create['deadline_seconds']==150 and create['elapsed_seconds']<=150, 'extraction deadline')
        for name in ['roles','flow','identity']:
            query=read(probe/(name+'.command.json'))
            expected=[cli,'query','run',str(old_probe/'queries'/(name+'.ql')),
                      '--database='+str(db),'--output='+str(old_probe/(name+'.bqrs')),
                      '--additional-packs='+packs,'--threads=2','--ram=2048','--timeout=60']
            require(query['argv']==expected, 'query command binding')
            require(query['deadline_seconds']==60 and query['elapsed_seconds']<=60, 'query deadline')
            decode=read(probe/(name+'-decode.command.json'))
            require(decode['argv']==[cli,'bqrs','decode',str(old_probe/(name+'.bqrs')),
                    '--format=json','--output='+str(old_probe/(name+'.json'))], 'decode command binding')
            require((probe/(name+'.bqrs')).stat().st_size>0, 'retained BQRS')
        require(sha(probe/'probe.py')==plan['runner_files']['scripts/probe-swift-v2-codeql.py'] and
                sha(probe/'process-runner.py')==plan['runner_files']['scripts/swift_v2_process.py'] and
                sha(probe/'swift_extraction_integrity.py')==plan['runner_files']['scripts/swift_extraction_integrity.py'], 'retained runner bytes')
