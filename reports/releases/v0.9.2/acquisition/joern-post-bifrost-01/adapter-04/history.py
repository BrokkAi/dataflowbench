"""109 bindings and exact historical/new context roster, not a runtime provider."""
from __future__ import annotations
import copy
from pathlib import Path
from typing import Any
from packet import document, inherited_core, load_history_reader, require

def validate(root: Path, *, historical_only: bool=False) -> dict[str, Any]:
    reader = load_history_reader()
    return reader.validate_tail(root, {'path': reader.DESCRIPTOR_PATH, 'sha256': reader.DESCRIPTOR_SHA}, live_mode='prefix-history-only' if historical_only else 'exact')

def context_bindings(root: Path, current: dict[str, Any] | None=None) -> dict[str, Any]:
    """Nine immutable origins remain unchanged; tenth requires actual bound files."""
    old = inherited_core(root)
    result = copy.deepcopy(old['source_contexts'])
    require(len(result) == 9, 'historical context roster differs')
    if current is None:
        return result
    require(set(current) == {'contract', 'source_commit', 'plan_commit', 'source_evidence'}, 'current context exact fields required')
    contract = document(root, current['contract'])
    evidence = document(root, current['source_evidence'])
    require(contract['source_commit'] == current['source_commit'] == evidence['source_commit'], 'current source differs')
    require(evidence['plan_commit'] == current['plan_commit'], 'current plan differs')
    key = current['contract']['sha256']
    require(key not in result, 'current context cannot relabel historical origin')
    result[key] = {k: copy.deepcopy(current[k]) for k in ('contract', 'source_commit', 'plan_commit')}
    result[key]['role'] = 'joern05-current'
    require(len(result) == 10, 'current context roster differs')
    return result

def selected_rows(root: Path, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    facts = validate(root, historical_only=True)
    reader = load_history_reader()
    descriptor = document(root, facts['descriptor_ref'])
    prefix_raw = reader.bound(root, {k: descriptor['ledger_prefix'][k] for k in ('path', 'sha256')})
    prefix = reader.ledger_rows(prefix_raw)[1]
    require(rows[:109] == prefix and len(rows) in (109, 110), 'registered109 plus at most one tail required')
    replacements = {item['group_id'] for item in facts['retained20']}
    selected = {row['group_id']: row for row in prefix[:89] if row['status'] == 'completed' and row['group_id'] not in replacements}
    for row in prefix[89:]:
        selected[row['group_id']] = row
    if len(rows) == 110:
        row = rows[109]
        require(row['group_id'] == 'joern-swift-common108' and row['attempt_id'] == 'joern-swift-common108-attempt-05-series-02', 'only Joern05 may append')
        if row['status'] == 'completed' and row.get('exit_code') == 0 and (row.get('capacity_loss') is None):
            selected[row['group_id']] = row
    return selected
