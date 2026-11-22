#!/usr/bin/env python3
"""Stopped PID observations must distinguish absence from uncertainty."""

import os
from types import SimpleNamespace
import unittest

from v092_closed_process_identity import observe_stopped


class ClosedProcessTests(unittest.TestCase):
    def run_table(self, extra="", returncode=0):
        return lambda *args, **kwargs: SimpleNamespace(
            returncode=returncode, stdout=f"{os.getpid()}\n{extra}")

    def test_confirmed_absence_never_queries_unknown_identity(self):
        def unavailable(_pid):
            raise AssertionError("absent PID must not need an identity")
        evidence = observe_stopped(1, "old", unavailable, run=self.run_table())
        self.assertEqual(evidence["status"], "confirmed-pid-absent")
        self.assertEqual(evidence["signals_sent"], [])

    def test_present_unknown_is_not_absent(self):
        for identity in (None, "", 0):
            with self.subTest(identity=identity), self.assertRaisesRegex(RuntimeError, "unknown"):
                observe_stopped(1, "old", lambda _pid: identity, run=self.run_table("1\n"))

    def test_known_replacement_proves_old_identity_stopped(self):
        evidence = observe_stopped(1, "old", lambda _pid: "new", run=self.run_table("1\n"))
        self.assertEqual(evidence["status"], "confirmed-different-birth-identity")

    def test_same_identity_is_still_present(self):
        with self.assertRaisesRegex(RuntimeError, "still present"):
            observe_stopped(1, "old", lambda _pid: "old", run=self.run_table("1\n"))

    def test_failed_or_malformed_observation_is_unknown(self):
        for run in (self.run_table(returncode=1), self.run_table("not-a-pid\n"),
                    lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="1\n")):
            with self.subTest(run=run), self.assertRaises(RuntimeError):
                observe_stopped(1, "old", lambda _pid: None, run=run)


if __name__ == "__main__":
    unittest.main()
