#!/usr/bin/env python3
"""Reconcile every retained Swift Joern assertion, native document and command manifest."""
import collections
import json
from pathlib import Path
from joern_swift import ROOT, normalize, sha


def audit():
    # Archived attempts remain immutable, including their original configuration and fields.
    for manifest_path in (ROOT/'evidence/joern-swift').rglob('manifest.json'):
        entries=json.loads(manifest_path.read_text())
        for name,digest in entries.items():
            assert sha(manifest_path.parent/name)==digest,('archived evidence digest',str(manifest_path),name)
    cases={}
    for entry in json.loads((ROOT/'populations/swift-synthetic-v1.json').read_text())['cases']:
        path=ROOT/entry['path']
        case=json.loads(path.read_text());cases[case['id']]=(path,case)
    summary={}
    for tier,suffix in [('core','kernel'),('modeling','modeling'),('calibration','calibration')]:
        report=json.loads((ROOT/f'reports/joern-swift-{suffix}.json').read_text())
        expected={key for key,(_,case) in cases.items() if case['score_tier']==tier}
        ids=[r['case_id'] for r in report['results']]
        assert set(ids)==expected and len(ids)==len(expected),('population',tier)
        outcomes=collections.Counter();native=collections.Counter();seconds=[];rss=[];errors=collections.Counter()
        for result in report['results']:
            identifier=result['case_id'];case_path,case=cases[identifier]
            directory=ROOT/f'reports/raw/joern-swift-{suffix}'/identifier
            manifest=json.loads((directory/'manifest.json').read_text())
            actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p.name!='manifest.json'}
            assert actual==set(manifest),('manifest inventory',identifier)
            for name,digest in manifest.items():
                assert sha(directory/name)==digest,('evidence digest',identifier,name)
            execution=json.loads((directory/'execution.json').read_text())
            assert result['outcome']==execution['outcome'],('outcome',identifier)
            assert result['peak_memory_mb'] is None and execution['peak_memory_mb'] is None
            assert result['raw_output']==f'reports/raw/joern-swift-{suffix}/{identifier}/execution.json'
            if (directory/'graph.json').exists() and 'native_outcome' in execution:
                graph=json.loads((directory/'graph.json').read_text());config=json.loads((directory/'config.json').read_text())
                outcome,diagnostics=normalize(graph,config)
                assert execution['native_outcome']==outcome,('native outcome',identifier,diagnostics)
                native[outcome]+=1
            if execution['outcome']=='unsupported':
                assert not (directory/'frontend').exists() and not (directory/'query').exists()
            else:
                hashes=json.loads((directory/'fixture-hashes.json').read_text())
                assert hashes[str(case_path.relative_to(ROOT))]==sha(case_path),('case metadata',identifier)
                for name in case['fixture_files']:assert hashes[name]==sha(case_path.parent/name),('fixture',identifier,name)
            if execution.get('time_maxrss_mb') is not None:rss.append(execution['time_maxrss_mb'])
            seconds.append(execution['phases']['total']);outcomes[execution['outcome']]+=1
            if execution['outcome']=='runner-error':errors.update(execution['diagnostics'])
            assert execution['outcome'] not in ['reached','not-reached'],'unqualified determinate outcome'
        summary[tier]=dict(assertions=len(ids),outcomes=dict(sorted(outcomes.items())),
                           provisional_native_observations=dict(sorted(native.items())),
                           total_seconds_range=[min(seconds),max(seconds)],
                           individual_maxrss_mib_range=[min(rss),max(rss)] if rss else None,
                           runner_error_diagnostics=dict(sorted(errors.items())),configuration_hash=report['configuration_hash'])
    return summary


if __name__=='__main__':print(json.dumps(audit(),indent=2,sort_keys=True))
