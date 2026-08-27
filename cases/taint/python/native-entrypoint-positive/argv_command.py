"""Tool-native probe, template 5 (category E): CPython's own process-entry
convention is the source.

No framework, no registration: `sys.argv[1]` is where a Python program's
arguments arrive, and a shipped `commandargs` threat model is what makes it a
source.
"""

import os
import sys


def run():
    command = sys.argv[1]  # DFB-SOURCE: native-entrypoint-argument
    os.system(command)  # DFB-SINK: native-entrypoint-command


if __name__ == "__main__":
    run()
