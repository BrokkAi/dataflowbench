"""Conservatively classify diagnostic observations from the Swift entry extractor.

This module reports only whether the exact anchored source reaches the exact
anchored sink.  It does not establish global semantic completeness or produce
scored benchmark outcomes.
"""

from collections import defaultdict
import os


def _incomplete(reason, **details):
    return {
        'status': 'INCOMPLETE',
        'reason': reason,
        'diagnostic': None,
        'scored': False,
        **details,
    }


def _is_int(value, minimum=0):
    return type(value) is int and value >= minimum


def _valid_sequence(rows):
    if not isinstance(rows, list):
        return None, 'missing-sequence'
    if not rows:
        return None, 'missing-sequence'

    owners = set()
    indices = defaultdict(list)
    seen_rows = set()
    for row in rows:
        if (not isinstance(row, (list, tuple)) or len(row) != 6
                or not isinstance(row[0], str) or not os.path.isabs(row[0])
                or not isinstance(row[1], str) or not row[1]
                or not _is_int(row[2]) or not _is_int(row[3], 1)
                or not _is_int(row[4]) or not _is_int(row[5])):
            return None, 'malformed-entry-row'
        file, module, index, _line, decl_count, cfg_count = row
        owners.add((file, module))
        indices[index].append(tuple(row))
        frozen = tuple(row)
        if frozen in seen_rows:
            return None, 'duplicate-owner-rows'
        seen_rows.add(frozen)
        if decl_count != 1:
            return None, 'duplicate-owner-rows' if decl_count > 1 else 'invalid-declaration-count'
        if cfg_count == 0:
            return None, 'missing-cfg'

    if len(owners) != 1:
        return None, 'multiple-entry-owners'
    if any(len(values) > 1 for values in indices.values()):
        return None, 'duplicate-indices'
    ordered = sorted(indices)
    if ordered != list(range(len(rows))):
        return None, 'invalid-dense-index'
    return rows, None


def _valid_endpoints(rows):
    if not isinstance(rows, list):
        return None, 'missing-endpoint-sequence'
    indexed = {}
    for row in rows:
        if (not isinstance(row, (list, tuple)) or len(row) != 10
                or not isinstance(row[0], str) or not row[0]
                or not _is_int(row[1], 1) or not _is_int(row[2], 1)
                or row[3] not in ('source', 'sink')
                or not _is_int(row[4]) or row[5] not in (0, 1) or type(row[5]) is not int
                or not _is_int(row[6]) or not _is_int(row[7]) or not _is_int(row[8])
                or not isinstance(row[9], str)):
            return None, 'malformed-endpoint-row'
        key = (row[0], row[1], row[2], row[3])
        normalized = tuple(row)
        prior = indexed.get(key)
        if prior is not None:
            if prior != normalized:
                return None, 'conflicting-endpoint-rows'
            return None, 'duplicate-endpoint-rows'
        indexed[key] = normalized

    exact = {}
    for role in ('source', 'sink'):
        candidates = [row for row in rows if row[3] == role and row[4] == 1 and row[5] == 1]
        if not candidates:
            return None, 'missing-exact-' + role
        if len(candidates) != 1:
            return None, 'ambiguous-exact-' + role
        row = candidates[0]
        # Counts are stages in the binding proof.  A display label alone is not
        # identity evidence; exactflag and the unique target count are required.
        if row[6] != 1:
            return None, 'missing-endpoint-expression-' + role
        if row[7] == 0:
            return None, 'missing-cfg'
        if row[8] == 0:
            return None, 'missing-df'
        exact[role] = row
    return exact, None


def classify(entry_rows, exact_endpoints, flow_rows):
    """Return a typed incomplete result or a non-scored reached/not-reached diagnostic.

    ``entry_rows`` are ``[absolute_file, module, index, line, decl_count,
    cfg_count]`` rows.  ``exact_endpoints`` are the ten-column diagnostic rows
    emitted by ``diagnostics.ql``.  ``flow_rows`` are five-column source/sink
    location rows.  Identical endpoint locations are joined by file and line
    for both endpoints. The diagnostic sink column describes the call, while
    the flow column describes its argument; columns are not comparable.
    """
    sequence, reason = _valid_sequence(entry_rows)
    if reason:
        return _incomplete(reason)

    endpoints, reason = _valid_endpoints(exact_endpoints)
    if reason:
        return _incomplete(reason)

    if not isinstance(flow_rows, list):
        return _incomplete('missing-flow-sequence')
    flows = set()
    for row in flow_rows:
        if (not isinstance(row, (list, tuple)) or len(row) != 5
                or not isinstance(row[0], str) or not row[0]
                or not _is_int(row[1], 1)
                or not isinstance(row[2], str) or not row[2]
                or not _is_int(row[3], 1) or not _is_int(row[4], 1)):
            return _incomplete('malformed-flow-row')
        flows.add(tuple(row))

    source = endpoints['source']
    sink = endpoints['sink']
    reached = any(row[:4] == (source[0], source[1], sink[0], sink[1]) for row in flows)
    owner_file, owner_module = sequence[0][0], sequence[0][1]
    return {
        'status': 'DIAGNOSTIC',
        'reason': None,
        'diagnostic': 'reached' if reached else 'not-reached',
        'scored': False,
        'entry_owner': {'file': owner_file, 'module': owner_module},
        'source_anchor': {'file': source[0], 'line': source[1], 'column': source[2]},
        'sink_anchor': {'file': sink[0], 'line': sink[1], 'column': sink[2]},
    }
