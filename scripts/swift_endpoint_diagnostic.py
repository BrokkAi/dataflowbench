"""Classify structural endpoint evidence without converting it to taint outcomes."""


def classify(rows, anchors):
    indexed = {}
    identities = set()
    for row in rows:
        if (not isinstance(row, list) or len(row) != 10 or not isinstance(row[0], str)
                or any(type(row[i]) is not int or row[i] < 1 for i in [1, 2])
                or row[3] not in ['source', 'sink']
                or any(type(row[i]) is not int or row[i] < 0 for i in range(4, 9))
                or row[5] not in [0, 1] or row[6] not in [0, 1]
                or not isinstance(row[9], str)):
            raise ValueError('MalformedEndpointEvidence')
        identity = tuple(row[:4])
        if identity in identities:
            raise ValueError('DuplicateEndpointEvidence')
        identities.add(identity)
        if ((row[5] and row[4] != 1) or (row[8] and not row[7])
                or ((row[7] or row[8]) and not row[6])):
            raise ValueError('ContradictoryEndpointEvidence')
        indexed.setdefault((row[0], row[1], row[3]), []).append(row)
    results = []
    seen = set()
    for anchor in anchors:
        if (not isinstance(anchor, dict) or not isinstance(anchor.get('file'), str)
                or type(anchor.get('line')) is not int or anchor['line'] < 1
                or anchor.get('role') not in ['source', 'sink']):
            raise ValueError('MalformedEndpointAnchor')
        key = (anchor['file'], anchor['line'], anchor['role'])
        if key in seen:
            raise ValueError('DuplicateEndpointAnchor')
        seen.add(key)
        candidates = indexed.get(key, [])
        exact = [r for r in candidates if r[5]]
        if len(exact) > 1 or (not exact and len(candidates) > 1):
            status = 'AmbiguousASTCalls'
        elif not candidates:
            status = 'ASTCallMissing'
        else:
            row = exact[0] if exact else candidates[0]
            status = ('UnresolvedEndpoint' if not row[4] else
                      'NonMatchingDeclaration' if not row[5] else
                      'EndpointExpressionMissing' if not row[6] else
                      'MissingControlFlow' if not row[7] else
                      'MissingDataFlow' if not row[8] else 'Bound')
        results.append(dict(anchor, status=status, rows=candidates))
    return results
