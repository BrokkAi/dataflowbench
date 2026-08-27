"""Tool-native probe, template 5 (category E), negative.

A constant local declared beside the `sys.argv` read, in the same function,
reaches the same sink. The argv read is present and goes nowhere.
"""

import os
import sys


def run():
    unused = sys.argv[1]  # DFB-SOURCE: native-entrypoint-argument
    command = "id"
    os.system(command)  # DFB-SINK: native-entrypoint-command


if __name__ == "__main__":
    run()
