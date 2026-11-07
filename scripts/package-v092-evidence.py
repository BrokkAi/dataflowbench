#!/usr/bin/env python3
"""Create or verify a lossless delivery copy without changing release evidence.

The manifest maps every original path to a content object and its metadata.
Repeated bytes are stored once, but restore creates independent regular files.
Archives are ordinary gzip/tar, split below Git's individual-file size limit.
This tool does not confer benchmark or publication qualification.
"""

import argparse
import collections
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
import tempfile
import shutil


BLOCK = 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(BLOCK), b''):
            h.update(block)
    return h.hexdigest()


def safe_path(value):
    p = PurePosixPath(value)
    require(p.parts and not p.is_absolute() and value == str(p) and
            all(x not in ('', '.', '..') for x in p.parts), 'unsafe path')
    return p


def stable_stat(path):
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode), f'not a regular file: {path}')
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns,
            stat.S_IMODE(s.st_mode))


class PartsWriter:
    def __init__(self, directory, limit):
        self.directory, self.limit = directory, limit
        self.stream, self.size, self.paths = None, 0, []

    def write(self, data):
        original = len(data)
        while data:
            if self.stream is None or self.size == self.limit:
                if self.stream:
                    self.stream.close()
                p = self.directory / f'detail.tar.gz.part{len(self.paths):04d}'
                self.stream = p.open('xb')
                self.paths.append(p)
                self.size = 0
            n = min(len(data), self.limit - self.size)
            self.stream.write(data[:n])
            data, self.size = data[n:], self.size + n
        return original

    def flush(self):
        if self.stream:
            self.stream.flush()

    def close(self):
        if self.stream:
            self.stream.close()


class PartsReader(io.RawIOBase):
    def __init__(self, paths):
        self.paths = iter(paths)
        self.stream = None

    def readable(self):
        return True

    def readinto(self, buffer):
        while True:
            if self.stream is None:
                p = next(self.paths, None)
                if p is None:
                    return 0
                self.stream = p.open('rb')
            n = self.stream.readinto(buffer)
            if n:
                return n
            self.stream.close()
            self.stream = None

    def close(self):
        if self.stream:
            self.stream.close()
        super().close()


class HashReader:
    def __init__(self, stream):
        self.stream, self.hash = stream, hashlib.sha256()

    def read(self, size):
        b = self.stream.read(size)
        self.hash.update(b)
        return b


def pack(root, scope, output, part_bytes):
    root, output = root.resolve(), output.resolve()
    relative = safe_path(scope)
    source = root / relative
    ancestor = root
    for component in relative.parts:
        ancestor = ancestor / component
        require(not ancestor.is_symlink(), 'symlink scope ancestor refused')
    require(source.is_dir() and not source.is_symlink(), 'invalid evidence scope')
    require(not output.is_relative_to(source), 'output must be outside evidence scope')
    require(1024 <= part_bytes <= 40 * BLOCK, 'part limit must be at most 40 MiB')
    output.mkdir(parents=True, exist_ok=False)
    records, objects, stamps = [], {}, {}
    paths = []
    for base, dirs, files in os.walk(source, followlinks=False):
        for name in dirs:
            require(not (Path(base) / name).is_symlink(), 'symlink directory refused')
        paths.extend(Path(base) / name for name in files)
    for path in sorted(paths):
        before = stable_stat(path)
        sha = digest(path)
        require(before == stable_stat(path), f'file changed during hash: {path}')
        record = {'path': path.relative_to(root).as_posix(), 'sha256': sha,
                  'bytes': before[2], 'mode': before[5], 'mtime_ns': before[3]}
        records.append(record)
        stamps[path] = before
        objects.setdefault(sha, path)
    manifest = output / 'files.jsonl.gz'
    with manifest.open('xb') as raw, gzip.GzipFile(filename='', mode='wb',
                                                 fileobj=raw, mtime=0) as gz:
        for record in records:
            gz.write((json.dumps(record, sort_keys=True) + '\n').encode())
    parts = PartsWriter(output, part_bytes)
    try:
        with gzip.GzipFile(filename='', mode='wb', fileobj=parts, mtime=0) as gz:
            with tarfile.open(mode='w|', fileobj=gz, format=tarfile.USTAR_FORMAT) as tar:
                for sha, path in sorted(objects.items()):
                    require(stamps[path] == stable_stat(path), 'source changed before compression')
                    info = tarfile.TarInfo('objects/' + sha)
                    info.size, info.mode, info.mtime = stamps[path][2], 0o644, 0
                    with path.open('rb') as stream:
                        reader = HashReader(stream)
                        tar.addfile(info, reader)
                    require(reader.hash.hexdigest() == sha, 'source changed during compression')
    finally:
        parts.close()
    for path, before in stamps.items():
        require(before == stable_stat(path), f'snapshot source changed: {path}')
    index = {
        'schema': 'dataflowbench-lossless-evidence-bundle/v1',
        'scope': str(relative), 'snapshot_file_count': len(records),
        'original_bytes': sum(r['bytes'] for r in records),
        'unique_objects': len(objects),
        'unique_object_bytes': sum(stamps[p][2] for p in objects.values()),
        'manifest': {'path': manifest.name, 'sha256': digest(manifest),
                     'bytes': manifest.stat().st_size},
        'parts': [{'path': p.name, 'sha256': digest(p), 'bytes': p.stat().st_size}
                  for p in parts.paths],
        'scope_note': 'Files inventoried at pack start only; later files require a successor snapshot.',
        'originals_modified': False, 'benchmark_qualification': False,
        'publication_authorized': False,
    }
    (output / 'bundle.json').write_text(json.dumps(index, indent=2) + '\n')
    return index


def check(bundle, restore=None):
    bundle = bundle.resolve()
    index = json.loads((bundle / 'bundle.json').read_text())
    require(index['schema'] == 'dataflowbench-lossless-evidence-bundle/v1', 'unknown schema')
    scope = safe_path(index['scope'])
    names = [item['path'] for item in [index['manifest'], *index['parts']]]
    require(len(set(names)) == len(names), 'duplicate bundle file reference')
    for item in [index['manifest'], *index['parts']]:
        p = safe_path(item['path'])
        require(len(p.parts) == 1, 'bundle files must be direct children')
        path = bundle / p
        require(stable_stat(path)[2] == item['bytes'] and digest(path) == item['sha256'],
                f'bundle digest mismatch: {p}')
    records, by_object = [], collections.defaultdict(list)
    with gzip.open(bundle / index['manifest']['path'], 'rt') as stream:
        for line in stream:
            r = json.loads(line)
            p = safe_path(r['path'])
            require(p.is_relative_to(scope), 'manifest path outside scope')
            require(len(r['sha256']) == 64 and all(x in '0123456789abcdef' for x in r['sha256']),
                    'invalid object digest')
            require(type(r['bytes']) is int and r['bytes'] >= 0 and
                    type(r['mode']) is int and 0 <= r['mode'] <= 0o7777 and
                    type(r['mtime_ns']) is int, 'invalid file metadata')
            records.append(r)
            by_object[r['sha256']].append(r)
    require(len(records) == index['snapshot_file_count'] and
            len({r['path'] for r in records}) == len(records), 'manifest count or duplicate path')
    file_paths = {PurePosixPath(r['path']) for r in records}
    require(not any(parent in file_paths for p in file_paths for parent in p.parents),
            'manifest file/child path collision')
    require(sum(r['bytes'] for r in records) == index['original_bytes'] and
            len(by_object) == index['unique_objects'] and
            sum(v[0]['bytes'] for v in by_object.values()) == index['unique_object_bytes'],
            'manifest totals differ')
    if restore is not None:
        restore = restore.resolve()
        restore.mkdir(parents=True, exist_ok=False)
    seen = set()
    with PartsReader([bundle / i['path'] for i in index['parts']]) as raw:
        with gzip.GzipFile(fileobj=io.BufferedReader(raw), mode='rb') as gz:
            with tarfile.open(mode='r|', fileobj=gz) as tar:
                for member in tar:
                    sha = member.name.removeprefix('objects/')
                    require(member.isfile() and member.name == 'objects/' + sha and
                            sha in by_object and sha not in seen, 'unexpected archive object')
                    require(all(r['bytes'] == member.size for r in by_object[sha]), 'object size differs')
                    h = hashlib.sha256()
                    with tempfile.TemporaryFile() if restore is not None else io.BytesIO() as spool:
                        source = tar.extractfile(member)
                        for block in iter(lambda: source.read(BLOCK), b''):
                            h.update(block)
                            if restore is not None:
                                spool.write(block)
                        require(h.hexdigest() == sha, 'uncompressed object digest differs')
                        if restore is not None:
                            for r in by_object[sha]:
                                target = restore / r['path']
                                target.parent.mkdir(parents=True, exist_ok=True)
                                spool.seek(0)
                                with target.open('xb') as dest:
                                    shutil.copyfileobj(spool, dest, BLOCK)
                                target.chmod(r['mode'])
                                os.utime(target, ns=(r['mtime_ns'], r['mtime_ns']))
                    seen.add(sha)
            # Consume the gzip trailer as well, verifying its CRC and length.
            while gz.read(BLOCK):
                pass
    require(seen == set(by_object), 'missing archive objects')
    return {'status': 'verified', 'files': len(records), 'objects': len(seen),
            'original_bytes': index['original_bytes'],
            'compressed_bytes': sum(p['bytes'] for p in index['parts']) + index['manifest']['bytes'],
            'restored': restore is not None}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    create = sub.add_parser('pack')
    create.add_argument('--root', type=Path, required=True)
    create.add_argument('--scope', default='reports/releases/v0.9.2')
    create.add_argument('--output', type=Path, required=True)
    create.add_argument('--part-mib', type=int, default=40)
    verify = sub.add_parser('check')
    verify.add_argument('bundle', type=Path)
    verify.add_argument('--restore', type=Path)
    args = p.parse_args()
    if args.command == 'pack':
        result = pack(args.root, args.scope, args.output, args.part_mib * BLOCK)
    else:
        result = check(args.bundle, args.restore)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
