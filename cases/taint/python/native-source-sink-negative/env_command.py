"""Tool-native probe, template 1 (category S), negative.

The environment read is present and goes nowhere; a clean constant local
reaches the *same* `os.system` callsite. The sink is identical in both cells by
construction, so a rule that fires on sink existence alone takes a false
positive here rather than an unearned true negative.
See docs/native-profile.md#sink-existence-only-findings-and-how-they-score.
"""

import os


def run():
    unused = os.environ["DFB_NATIVE_COMMAND"]  # DFB-SOURCE: native-source-sink-environment
    command = "id"
    os.system(command)  # DFB-SINK: native-source-sink-command


if __name__ == "__main__":
    run()
