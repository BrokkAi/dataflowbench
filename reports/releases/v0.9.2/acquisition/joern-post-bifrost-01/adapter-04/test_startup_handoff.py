"""Tiny OS-level startup handoff probes; no engine, analyzer, or replay."""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import packet
import supervisor


CHILD = r'''
import fcntl, json, os, sys, time
from pathlib import Path
import packet, supervisor

class Controller:
    @staticmethod
    def _process(pid):
        return {"pid": pid, "birth_identity": "birth-%d" % pid}

class Protocol:
    @staticmethod
    def write_immutable(root, path, value):
        target = Path(root) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = packet.canonical(value)
        temporary = target.with_name('.' + target.name + '.tmp-' + str(os.getpid()))
        with temporary.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
        temporary.unlink()
        return {"path": path, "sha256": packet.digest(raw)}

class Graph:
    graph_sha256 = "g" * 64
    def module(self, name):
        if name == "supervisor24":
            return Controller
        if name == "protocol24":
            return Protocol
        raise AssertionError(name)

root = Path(sys.argv[1])
lock_fd = int(sys.argv[2])
startup_fd = int(sys.argv[3])
token = sys.argv[4]
receipt_path = sys.argv[5]
manifest = json.loads(sys.argv[6])
core = json.loads(sys.argv[7])
mode = sys.argv[8]
delay = float(sys.argv[9])
if mode == "exit":
    raise SystemExit(19)
if mode == "sleep":
    time.sleep(delay)
    raise SystemExit(0)
if delay:
    time.sleep(delay)
supervisor.startup_child_ready(root, core, manifest, graph=Graph(),
    lock_fd=lock_fd, startup_fd=startup_fd, token=token,
    receipt_path=receipt_path)
time.sleep(0.25)
'''


class StartupHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='joern05-startup-')
        self.root = Path(self.temp.name).resolve()
        self.lock_path = self.root / 'lock'
        self.lock_path.write_bytes(b'')
        self.lock_fd = os.open(self.lock_path, os.O_RDWR)
        fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.handoff_fd = os.dup(self.lock_fd)
        self.receipt_path = 'candidate/execution/supervision/startup-ready.json'
        self.token = 'a' * 32
        self.manifest = {'path': 'manifest.json', 'sha256': 'm' * 64}
        self.core = {
            'sidecar_namespace': 'candidate/execution',
            'lock_path': str(self.lock_path),
            'core_identity': {'path': 'core.json', 'sha256': 'c' * 64},
            'source_commit': 's' * 40,
            'plan_commit': 'p' * 40,
            'contract': {'sha256': 'k' * 64},
        }

    def tearDown(self):
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        except (OSError, ValueError):
            pass
        for name in ('handoff_fd', 'lock_fd'):
            fd = getattr(self, name, -1)
            if fd >= 0:
                os.close(fd)
        self.temp.cleanup()

    def launch(self, mode='ready', delay=0.0):
        read_fd, write_fd = os.pipe()
        os.set_inheritable(read_fd, False)
        os.set_inheritable(write_fd, True)
        child = subprocess.Popen(
            [sys.executable, '-B', '-E', '-c', CHILD, str(self.root), str(self.handoff_fd),
             str(write_fd), self.token, self.receipt_path, json.dumps(self.manifest),
             json.dumps(self.core), mode, str(delay)],
            cwd=HERE, close_fds=True, pass_fds=(self.handoff_fd, write_fd),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(write_fd)
        return child, read_fd

    def await_ready(self, child, read_fd, timeout=2.0):
        return supervisor.await_startup_ready(
            self.root, self.core, self.manifest, child=child, read_fd=read_fd,
            expected_process={'pid': child.pid, 'birth_identity': 'birth-%d' % child.pid},
            expected_parent_process={'pid': os.getpid(), 'birth_identity': 'birth-%d' % os.getpid()},
            expected_lock={'dev': os.fstat(self.lock_fd).st_dev, 'ino': os.fstat(self.lock_fd).st_ino},
            token=self.token, receipt_path=self.receipt_path,
            expected_graph_sha256='g' * 64, timeout_seconds=timeout)

    def test_inherited_descriptor_survives_delayed_parent_release(self):
        child, read_fd = self.launch(delay=0.15)
        started = time.monotonic()
        result = self.await_ready(child, read_fd)
        elapsed = time.monotonic() - started
        os.close(read_fd)
        self.assertEqual(result['receipt']['lock_ownership'], 'inherited-open-file-description')
        self.assertGreaterEqual(elapsed, 0.10)
        # Drop only the bootstrap reference. The child still owns the flock.
        os.close(self.handoff_fd)
        self.handoff_fd = -1
        os.close(self.lock_fd)
        self.lock_fd = -1
        probe = os.open(self.lock_path, os.O_RDWR)
        try:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(probe)
        self.assertEqual(child.wait(timeout=2), 0)
        probe = os.open(self.lock_path, os.O_RDWR)
        try:
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            fcntl.flock(probe, fcntl.LOCK_UN)
            os.close(probe)

    def test_permanently_unready_peer_times_out_without_retry(self):
        child, read_fd = self.launch(mode='sleep', delay=2.0)
        with self.assertRaises(TimeoutError):
            self.await_ready(child, read_fd, timeout=0.20)
        os.close(read_fd)
        child.terminate()
        child.wait(timeout=2)

    def test_inode_path_swap_is_rejected_before_readiness(self):
        child, read_fd = self.launch(delay=0.20)
        self.lock_path.unlink()
        self.lock_path.write_bytes(b'replacement')
        with self.assertRaises(ValueError):
            self.await_ready(child, read_fd)
        os.close(read_fd)
        self.assertNotEqual(child.wait(timeout=2), 0)
        self.assertFalse((self.root / self.receipt_path).exists())

    def test_peer_exit_before_ack_is_terminal_startup_failure(self):
        child, read_fd = self.launch(mode='exit')
        with self.assertRaises(ValueError):
            self.await_ready(child, read_fd)
        os.close(read_fd)
        self.assertEqual(child.wait(timeout=2), 19)
        self.assertFalse((self.root / self.receipt_path).exists())


if __name__ == '__main__':
    unittest.main()
