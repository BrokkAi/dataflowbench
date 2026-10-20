#!/usr/bin/env python3
"""Replay fresh Pysa profile controls without treating native silence as clean."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('reports/releases/v0.9.2/qualification/profile-controls')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def entries(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'qualification will not be overwritten')
    bindings = json.loads(args.bindings.read_bytes())
    spec = importlib.util.spec_from_file_location('executor', ROOT / 'scripts/execute-release-v092.py')
    executor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(executor)
    tool = bindings['tool_bindings']['pysa']
    for alias in ['pysa'] + bindings['tool_components']['pysa']:
        executor._check_tool_file(bindings['tool_bindings'][alias], alias)
    captures = {}
    receipts = []
    for control in ('probe-pysa-modeling-load-bearing', 'probe-pysa-native-activation', 'probe-pysa-callee-resolution'):
        folder = ROOT / BASE / (control + '-attempt-02')
        path = folder / 'completed.json'
        data = json.loads(path.read_bytes())
        require(data['control'] == control and data['status'] == 'completed' and data['exit_code'] == 0 and not data['timed_out'] and not data['capacity_loss'] and not data.get('recorder_error'), 'incomplete control ' + control)
        for alias in ['pysa'] + bindings['tool_components']['pysa']:
            require(data['tool_bindings'][alias] == bindings['tool_bindings'][alias], 'control identity differs')
        inputs = {row['path']: row['sha256'] for row in data['source_inputs']}
        require(len(inputs) == len(data['source_inputs']), 'duplicate source inputs')
        expected = {str(path.relative_to(ROOT)) for directory in ('adapters/pysa', 'cases/taint/python') for path in (ROOT / directory).rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        relevant = {name for name in inputs if name.startswith(('adapters/pysa/', 'cases/taint/python/'))}
        require(relevant == expected, 'Pysa source input roster differs')
        script = 'scripts/' + control + '.sh'
        require(inputs[script] == sha(ROOT / script), 'control implementation changed')
        for relative, digest in inputs.items():
            if relative.startswith(('adapters/pysa/', 'cases/taint/python/')):
                require(sha(ROOT / relative) == digest, 'Pysa configuration or fixture changed: ' + relative)
        files = {}
        for row in data['captured_files']:
            captured = Path(row['capture_path'])
            require(captured.resolve().is_relative_to(folder.resolve()) and captured.is_file() and not captured.is_symlink(), 'escaped capture')
            require(sha(captured) == row['sha256'] and captured.stat().st_size == row['bytes'], 'capture changed')
            files[row['execution_relative']] = captured
        require(files, 'empty capture')
        captures[control] = files
        receipts.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
    modeling = captures['probe-pysa-modeling-load-bearing']
    counts = {}
    # Exact immutable probe expectations; no inferred result from process success.
    positives = {'declared-source-positive','declared-sink-positive','opaque-propagator-unmodeled','opaque-propagator-positive','propagator-position-positive','sanitizer-kill-positive','sanitizer-kill-removed','sanitizer-selectivity-positive','summary-through-positive','summary-through-body-control','summary-field-positive','entrypoint-parameter-positive','entrypoint-selectivity-positive'}
    for relative, path in modeling.items():
        if path.suffix != '.json':
            continue
        rows = entries(path)
        require(rows and rows[0].get('file_version') == 3, 'missing native Pysa header')
        count = sum(row.get('kind') == 'issue' for row in rows)
        counts[path.stem] = count
        require(count == int(path.stem in positives), 'model control observation differs: ' + path.stem)
        require(any(row.get('kind') == 'model' for row in rows), 'models not bound')
    negatives = {'declared-source-negative','declared-source-removed','declared-sink-negative','opaque-propagator-negative','opaque-propagator-tito-removed','propagator-position-negative','sanitizer-kill-negative','sanitizer-selectivity-negative','summary-through-negative','summary-through-tito-removed','summary-field-negative','summary-field-removed','entrypoint-parameter-negative','entrypoint-parameter-removed','entrypoint-selectivity-negative'}
    require(set(counts) == positives | negatives, 'model control roster differs')
    native = captures['probe-pysa-native-activation']
    prefix = 'reports/raw/amendment-a17-pysa-native/'
    require(set(native) == {prefix + name for name in ('shipped-activation.json','no-model-path-refusal.txt','strict-verification-refusal.txt')}, 'native capture roster differs')
    shipped = next(path for key, path in native.items() if key.endswith('/shipped-activation.json'))
    rows = entries(shipped)
    require(any(row.get('kind') == 'model' and row.get('data', {}).get('callable') == 'os.system' for row in rows), 'native sink did not bind')
    for name, marker in [('no-model-path-refusal.txt', 'taint configuration error'), ('strict-verification-refusal.txt', 'model verification error')]:
        text = next(path for key, path in native.items() if key.endswith('/' + name)).read_text()
        require(marker in text and 'exit 0' not in text, 'native refusal evidence differs')
    callee_files = captures['probe-pysa-callee-resolution']
    require(set(callee_files) == {'reports/raw/pysa-callee-resolution-probe/dispatch-table-call-graph.json'}, 'callee capture roster changed')
    callee = json.loads(next(iter(callee_files.values())).read_bytes())
    require(callee['run_call_graph']['callable'] == 'dispatch_table.run' and callee['bound_models'], 'callee discovery missing')
    parent = json.loads((ROOT / 'reports/releases/v0.9.0/execution-v1/contract.json').read_bytes())
    groups = [row['id'] for row in parent['groups'] if row['tool'] == 'pysa']
    require(len(groups) == 3 and set(groups) == {name for name, alias in bindings['group_tools'].items() if alias == 'pysa'}, 'Pysa matrix scope changed')
    result = {'schema': 'v092-pysa-release-qualification/v1', 'status': 'measurement-with-known-limits', 'execution_eligible': True, 'groups': groups,
              'tool': {key: tool[key] for key in ('path','sha256','version')},
              'identity_components': [executor._component_identity(alias, bindings['tool_bindings'][alias]) for alias in bindings['tool_components']['pysa']],
              'control_receipts': receipts, 'modeling_issue_counts': counts,
              'native_issue_count': sum(row.get('kind') == 'issue' for row in rows), 'callee_observation': callee,
              'limits': ['Native activation requires shipped models and --no-verify; activation does not establish source coverage.', 'Higher-order callee behavior is retained as observed, including missing edges and zero issues.', 'Earlier recorder failure and ignored-fixture failure remain in separate attempts and do not qualify groups.'],
              'review_implementation': {'path': str(Path(__file__).relative_to(ROOT)), 'sha256': sha(Path(__file__))}}
    args.output.write_bytes(executor._json_bytes(result))
    print(json.dumps({'status': result['status'], 'groups': len(groups), 'model_controls': len(counts)}))


if __name__ == '__main__':
    main()
