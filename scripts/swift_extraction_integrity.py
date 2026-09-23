"""Conservative compiler-diagnostic gate for Swift extraction observations."""
import gzip
from pathlib import Path
import re


def inspect_logs(directory):
    paths = sorted(p for p in Path(directory).rglob('*') if p.is_file() and
                   (p.name.endswith('.log.txt') or p.name.endswith('.log.txt.gz')))
    errors = []
    for path in paths:
        opener = gzip.open if path.suffix == '.gz' else open
        with opener(path, 'rt', errors='strict') as stream:
            for number, line in enumerate(stream, 1):
                if re.search(r'\b(?:ERRO|ERROR)\b', line):
                    errors.append({'path': str(path), 'line': number, 'text': line.rstrip('\n')})
    return {'logs_checked': len(paths), 'errors': errors,
            'ready_for_observation': bool(paths) and not errors}
