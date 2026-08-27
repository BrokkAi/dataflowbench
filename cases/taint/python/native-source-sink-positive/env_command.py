"""Tool-native probe, template 1 (category S): a platform environment read
reaches a platform command sink in one hop.

Every identity here is the real CPython one, by its real module path, so a
shipped source model for `os.environ` and a shipped sink model for `os.system`
have something to bind to. See docs/native-profile.md#the-native-binding-trap.
"""

import os


def run():
    command = os.environ["DFB_NATIVE_COMMAND"]  # DFB-SOURCE: native-source-sink-environment
    os.system(command)  # DFB-SINK: native-source-sink-command


if __name__ == "__main__":
    run()
