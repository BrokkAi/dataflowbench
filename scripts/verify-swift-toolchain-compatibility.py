#!/usr/bin/env python3
"""Verify isolated Swift toolchain provenance and bounded, incomplete attempt."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/swift-toolchain-compatibility-220'

def read(name):
    return json.loads((BASE / name).read_text())

def main():
    actual = {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in BASE.rglob('*') if p.is_file() and p.name != 'evidence-manifest.json'}
    assert actual == read('evidence-manifest.json')['files']
    acquisition = read('acquisition.json')
    assert acquisition['signature_check_exit'] == 0
    assert acquisition['publisher'] == 'Swift Open Source (V9AUD2URP3)'
    signature = (BASE / 'package-signature.txt').read_text()
    assert 'trusted by the Apple notary service' in signature
    assert read('compiler-version.command.json')['timed_out']
    for name in ['compiler-version-attempt-02', 'compiler-typecheck']:
        record = read(name + '.command.json')
        assert record['exit_status'] == 0 and not record['timed_out']
        assert record['cleanup_status'] == 'tracked-processes-stopped'
    assert not read('compiler-control.json')['native_binary_execution']
    attempt = read('codeql-attempt-01/witness.json')
    assert attempt['extraction_phase_deadline_seconds'] == 60
    assert attempt['budget'] == {'peak_memory_mb': 512, 'wall_clock_seconds': 60}
    assert attempt['phases']['database-create']['timed_out']
    assert set(attempt['phases']) == {'database-create'}
    assert 'database_validation' not in attempt
    assert not list((BASE / 'codeql-attempt-01').glob('*.bqrs'))
    plan = read('codeql-plan.json')
    assert plan['maximum_attempts'] == 1 and not plan['absence_qualification']
    assert hashlib.sha256((BASE/'control/main.swift').read_bytes()).hexdigest() == plan['source_sha256']
    for name, digest in plan['query_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
    print('Isolated compiler control passed; CodeQL timeout remains incomplete and unqualified')

if __name__ == '__main__':
    main()
