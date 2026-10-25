"""Independent source-only monitor probe; no ps, resources, analyzer, JVM, or Git."""
import importlib.util
from pathlib import Path
import types


ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
CANDIDATE = Path('/private/tmp/joern05-native-qualifier-07/native_qualifier.py')


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


n = load(CANDIDATE, 'independent_native_qualifier_probe')
proc = load(ROOT / 'scripts/swift_v2_process.py', 'independent_native_process_probe')
executor_source = load(ROOT / 'scripts/execute-release-v092.py', 'independent_frozen_executor_probe')
controller_source = load(ROOT / 'reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-24.py', 'independent_frozen_controller_probe')


def snap(command_table: str, native_table: dict, tracked: dict):
    events = []
    executor = types.SimpleNamespace(
        _process_table=lambda: (events.append('command') or command_table),
        _contenders=executor_source._contenders,
    )
    controller = types.SimpleNamespace(
        _hashed_bifrost_contenders=controller_source._hashed_bifrost_contenders,
    )
    native = types.SimpleNamespace(
        process_table=lambda: (events.append('native') or native_table),
        descendants=lambda table, current: (events.append('descendants') or proc.descendants(table, current)),
    )
    return n._contention_snapshot(executor, controller, native, tracked), events


def main():
    tracked = {100: 'root-birth'}
    native = {
        100: (1, 'root-birth', 'S'),
        101: (100, 'child-birth', 'S'),
        102: (101, 'grandchild-birth', 'S'),
        104: (999, 'foreign-birth', 'S'),
        106: (999, 'reparented-birth', 'S'),
    }
    command = '\n'.join([
        '101 80.0 joern /usr/bin/joern --scan',
        '102 80.0 joern /usr/bin/joern --scan',
        '104 80.0 joern /usr/bin/joern --scan',
        '106 80.0 joern /usr/bin/joern --scan',
        '107 80.0 joern /usr/bin/joern --scan',
    ])
    result, events = snap(command, native, tracked)
    assert events == ['command', 'native', 'descendants'], events
    assert result['tracked_after'] == {100: 'root-birth', 101: 'child-birth', 102: 'grandchild-birth'}
    assert [row['pid'] for row in result['proven_owned_rows']] == [101, 102]
    assert result['contenders'] == [
        '104 80.0 joern /usr/bin/joern --scan',
        '106 80.0 joern /usr/bin/joern --scan',
        '107 80.0 joern /usr/bin/joern --scan',
    ]
    rejected = {row['pid']: row['native'] for row in result['rejected_command_rows']}
    assert rejected[104]['ppid'] == 999
    assert rejected[106]['ppid'] == 999
    assert rejected[107] is None

    # A PID already tracked with another birth remains foreign when the fresh
    # native row reports a wrong/recycled identity.
    wrong, _ = snap(
        '103 80.0 joern /usr/bin/joern --scan',
        {100: (1, 'root-birth', 'S'), 103: (100, 'wrong-child-birth', 'S')},
        {100: 'root-birth', 103: 'expected-child-birth'},
    )
    assert wrong['contenders'] == ['103 80.0 joern /usr/bin/joern --scan']
    assert wrong['rejected_command_rows'][0]['native']['birth_identity'] == 'wrong-child-birth'

    recycled, _ = snap(
        '105 80.0 joern /usr/bin/joern --scan',
        {100: (1, 'recycled-root-birth', 'S'), 105: (100, 'child-birth', 'S')},
        {100: 'root-birth'},
    )
    assert recycled['contenders'] == ['105 80.0 joern /usr/bin/joern --scan']
    assert recycled['rejected_command_rows'][0]['native']['ppid'] == 100
    assert recycled['tracked_after'] == {100: 'root-birth'}

    # The public compatibility wrapper remains list-shaped and keeps the same
    # frozen classifier behavior for an unowned foreign row.
    events = []
    executor = types.SimpleNamespace(
        _process_table=lambda: (events.append('command') or '204 80.0 joern /usr/bin/joern --scan'),
        _contenders=executor_source._contenders,
    )
    controller = types.SimpleNamespace(
        _hashed_bifrost_contenders=controller_source._hashed_bifrost_contenders,
    )
    native = types.SimpleNamespace(
        process_table=lambda: (events.append('native') or {100: (1, 'root-birth', 'S'), 204: (999, 'foreign', 'S')}),
        descendants=lambda table, current: (events.append('descendants') or proc.descendants(table, current)),
    )
    assert n.contenders(executor, controller, native, tracked) == ['204 80.0 joern /usr/bin/joern --scan']
    assert events == ['command', 'native', 'descendants'], events
    print({'status': 'passed', 'tracked_outer_ready': result['tracked_after'], 'contenders': result['contenders']})


if __name__ == '__main__':
    main()
